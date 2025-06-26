import os
from langchain_openai import ChatOpenAI

from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import ConfigurableFieldSpec

from langchain_anthropic import ChatAnthropic
import time
from .retrieve_experts import retrieve_experts


from ..models import ChatHistory
from django.conf import settings
from django.http import JsonResponse, StreamingHttpResponse
import logging

import json
from translations.helpers.translate import detect_language, translate

from .models_supported import retriever_models_supported
import pinecone
from .vectorize_helpers import CustomEmbeddings, calculate_similarities, generate_system_prompt
from langchain_pinecone import PineconeVectorStore
from pinecone import Pinecone as PineconeClient


from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage
from langchain_core.runnables import RunnableLambda
from typing import List, Sequence
from langchain_core.runnables import RunnableMap
from langchain_core.runnables import Runnable
from typing import Dict, Union
from langchain_core.messages import BaseMessage



logger = logging.getLogger('django')

__all__ = ['set_up_retriever', 'stream_response_to_user']

# Ensure that environment variables are set
required_env_vars = ['LANGCHAIN_API_KEY', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY', 'AICHAT_LANGCHAIN_PROJECT']
missing_vars = [var for var in required_env_vars if not os.getenv(var)]
if missing_vars:
    raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")

# Set the LangChain-specific environment variables
os.environ['LANGCHAIN_TRACING_V2'] = 'true'
os.environ['LANGCHAIN_ENDPOINT'] = 'https://api.smith.langchain.com'

   

context_available_phrase = 'According to the sources listed below,'
chat_history_phrase = 'Based on our chat history,'
general_knowledge_phrase = 'While not contained in the documents uploaded, my access to internet data suggests'
no_answer_phrase = "I'm sorry, but I cannot answer that question, as it is not included in the documents uploaded."
use_gn_instructions = "Use knowledge from the internet if my input contains a question and the needed information is not in conversation history or documents I uploaded."
no_use_gn_instructions = "Do not use knowledge from the internet to respond to my input."


# This allows prior messages for a user + session combination to be used in conjunction with uploaded documents to answer a user's question.
class DjangoChatMessageHistory(BaseChatMessageHistory):
    def __init__(self, session_id, chat_history_window_int=None):
        self.session_id = session_id
        self.chat_history_window_int = chat_history_window_int
        self._messages: List[BaseMessage] = []  # Store as BaseMessage objects
        self._load_messages()

    def _load_messages(self):
        messages_query = ChatHistory.objects.filter(session_id=self.session_id).order_by('-id')
        
        # Apply the chat_history_window_int limit if specified
        if self.chat_history_window_int is not None:
            messages_query = messages_query[:self.chat_history_window_int]

        # Filter out responses that match the specific "no answer" content
        excluded_response = "I'm sorry, but I cannot answer that question, as it is not included in the documents uploaded."
        
        # Convert to BaseMessage objects
        self._messages = []
        for message in messages_query.values('message')[::-1]:  # Reverse to maintain correct order
            if excluded_response not in message['message']:
                self._messages.append(HumanMessage(content=message['message']))

    @property
    def messages(self) -> List[BaseMessage]:
        """Return the list of messages."""
        return self._messages

    def add_message(self, message: BaseMessage) -> None:
        """Add a message to the chat history."""
        self._messages.append(message)
        # Save to database
        ChatHistory.objects.create(session_id=self.session_id, message=message.content)

    def add_messages(self, messages: Sequence[BaseMessage]) -> None:
        """Add multiple messages to the chat history."""
        for message in messages:
            self.add_message(message)

    def clear(self) -> None:
        """Clear all messages from the chat history."""
        self._messages = []



def get_session_history(user_id: str, conversation_id: str, chat_history_window_int=None): # Note: Even though user_id is not being used due to use of 'conversation_id' instead, LangChain expects it to be passed as a config for RunnableWithMessageHistory and thus, it must also be included here.
    logger.debug(f'running get_session_history() ... function started')
    session_id = conversation_id
    return DjangoChatMessageHistory(session_id, chat_history_window_int)



# Declare retriever as a global variable
# Declare retriever as a global variable
retriever = None
def set_up_retriever(user):
    logger.debug(f'running set_up_retriever() ... function started')

    global retriever
    user_profile = user.aichat_userprofile
    
    # Check if the retriever already exists in the global scope
    if retriever is not None:
        logger.info(f'running set_up_retriever ... retriever already set up, using existing instance')
        return retriever

    # If the retriever is not pulled from the cache, create a new one, with its settings saved to SQL and the newly-created retriever itself saved to cache
    else:
        index_name = 'vectorized-sources' # EXPOSE LATER
        search_type = 'similarity' # EXPOSE LATER
        rag_source_data = user_profile.rag_sources_used # Will come back as 'website' , 'document' or 'all'
        logger.info(f'running set_up_retriever() ... '
                    f'index_name is: { index_name } '
                    f'search_type is: { search_type } '
                    f'rag_source_data is: { rag_source_data }')
        
        if rag_source_data == 'website':
            search_kwargs={
                "k": user_profile.langchain_k,
                'filter': {
                    'type': 'website'
                }
            }
        elif rag_source_data == 'document':
            search_kwargs={
            "k": user_profile.langchain_k,
            'filter': {
                'type': 'document'
                }
            }
        else:
            search_kwargs={
                "k": user_profile.langchain_k,
            }
        
        try:
            # Instantiate Pinecone vectorstore with embedding generator
            embedding_generator = CustomEmbeddings(user=user)
            logger.info(f'running set_up_retriever() ... embedding_generator is: { embedding_generator }')
            
            # Updated Pinecone syntax - get the Pinecone client and index
            PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
            if not PINECONE_API_KEY:
                raise ValueError("Pinecone API key is not set.")
            
            pc = PineconeClient(api_key=PINECONE_API_KEY)
            pinecone_index = pc.Index(index_name)
            
            # Create vectorstore using new syntax
            vectorstore = PineconeVectorStore(
                index=pinecone_index,
                embedding=embedding_generator,
                text_key="text"  # This should match your metadata structure
            )
            logger.info(f'running set_up_retriever() ... '
                         f'connected to Pinecone vectorstore: { vectorstore }')

            # Create retriever using vectorstore
            retriever = vectorstore.as_retriever(
                search_type=search_type,
                search_kwargs=search_kwargs
            )

            logger.info(f'running set_up_retriever ... '
                        f'successfully completed retriever setup, retriever is: { retriever }')
            return retriever
        
        except Exception as e:
            logger.error(f'Failed to save Retriever settings for user {user} due to: {e}')
            retriever = None
            return retriever



def stream_response_to_user(
    conversation_id,
    user_input,
    user,
):
    def event_stream():
        
        # Initialize message history. Note that we pass in chat history window.
        user_id = user.id
        user_profile = user.aichat_userprofile

        chat_history_window_int = user_profile.chat_history_window
        
        preferred_language = user_profile.preferred_language
        retriever_model = user_profile.retriever_model
        model_provider = retriever_models_supported.get(retriever_model, {}).get('model_provider', 'Unknown')
        temperature = user_profile.temperature
        top_p = user_profile.top_p
        logger.info(f'running stream_response_to_user ... '
                    f'user is: { user }, '
                    f'retriever_model is: { retriever_model },  '
                    f'model_provider is: { model_provider }'
                    f'temperature is: { temperature }, and '
                    f'top_p is: { top_p }')

        if model_provider == 'Anthropic':
            # Instructions for Anthropic API: https://python.langchain.com/docs/integrations/chat/anthropic/, https://python.langchain.com/api_reference/anthropic/chat_models/langchain_anthropic.chat_models.ChatAnthropic.html
            model = ChatAnthropic(
                model_name=retriever_model,  # Changed from 'model' to 'model_name'
                temperature=user_profile.temperature,
                max_tokens_to_sample=1024,
                timeout=None,
                max_retries=2,
                top_p=top_p,
                stop=None,  # Added required 'stop' parameter
                streaming=True
                # other params...
            )
        else:
            # Instructions for OpenAI API
            model = ChatOpenAI(
                model=retriever_model, # EXPOSE LATER
                streaming=True,  # Enable streaming
                temperature=temperature,
                top_p=top_p,
            )
        logger.debug(f"running stream_response_to_user() ... model is: { model }")

        # Detect user input language and use this for translation of key phrases
        try:
            detected_language = preferred_language
            #detected_language = detect_language(user_input)
        except Exception as e:
            logger.error(f'running stream_response_to_user() ... unable to determine detected language, falling back to "en"')
            detected_language = 'en'
        logger.debug(f'running stream_response_to_user() ... '
                     f'user_input is: { user_input } and '
                     f'detected_language is: { detected_language }')

        if detected_language == None:
            detected_language = user_profile.preferred_language
            logger.error(f'running stream_response_to_user() ... detected_language was None, '
                         f'falling back to user.aichat_userprofile.preferred_language: { detected_language }')


        # Step 2: Translate key phrases, if needed
        if detected_language != "en":
            context_available_phrase_translated = translate(
                input_text=context_available_phrase,
                from_language="en",
                to_language=detected_language,
            )
            chat_history_phrase_translated = translate(
                input_text=chat_history_phrase,
                from_language="en",
                to_language=detected_language,
            )
            no_answer_phrase_translated = translate(
                input_text=no_answer_phrase,
                from_language="en",
                to_language=detected_language,
            )
            general_knowledge_phrase_translated = translate(
                input_text=general_knowledge_phrase,
                from_language="en",
                to_language=detected_language,
            )
            sources_translated = translate(input_text="Sources:", from_language="en", to_language=detected_language)
            page_translated = translate(input_text="page", from_language="en", to_language=detected_language)
        else:
            context_available_phrase_translated = context_available_phrase
            chat_history_phrase_translated = chat_history_phrase
            no_answer_phrase_translated = no_answer_phrase
            general_knowledge_phrase_translated = general_knowledge_phrase
            sources_translated = "Sources:"
            page_translated = "page"
            
        logger.debug(
            f"running stream_response_to_user() ... context_available_phrase_translated is: { context_available_phrase_translated }, "
            f"running stream_response_to_user() ... chat_history_phrase_translated is: { chat_history_phrase_translated }, "
            f"running stream_response_to_user() ... no_answer_phrase_translated is: { no_answer_phrase_translated }, "
            f"running stream_response_to_user() ... general_knowledge_phrase_translated is: { general_knowledge_phrase_translated }, and "
            f"running stream_response_to_user() ... sources_translated is: { sources_translated }"
        )

        # Step 1: Send begin of stream message
        yield "id: {}\ndata: [BEGIN]\n\n".format(1)

        # Step 3: Select the appropriate system prompt relative to use general knowledge bool      
        data_source = user_profile.data_source
        logger.debug(f"running stream_response_to_user() ... for user: { user }, data_source is: { data_source }")
        if data_source == 'hist_rag_web':
            use_general_knowledge_bool = True
        else:
            use_general_knowledge_bool = False
        logger.debug(f'running stream_response_to_user ... '
                     f'use_general_knowledge_bool type is: {type(use_general_knowledge_bool)}, '
                     f'use_general_knowledge_bool value is: {use_general_knowledge_bool}')
        
        
        # Step 3: Use LangChain's ChatPromptTemplate to combine the system instructions, conversation history, and user input into a single prompt
        if data_source == 'rag':
            ignore_chat_history_bool = True
        else:
            ignore_chat_history_bool = False
        logger.debug(f'running stream_response_to_user ... '
                    f'ignore_chat_history_bool is: { ignore_chat_history_bool }')
        
        # Select the correct system prompt according to whether the user has toggled on web access
        system_prompt = generate_system_prompt(ignore_chat_history_bool=ignore_chat_history_bool, use_general_knowledge_bool=use_general_knowledge_bool)
        logger.info(f'running stream_response_to_user() ... '
                    f'use_general_knowledge_bool is: { use_general_knowledge_bool }, '
                    f'ignore_chat_history_bool is: { ignore_chat_history_bool }, and '
                    f'system_prompt is: { system_prompt }')

        if ignore_chat_history_bool:
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", system_prompt),
                    # MessagesPlaceholder(variable_name="history"), Ignores chat history
                    ("human", "{input}"),
                ]
            )
        else:
            prompt = ChatPromptTemplate.from_messages(
                [
                    ("system", system_prompt),
                    MessagesPlaceholder(variable_name="history"),
                    ("human", "{input}"),
                ]
            )

        # Step 4: Set up LangChain's runnable framework which is used to manage how prompts and user inputs are sent to the OpenAI model while maintaining context.
        
        runnable = prompt | model
        

        # Step 5: Invoke LangChain's RunnableWithMessageHistory, we pass both the retrieved document, and the conversation history.
        with_message_history = RunnableWithMessageHistory(
            runnable, # type: ignore
            get_session_history,
            input_messages_key="input",
            history_messages_key="history",
            history_factory_config=[
                ConfigurableFieldSpec(
                    id="user_id",
                    annotation=str,
                    name="User ID",
                    description="Unique identifier for the user.",
                    default="",
                    is_shared=True,
                ),
                ConfigurableFieldSpec(
                    id="conversation_id",
                    annotation=str,
                    name="Conversation ID",
                    description="Unique identifier for the conversation.",
                    default="",
                    is_shared=True,
                ),
                ConfigurableFieldSpec(
                    id="chat_history_window_int",
                    annotation=int,
                    name="Chat History Window",
                    description="Number of prior messages to include in chat history.",
                    default=None,
                    is_shared=True,
                ),
            ],
        )
        logger.debug(f'running stream_response_to_user() ... with_message_history is: { with_message_history }')


        # Step 6: Retrieve the relevant docs
        retriever = set_up_retriever(user)  
        if not retriever:
            logger.error(f'running stream_response_to_user() ... failed create or access the retriever')
            return JsonResponse({'status': 'error', 'message': 'Error: failed create or access the retriever'}, status=500)
        logger.debug(f'running stream_response_to_user() ... sucessfully pulled retriever: { retriever }')

        #retrieved_chunks = retriever.vectorstore.similarity_search_with_score(user_input)
        retrieved_chunks = retriever.invoke(user_input)
        logger.debug(f'running stream_response_to_user() ... '
                     f'user_input is: { user_input } and '
                     f'retrieved_chunks is: { retrieved_chunks }')
        
        # Separate the retrieved sources into documents and websites
        context = []

        
        #similarity_threshold = 0.7
        #for chunk, score in retrieved_chunks:
        for chunk in retrieved_chunks:
            logger.debug(f'running stream_response_to_user() ... chunk is: { chunk }')
            context.append(chunk.page_content.strip())
            #context.append(f"{chunk.page_content.strip()} (Score: {score:.2f})")
        # Join the list entries to form a single string for context
        context = ' '.join(context)
        logger.debug(f'running stream_response_to_user() ... context is: { context }')
            
        # Step 8: Append each answer chunk as it comes in, passing in user_input
        answer_chunks = []  # Initiate a list to hold the chunks of a given response

        event_id = 2
        response_length = user_profile.response_length

        # Here, 'chunk' represents a chunk in the streamed answer
        for chunk in with_message_history.stream(
            {
                "language": detected_language,
                "input": user_input,
                "context": context,
                "chat_history_phrase_translated": chat_history_phrase_translated,
                "context_available_phrase_translated": context_available_phrase_translated,
                "no_answer_phrase_translated": no_answer_phrase_translated,
                "general_knowledge_phrase_translated": general_knowledge_phrase_translated,
                "response_length": response_length,
            },
            config={"configurable": {"user_id": user_id, "conversation_id": conversation_id, "chat_history_window_int": chat_history_window_int,}},
        ):
            logger.debug(f'running stream_response_to_user() ... chunk is: { chunk }')
            
            # Safely extract content and ensure it's a string
            chunk_content = ""
            if hasattr(chunk, 'content'):
                content = chunk.content
                if isinstance(content, str):
                    chunk_content = content
                elif isinstance(content, dict):
                    # Handle case where content is a dictionary
                    chunk_content = str(content.get('text', '')) if 'text' in content else str(content)
                else:
                    chunk_content = str(content)
            
            # Append the chunk to answer_chunks (this consolidated answer is used for topic extraction and expert recommendation)
            answer_chunks.append(chunk_content)
            
            yield "id: {}\ndata: {}\n\n".format(event_id, chunk_content)
            event_id += 1
            time.sleep(0.1)  # Adjust the delay as needed

        # Ensure answer_text is always a string
        answer_text = "".join(str(chunk) for chunk in answer_chunks)

        # Ensure answer_text is a string before using 'in' operator
        if isinstance(answer_text, str):
            pass
        elif isinstance(answer_text, dict):
            answer_text = answer_text.get("text", "")
        else:
            answer_text = str(answer_text)

        # If an answer was streamed to the user, proceed with listing sources and experts (if recommendations are turned on)
        if isinstance(context_available_phrase_translated, str) and context_available_phrase_translated in answer_text:
            logger.debug(f'running stream_response_to_user() ... proceeding to list sources')

            contributing_chunks = []
            
            similarities = calculate_similarities(
                retrieved_chunks=retrieved_chunks, 
                answer_text=answer_text, 
                user=user,
            )

            for chunk, similarity in zip(retrieved_chunks, similarities):
                chunk_key = ""  # Initialize with default value
                
                if chunk.metadata['type'] == 'document':
                    doc_name = chunk.metadata['source']
                    doc_chunk_link_url = f"{settings.MEDIA_URL}{user.id}/{doc_name}"
                    doc_chunk_link = f'<a href="{doc_chunk_link_url}" target="_blank">{doc_name}</a>'
                    chunk_key = f"{doc_chunk_link}, {page_translated}, {int(chunk.metadata['page_number'])}<br>"

                elif chunk.metadata['type'] == 'website':
                    title = chunk.metadata.get('title', 'No Title Available')
                    chunk_url = chunk.metadata.get('source')
                    chunk_url_formatted = f'<a href="{chunk_url}" target="_blank">{chunk_url}</a>'
                    chunk_key = f"{title}, {chunk_url_formatted}<br>"
                
                # Only append if chunk_key was set
                if chunk_key:
                    contributing_chunks.append((chunk_key, similarity))

            logger.debug(f'running stream_response_to_user() ... '
                        f'contributing_chunks is: { contributing_chunks }')
            
            min_source_score = 0.75
            ranked_sources_deduplicated = []
            for source in contributing_chunks:
                if source not in ranked_sources_deduplicated and float(source[1][0]) >= min_source_score: # source[0] is the total score for each source, as returned by the calculate_similarities function
                    ranked_sources_deduplicated.append(source)
            
            ranked_sources = sorted(ranked_sources_deduplicated, key=lambda x: x[1][0], reverse=True)[:1] # EXPOSE LATER
            #ranked_sources = contributing_chunks[:1]
            logger.info(f'running stream_response_to_user() ... '
                        f'ranked_sources is: { ranked_sources }')

            # Stream the traslated version of the phrase 'Sources:'
            yield "id: {}\ndata: <br><br><b>{}</b><br>\n\n".format(event_id, sources_translated)
            
            for source, _ in ranked_sources: # Since deduplicated_sources_sorted is a tuple containing both a source and its associated score, here, we only care about the source. The use of '_' allows us to skip over the second item in the tuple (e.g the score), since that is not needed in printing the sources. 
            #for source in ranked_sources:
                yield "id: {}\ndata: {}\n\n".format(event_id, source)
                event_id += 1
        
        
            # Step 16: Use if statement to extract question topic and recommend experts only if suggest_experts is toggled on
            number_of_experts = int(user_profile.experts_suggested_number)
        
            if user_profile.suggest_experts and number_of_experts > 0:
                    
                related_experts = retrieve_experts(
                        input_text = user_input + answer_text, 
                        number_of_experts = number_of_experts,
                        detected_language = detected_language,
                        user = user,
                    )
            
                logger.debug(f"running stream_response_to_user() ... after running retrieve_experts(), related_experts is: { related_experts }")
                for expert in related_experts:
                    yield f"id: {event_id}\ndata: Expert: {json.dumps(expert)}\n\n"
                    event_id += 1

            else:
                logger.debug(f"running stream_response_to_user() ... no topic extracted")

        # Step 22: Send end of stream message
        yield "id: {}\ndata: [END]\n\n".format(event_id)

    def event_stream_bytes():
        for chunk in event_stream():
            yield chunk.encode('utf-8')
    
    return StreamingHttpResponse(event_stream_bytes(), content_type="text/event-stream")
