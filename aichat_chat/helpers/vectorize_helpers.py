from bs4 import BeautifulSoup
from django.conf import settings
import hashlib
from langchain_core.embeddings import Embeddings

from langchain_openai import OpenAIEmbeddings

import logging
from .models_supported import tokenization_and_vectorization_models_supported, preprocessing_models_supported
from nltk.util import ngrams
import numpy as np
from .open_source_helpers import *
import os
from pinecone import Pinecone, PineconeException, ServerlessSpec
from pydantic import SecretStr
import tiktoken
import time
import torch
import torch.nn.functional as F
from translations.helpers.translate import translate
from typing import List

logger = logging.getLogger('django')
USER_AGENT = os.getenv('USER_AGENT')


__all__ = ['CustomEmbeddings', 'Document', 'Website', 'connect_to_pinecone', 'create_index_if_not_present', 'delete_obsolite_vectors_from_index', 'format_full_web_address','generate_embedding', 'preprocess', 'select_preprocessing_model' ]

# Object classes ------------------------------------------------

openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    raise RuntimeError("OPENAI_API_KEY environment variable is not set.")

# Defines a custom wrapper similar to HuggingFaceEmbeddings, but allows for use of both sentence-transformer and BERT models
# Correct fixes for your CustomEmbeddings class

class CustomEmbeddings(Embeddings):  # Now inherits from Embeddings
    def __init__(self, user):
        super().__init__()  # Call parent constructor
        self.user = user
        tokenization_and_vectorization_model = user.aichat_userprofile.tokenization_and_vectorization_model
        logger.info(f"running CustomEmbeddings ... tokenization_and_vectorization_model is: { tokenization_and_vectorization_model }")
        
        if tokenization_and_vectorization_model in ['gpt-4o', 'gpt-4o-mini']:
            # Fix 1: Handle the SecretStr issue by checking if OPENAI_API_KEY is not None
            if openai_key:
                self.embeddings = OpenAIEmbeddings(
                    model="text-embedding-ada-002",
                    api_key=SecretStr(openai_key)
                )
            else:
                # Let OpenAIEmbeddings use environment variable automatically
                self.embeddings = OpenAIEmbeddings(
                    model="text-embedding-ada-002"
                )
            self.use_openai = True
        else:
            self.embeddings = OpenSourceEmbeddings(tokenization_and_vectorization_model)
            self.use_openai = False

    # Fix 2: Match the parameter names from the base class
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """Embed search docs - parameter name matches base class"""
        logger.debug(f'running CustomEmbeddings ... embedding texts: {texts}')
        return self.embeddings.embed_documents(texts)
        
    # Fix 3: Match the parameter names from the base class
    def embed_query(self, text: str) -> List[float]:
        """Embed query text - parameter name matches base class"""
        logger.debug(f'running CustomEmbeddings ... embedding text: {text}')
        return self.embeddings.embed_query(text)
    
    def __call__(self, text: str) -> List[float]:
        # This makes the object callable like a function
        return self.embed_query(text)



# Define the Document class
class Document:
    def __init__(self, page_content, metadata, similarity=None):
        self.page_content = page_content
        self.metadata = metadata
        self.similarity = similarity

    def __str__(self):
        # Create a string representation that includes the source and page number
        source = self.metadata.get('source', 'No Source')
        page_number = self.metadata.get('page_number', 'Unknown Page')
        return f'Document(source={source}, page_number={page_number})'

    def __repr__(self):
        # Use the string representation for repr as well
        return self.__str__()




class Website:
    def __init__(self, page_content, metadata, similarity=None):
        self.page_content = page_content  # Main content for embedding and retrieval
        self.metadata = metadata          # Metadata containing additional information like source, title, etc.
        self.similarity = similarity      # Optional similarity attribute for retrieved results

    def __str__(self):
        # Include main identifying features in the string representation
        title = self.metadata.get('title', 'No Title')
        source = self.metadata.get('source', 'No Source')
        return f'Website(title={title}, source={source})'

    def __repr__(self): 
        # Use the __str__ method for representation consistency
        return self.__str__()





# Helper functions ------------------------------------------------
# Global variable to store the Pinecone instance and avoid unnessary duplicate attempts to log into Pinecone


# Function 1: Calculate similarity between two text chunks (used for citation generation)
# Fix the calculate_similarities function (around line 103)

def calculate_similarities(retrieved_chunks, answer_text, user):
    source_data_chunks = [chunk.page_content for chunk in retrieved_chunks]
    
    # Initialize model and tokenizer
    tokenization_and_vectorization_model = user.aichat_userprofile.tokenization_and_vectorization_model

    # Get embeddings based on model type
    if tokenization_and_vectorization_model in ['gpt-4o', 'gpt-4o-mini']:
        # Fix: Remove the openai_api_key parameter entirely or handle None case
        if openai_key:
            embeddings_generator = OpenAIEmbeddings(api_key=SecretStr(openai_key))
        else:
            # Let it use environment variable automatically
            embeddings_generator = OpenAIEmbeddings()
        
        # Get embeddings
        embedding_answer = torch.tensor(embeddings_generator.embed_query(answer_text)).unsqueeze(0)
        embeddings_chunks = torch.tensor(embeddings_generator.embed_documents(source_data_chunks))

    else:
        # Get embeddings
        embedding_answer = generate_embeddings_open_source(tokenization_and_vectorization_model=tokenization_and_vectorization_model, text_list=answer_text, is_single=True)
        embeddings_chunks = generate_embeddings_open_source(tokenization_and_vectorization_model=tokenization_and_vectorization_model, text_list=source_data_chunks)

    # 2. Calculate n-gram overlap
    def calculate_ngram_overlap(text1, text2, n=3):
        # Convert texts to n-grams
        ngrams1 = set(map(''.join, ngrams(text1.lower().split(), n)))
        ngrams2 = set(map(''.join, ngrams(text2.lower().split(), n)))
        
        if not ngrams1 or not ngrams2:
            return 0.0
        
        # Calculate Jaccard similarity
        overlap = len(ngrams1.intersection(ngrams2)) / len(ngrams1.union(ngrams2))
        return overlap

    # 3. Calculate key phrase overlap
    def extract_key_phrases(text):
        # Simple key phrase extraction using noun phrases
        words = text.lower().split()
        # Remove common words and keep potential key phrases
        return set([w for w in words if len(w) > 3])

    # Calculate final similarities using multiple metrics
    final_similarities = []
    chunk_metadata = []
    
    for i, chunk in enumerate(retrieved_chunks):
        # Calculate semantic similarity
        semantic_sim = F.cosine_similarity(embedding_answer, embeddings_chunks[i].unsqueeze(0)).item()
        
        # Calculate n-gram overlap
        ngram_sim = calculate_ngram_overlap(text1=answer_text, text2=source_data_chunks[i])
        
        # Calculate key phrase overlap
        answer_phrases = extract_key_phrases(text=answer_text)
        source_data_chunk_phrases = extract_key_phrases(text=source_data_chunks[i])
        phrase_sim = len(answer_phrases.intersection(source_data_chunk_phrases)) / len(answer_phrases.union(source_data_chunk_phrases)) if answer_phrases and source_data_chunk_phrases else 0
        
        # A weighed version of the three scoring methodologies used above
        combined_score = (0.5 * semantic_sim) + (0.3 * ngram_sim) + (0.2 * phrase_sim)
        
        # Apply temperature scaling for better differentiation
        temperature = 0.1
        scaled_score = np.exp(combined_score / temperature)
        
        final_similarities.append(scaled_score)
        chunk_metadata.append({
            "source": chunk.metadata.get("source"),
            "page": chunk.metadata.get("page_number"),
            "semantic_sim": semantic_sim,
            "ngram_sim": ngram_sim,
            "phrase_sim": phrase_sim
        })

    # Normalize scores
    max_score = max(final_similarities)
    min_score = min(final_similarities)
  
    normalized_similarities = []
    for score in final_similarities:
        if max_score != min_score:
            normalized_score = (score - min_score) / (max_score - min_score)
        else:
            normalized_score = score
        normalized_similarities.append(normalized_score)

    # Pair each chunk with it's final score (e.g. normalized_score, which is stored in the normalized_similarities list)
    similarities_list = list(zip(normalized_similarities, chunk_metadata))
    
    logger.debug(f'calculate_similarities() - answer_text: {answer_text}')
    logger.debug(f'calculate_similarities() - similarities_list: {similarities_list}')
    
    return similarities_list








def clean_website_content(html_content):
    soup = BeautifulSoup(html_content, "html.parser")
    # Remove unnecessary tags
    for tag in soup(["script", "style", "header", "footer", "nav", "aside"]):
        tag.extract()
    # Extract main text
    main_content = soup.get_text(separator=" ")
    return main_content



# Function 2: Connect to Pinecone
def connect_to_pinecone(user):
    logger.debug(f'running connect_to_pinecone() ... function started')
    
    deleted_existing_index = False  # Default value if no index is deleted

    # Set the Pinecone API key and profile (aka 'pc')
    PINECONE_API_KEY = os.getenv('PINECONE_API_KEY')
    if not PINECONE_API_KEY:
        logger.error("running connect_to_pinecone() ... error: PINECONE_API_KEY not set.")
        raise ValueError("Pinecone API key is not set.")
    
    pc = Pinecone(api_key=PINECONE_API_KEY)
    logger.debug(f'running connect_to_pinecone() .... set pinecone API key and pc is: { pc }')
    
    index_name = 'vectorized-sources' # EXPOSE THIS LATER
    similarity_metric = user.aichat_userprofile.similarity_metric

    # Create the index if it doesn't already exist
    create_index_if_not_present(
        index_name=index_name,
        similarity_metric=similarity_metric, # EXPOSE THIS LATER
        pc=pc,
        user=user,
    )

    namespace = str(user.id)
    
    # If the index already exists, but the index's number of dimensions doesn't match the 
    # number of dimensions for the current tokenization_and_vectorization_model, 
    # delete the exiting index and re-create it with the correct number of dimensions
    index_stats = pc.Index(index_name).describe_index_stats()
    existing_index_dimensions = index_stats['dimension']
    model_name = user.aichat_userprofile.tokenization_and_vectorization_model
    selected_model_dimensions = int(tokenization_and_vectorization_models_supported[model_name]['vector_dimensions'])
    logger.debug(f'running connect_to_pinecone() .... '
                f'existing_index_dimensions is: { existing_index_dimensions } and '
                f'selected_model_dimensions is: { selected_model_dimensions }. ')

    if existing_index_dimensions != selected_model_dimensions:
        logger.debug(f'running connect_to_pinecone() ... deleting existing index with index_name: { index_name } and pc: { pc }. Will then re-create it due to mismatch in vectors.')
        
        deleted_existing_index = delete_index(index_name=index_name, pc=pc)
        logger.info(f'running connect_to_pinecone() .... deleted index with index_name: { index_name }')
        
        # After deleting the old index, crate the new one with the correct number of dimensions
        create_index_if_not_present(
            index_name=index_name,
            similarity_metric=similarity_metric, # EXPOSE THIS LATER
            pc=pc,
            user=user
        )
        logger.debug(f'running connect_to_pinecone() .... re-created index with index_name: { index_name }')

    # Finally, log into the index
    index = pc.Index(index_name)
    logger.debug(f'running connect_to_pinecone() .... connected to index: { index } with index_name: { index_name }. Namespace is: { namespace }')

    return deleted_existing_index, index, namespace



# Function 3: Count the number of tokens in a string using the tiktoken library
def count_tokens(text, retriever_model):
    logger.debug(f'running count_tokens() ... function started')
    enc = tiktoken.encoding_for_model(retriever_model)
    #enc = tiktoken.get_encoding(retriever_model)
    return len(enc.encode(text))



# Function 4: Create a specified Pinecone index, creating a new index by that name, if needed
def create_index_if_not_present(index_name, similarity_metric, pc, user):
    logger.info(f'running create_index_if_not_present() ... function started, '
                 f'index_name is: { index_name }, '
                 f'similarity_metric is: { similarity_metric }, pc is: { pc }'
                 )

    model_name = user.aichat_userprofile.tokenization_and_vectorization_model
    selected_model_dimensions = int(tokenization_and_vectorization_models_supported[model_name]['vector_dimensions'])
    
    if index_name not in [index['name'] for index in pc.list_indexes()]:
        pc.create_index(
                name=index_name,
                dimension=selected_model_dimensions,  # Ensure this matches your model output dimensions. # Previously used: 384  Mbert is: 768
                metric=similarity_metric, # Options include 'cosine', 'euclidean', 'dotproduct'. The metric should ideally match the type of distance or similarity your model was designed to produce. More information here: https://www.pinecone.io/learn/vector-similarity/
                spec=ServerlessSpec( # Configs for Pinecone's offering that handles server for the user. More info here: https://docs.pinecone.io/guides/indexes/create-an-index#create-a-serverless-index
                    cloud='aws',
                    region='us-east-1'
                )
            )
        # Add a brief delay to ensure the index is created
        time.sleep(5)
        
        logger.info(f'running create_index_if_not_present() ...'
                    f'new Pinecone index created with index_name: { index_name }'
                    )
    else:
        logger.info(f'running create_index_if_not_present() ... index_name: { index_name } already present, no new index created')                    



# Function 5: Create a vector ID for a vector (appened to aichat_vector and Pinecone records)
def create_vector_id(vector_content, user):
    logger.debug(f'running create_vector_id() ... '
                f'function started with content: { vector_content } and user: { user }')

    user_id = str(user.id)
    hased_vector_content = hashlib.sha256(vector_content.encode()).hexdigest()

    vector_id = 'user:'+user_id+' - '+hased_vector_content
    logger.debug(f'running create_vector_id() ... '
                f'returning vector_id: { vector_id }')

    return vector_id



# Function 6: Delete all Pinecone indexes
def delete_all_indexes(pc):
    logger.debug(f'running delete_all_indexes() ... function started, pc is: { pc }')
    
    # List all indexes
    indexes = pc.list_indexes()

    # Delete each index by its name
    for index in indexes:
        index_name = index['name']  # Extract the name of the index
        logger.debug(f'running delete_all_indexes() ... deleting index: {index_name}')
        pc.delete_index(index_name)
        logger.debug(f'running delete_all_indexes() ... index_name: {index_name} deleted successfully')



# Function 7: Delete a specific Pinecone index
def delete_index(index_name, pc):
    logger.debug(f'running vectorize_db.py, delete_index() ... starting function, index_name is: { index_name } and pc is: { pc }')

    deleted_existing_index = False
    
    index_list = [index['name'] for index in pc.list_indexes()]
    logger.debug(f'running vectorize_db.py, delete_index() ... index_list is: { index_list }')

    # Check if the specified index exists
    if index_name in index_list:

        # Delete the specified index
        pc.delete_index(index_name)
        deleted_existing_index = True
        time.sleep(5)
        logger.info(f'running vectorize_db.py, delete_index() ... deleted index with index_name: {index_name}')
    
    # If the specified index does not exist, throw an error
    else:
        logger.error(f'running vectorize_db.py, delete_index() ... index: {index_name} does not exist.')
        raise ValueError(f"Index name: '{index_name}' does not exist.")
    return deleted_existing_index



# Function 8: Delete specified vectors from a specified index (used for removing obsolite vectors from the index)
def delete_obsolite_vectors_from_index(index, namespace, pc, vector_ids_to_delete_from_index):
    logger.info(f'running delete_obsolite_vectors_from_index() ... function started')
    
    try:
        # Assuming you have already connected to the Pinecone index as 'index'
        index_name = 'vectorized-sources' # EXPOSE LATER
        index_description = pc.describe_index(index_name)
        number_of_vectors_to_delete = len(vector_ids_to_delete_from_index)
        vector_count_starting = index_description['total_vector_count']
        logger.info(f'running delete_obsolite_vectors_from_index() ... before deletion, index_name is: { index_name } and '
                    f'vector_count_starting is: { vector_count_starting } and '
                    f'number_of_vectors_to_delete is: { number_of_vectors_to_delete }'
                    )

        # Delete from Pinecone the obsolite vectors pulled from SQL above
        if vector_ids_to_delete_from_index:
        
            # Delete all vectors in Pinecone that have IDs in sql_vectors_to_delete
            index.delete(ids=vector_ids_to_delete_from_index, namespace=namespace)
            # Assuming you have already connected to the Pinecone index as 'index'
            index_description = pc.describe_index(index_name)
            number_of_vectors_to_delete = len(vector_ids_to_delete_from_index)
            vector_count_ending = index_description['total_vector_count']
            logger.debug(f'running delete_obsolite_vectors_from_index() ... '
                        f'index_name is: { index_name }, '
                        f'vector_count_starting was: { vector_count_starting }, '
                        f'number_of_vectors_to_delete was: { number_of_vectors_to_delete }, '
                        f'after deletion, vector_count_ending is: { vector_count_ending }')
            return True  # Success flag
        else:
            logger.debug('running delete_obsolite_vectors_from_index() ... No vectors to delete from Pinecone.')
            return True  # Still successful since there's nothing to delete
        
        
    except PineconeException as e:
        logger.error(f'running delete_obsolite_vectors_from_index ...'
                        f'Error deleting vectors from Pinecone: {e}'
                        )



# Function 9: Delete all vectors with a specified namespace, within a specified Pinecone index
def delete_vectors_by_namespace(index_name, namespace, pc):
    logger.debug(f'running delete_vectors_by_namespace() ... '
                 f'function started, index_name is: { index_name }, '
                 f'namespace is: { namespace } and pc is: { pc }'
                 )
    
    index_list = [index['name'] for index in pc.list_indexes()]
    logger.debug(f'running delete_vectors_by_namespace() ... index_list is: { index_list }')

    # Check if the specified index exists
    if index_name in index_list:

        # Connect to the specified index
        index = pc.Index(index_name)
        logger.debug(f'running delete_vectors_by_namespace() ... connected to index: { index }')
    
        # Define a filter to select vectors with the specified type
        filter_query = {'namespace': {'$eq': namespace}}
        logger.debug(f'running delete_vectors_by_namespace() ... filter_query is: { filter_query }')

        # Query vectors from the specified index based on the filter
        try:
            index.delete(namespace=namespace)
            logger.debug(f'running delete_vectors_by_namespace() ... '
                        f'deleted vectors with namespace: { namespace } '
                        f'from index: { index }'
                        )
        except Exception as e:
            logger.error(f'running delete_vectors_by_namespace() ... '
                         f'failed to delete vectors in namespace: {namespace} '
                         f'from index: {index_name}. Error: {e}'
                         )

    # If the specified index does not exist, throw an error
    else:
        logger.error(f'running delete_vectors_by_namespace() ... '
                     f'index: {index_name} does not exist.'
                     )
        raise ValueError(f'running delete_vectors_by_namespace() ... index name: { index_name } does not exist.')



# Function: Take user inputted simplified doman and converts it into a full html address (e.g. 'google.com' --> 'https://www.google.com')
def format_full_web_address(abbreviated_url):
    logger.debug(f'running format_full_web_address() ... function started')

    # Option 1: Check if abbreviated_url is None or an empty string. If yes, just return it as is.
    if not abbreviated_url:
        logger.debug(f'running format_full_web_address() ... abbreviated URL is None or an empty string, returning that same value')
        return abbreviated_url

    # Option 2: If the URL already starts with 'http://www.' or 'https://www.' (e.g. https://www.google.com), return it as is
    if abbreviated_url.startswith('http://www.') or abbreviated_url.startswith('https://www.'):
        logger.debug(f'running format_full_web_address() ... URL already has a scheme, returning: {abbreviated_url}')
        return abbreviated_url
    
    # Option 3: If the URL already starts with 'www.' but not 'http://' or 'https://' (e.g. www.google.com), prepend https://
    if abbreviated_url.startswith('www.'):
        full_url = f"https://{abbreviated_url}"
        logger.debug(f'running format_full_web_address() ... URL already has a scheme, returning: {abbreviated_url}')
        return full_url

    # Option 4: If the URL has neither 'https', 'http', nor 'www' (e.g. google.com), preprend both 
    full_url = f"https://www.{abbreviated_url}"
    logger.debug(f'running format_full_web_address() ... prepended https:// to abbreviated_url: {abbreviated_url}, full_url is: {full_url}')
    return full_url









# Function 10: Generate embeddings for a given text (called via CustomEmbeddings.embed_sources and CustomEmbeddings.embed_query)
def generate_embedding(huggingface_model, text, tokenizer):
    logger.debug(f'running generate_embedding() ... function started, '
                f'huggingface_model is: { huggingface_model }, '
                f'text is: { text }, '
                f'len(text) is: { len(text) }, '
                f'tokenizer is: { tokenizer }'
                )

    tokenizer_max_length = tokenizer.model_max_length
    logger.debug(f'running generate_embeddings() ... tokenizer_max_length is: { tokenizer_max_length }')
    
    max_length_set = min(tokenizer_max_length, settings.TOKENIZER_MAX_LENGTH_FIXED)
    logger.debug(f'running generate_embeddings() ... max_length_set is: { max_length_set }')

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=max_length_set
    )
    outputs = huggingface_model(**inputs)
    logger.debug(f'running generate_embeddings ... outputs is: { outputs }')

    if huggingface_model.config.architectures and 'BERT' in huggingface_model.config.architectures[0]:
        logger.debug(f'running generate_embeddings ... updating embedding structure for BERT')
        # Use [CLS] token for BERT-based models
        embedding = outputs.last_hidden_state[:, 0, :].detach().numpy().flatten()
    
    elif huggingface_model.config.architectures and 'XLMRoberta' in huggingface_model.config.architectures[0]:
        logger.debug(f'running generate_embeddings ... updating embedding structure for XLMRoberta')
        # For XLM-RoBERTa and other RoBERTa-based models, use mean pooling across all tokens
        embedding = outputs.last_hidden_state.mean(dim=1).detach().numpy().flatten()
    
    else:
        logger.debug(f'running generate_embeddings ... defaulting to normal embedding structure')
        # Default to mean pooling if model architecture is unknown
        embedding = outputs.last_hidden_state.mean(dim=1).detach().numpy().flatten()

    # Log the length of the resulting embedding and return the result
    logger.debug(f'running generate_embedding() ... finished function with the following: '
                f'len(text) (input length) was: { len(text) }, '
                f'len(embedding) (output length) is: { len(embedding) }'
                )
    return embedding.tolist()



# Function 11: Select the system_prompt based on whether general knowledge is allowed
def generate_system_prompt(ignore_chat_history_bool, use_general_knowledge_bool):
    logger.debug(f'running generate_system_prompt() ... function started')
    
    if use_general_knowledge_bool:
        # Case 1: General knowledge + NO chat history
        if ignore_chat_history_bool:
            system_prompt = (
                "You're a helpful research assistant who speaks many languages. "
                "Use information provided by the user in the chat and the following websites and uploaded documents as the primary source of information to answer user questions: {context}, even if that context is incomplete. "
                "If the answer to the user's question is from {context} you must begin your response with exactly the following phrase: {context_available_phrase_translated}. "
                "You may now use general knowledge to answer questions. If the answer to a user's question is not derived from the documents uploaded or from chat history, you must begin your response with exactly the following phrase: {general_knowledge_phrase_translated}. "
                "Respond in {response_length} sentences or fewer in {language} and keep the answer concise. "
                "You may converse with the user in a friendly manner. "
                "\n\n"
            )
        # Case 2: General knowledge + chat history
        else:
            system_prompt = (
                "You're a helpful research assistant who speaks many languages. "
                "Use information provided by the user in the chat and the following websites and uploaded documents as the primary source of information to answer user questions: {context}, even if that context is incomplete. "
                "If the answer to the user's question is in the uploaded documents and/or websites, but not from chat history, you must begin your response with exactly the following phrase: {context_available_phrase_translated}. "
                "If the answer to the user's question is from chat history, you must begin your response with exactly the following phrase: {chat_history_phrase_translated}. "
                "You may now use general knowledge to answer questions. If the answer to a user's question is not derived from the documents uploaded or from chat history, you must begin your response with exactly the following phrase: {general_knowledge_phrase_translated}. "
                "Respond in {response_length} sentences or fewer in {language} and keep the answer concise. "
                "You may converse with the user in a friendly manner. "
                "\n\n"
            )

    else:
        # Case 3: NO General knowledge + NO chat history
        if ignore_chat_history_bool:
            system_prompt = (
                "You're a helpful research assistant who speaks many languages. "
                "Use only the information in the following context to answer user questions: {context}, even if that context is incomplete. "
                "If the answer to the user's question is in {context}, you must begin your response with exactly the following phrase: {context_available_phrase_translated}. "
                "If you don't know the answer to a user question, respond with exactly the following phrase: {no_answer_phrase_translated}. "
                "Respond in {response_length} sentences or fewer in {language} and keep the answer concise. "
                "You may converse with the user in a friendly manner. "
                "\n\n"
            )
        # Case 4: NO general knowledge + chat history
        else:
            system_prompt = (
                "You're a helpful research assistant who speaks many languages."
                "Use only the information provided by the user in the chat and in the following context to answer user questions: {context}, even if that context is incomplete. "
                "If the answer to the user's question is in the uploaded documents and/or websites, but not from chat history, you must begin your response with exactly the following phrase: {context_available_phrase_translated}. "
                "If the answer to the user's question is from chat history, you must begin your response with exactly the following phrase: {chat_history_phrase_translated}. "
                "If you don't know the answer to a user question, respond with exactly the following phrase: {no_answer_phrase_translated}. "
                "Respond in {response_length} sentences or fewer in {language} and keep the answer concise. "
                "You may converse with the user in a friendly manner. "
                "\n\n"
            )
    return system_prompt




# Function 12: Return sources in a structured format
def return_sources(detected_language, deduplicated_sources):
    logger.debug(f'return_sources() ... function started')
    
    source_cutoff = 0  # Used to ignore the first source, which seems to improve results
    
    if detected_language == 'en':
        sources_string_formatted = 'Sources:'
    else:
        translated_result = translate(input_text='Sources:', from_language='en', to_language=detected_language)
        # Ensure we get a string from the translate function
        sources_string_formatted = str(translated_result) if translated_result is not None else 'Sources:'
    
    for source in deduplicated_sources[source_cutoff:]:
        sources_string_formatted += f'{str(source)}\n'
    return sources_string_formatted



# Function 13: Select te preprocessing model to be used, based on a specified human language
def select_preprocessing_model(language_code):
    logger.info(f'running select_preprocessing_model() ... function started')

    fallback_model = 'xx_sent_ud_sm'

    # Iterate through preprocessing_models_supported to find a matching language_code
    for model_key, model_info in preprocessing_models_supported.items():
        if model_info.get('language_code') == language_code:
            logger.debug(f'running select_preprocessing_model() ... '
                        f'model_key is: {model_key} for '
                        f'language_code is: {language_code}')
            return model_key
        
    # Default to multilingual model if no match is found
    logger.warning(f'running select_preprocessing_model() ... '
                   f'no model_key found for language_code: {language_code} '
                   f'Falling back to: { fallback_model }')
    return fallback_model

