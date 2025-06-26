import os
import sys
import django

# Add the project root to the system path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
sys.path.insert(0, project_root)

# Set the settings module
if "DJANGO_SETTINGS_MODULE" not in os.environ:
    settings_module = os.getenv("PROJECT_SETTINGS_FILE")
    if not settings_module:
        raise RuntimeError("PROJECT_SETTINGS_FILE environment variable is not set.")
    os.environ["DJANGO_SETTINGS_MODULE"] = settings_module


# Setup Django
django.setup()

import logging
from django.db.models import Q
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from aichat_chat.models import Expert, Experience, Topic
from pinecone import Pinecone
from transformers import AutoTokenizer, AutoModel
import numpy as np
from translations.helpers.translate import detect_language, supported_languages_selected, translate



from sentence_transformers import SentenceTransformer

logger = logging.getLogger('django')

# Setting up environment variables for OpenAI
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    raise RuntimeError("OPENAI_API_KEY environment variable is not set.")

openai_model = os.getenv("OPENAI_MODEL")
if not openai_model:
    raise RuntimeError("OPENAI_MODEL environment variable is not set.")

pc = Pinecone(api_key=os.getenv("PINECONE_API_KEY"))
if not pc:
    raise RuntimeError("PINECONE_API_KEY environment variable is not set.")
index = pc.Index('experts')  # Connect to the appropriate index

# Using working ChatOpenAI import; ignoring type checker due to mismatch with stubs
llm = ChatOpenAI(  
    model_name=openai_model,  # type: ignore
    api_key=openai_key,  # already validated earlier
    temperature=0.7
)

# Initialize the model for vectorization
model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')


def retrieve_experts(
        input_text, 
        number_of_experts,
        detected_language,
        user,
        ):
    logger.info(f'running retrieve_experts() ... '
                 f'input_text is: { input_text }, '
                 f'number_of_experts is: { number_of_experts }, '
                 f'detected_language is: { detected_language },'
                 )

    system_prompt_terms = f"""\
    You are an AI assistant that extracts key terms and closely related terms from a query.

    Given a user query, extract key terms and use general knowledge to identify the following:
    1. Five closely-related topics. \
        For example, if the query contains information about hops (an ingredient in beer production), then include related topics such as 'consumer goods', 'alcohol' and 'beer' as related terms. \
        As another example, if the query contains information about cancer, then include related topics such as 'healthcare', 'wellness', 'oncology', etc. as related terms. \
    2. The top 2 industries most closely related to the user's question.  \
        For example, if the user asks about 'beer', the top industries should be 'food and beverage' and 'alcohol', since beer, since those industries match the related terms identified. \
        As another example, if the user asks about 'cancer', then 'healthcare' should be a top industry.
    """

    prompt_terms = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt_terms),
            ("human", f"Extract key terms and related terms from the query: '{input_text}'"),
        ]
    )

    chain_terms = prompt_terms | llm

    response = chain_terms.invoke({"input_text": input_text})
    extracted_terms = response.content
    logger.debug(f'running retrieve_experts() ... extracted terms is: { extracted_terms }')

    # Since expert DB is in english, translate the key terms to english for better matching results
    if detected_language != 'en':
        extracted_terms_translated = translate(
            input_text=extracted_terms, 
            from_language=detected_language, 
            to_language='en'
            )
    else:
        extracted_terms_translated = extracted_terms
    logger.info(f'running retrieve_experts() ... extracted terms_translated is: { extracted_terms_translated }')

    # Vectorize the extracted terms
    query_vector = model.encode(str(extracted_terms_translated)).tolist()
    #logger.debug(f'running retrieve_experts() ... query_vector is: { query_vector }')

    # Query Pinecone vector database
    query_response = index.query(
        vector=query_vector, 
        top_k=20, 
        include_metadata=True
        )
    logger.debug(f'running retrieve_experts() ... querying the pinecone database')
    
    # Process the query response
    
    expert_ids = [match['metadata']['expert_id'] for match in query_response['matches']] # type: ignore
    if not expert_ids:
        return ["No experts available on this topic"]

    # Retrieve Expert objects from the database
    related_experts = Expert.objects.filter(id__in=expert_ids)
    logger.debug(f'running retrieve_experts() ... related experts is: { related_experts }')
    
    # If expert_speaks_my_lang_bool = true, then filter out any experts who don't speak the user's language
    if user.aichat_userprofile.expert_speaks_my_lang:
        
        # Filter related_experts to include only results where there is a language match
        related_experts = related_experts.filter(languages__language__code=detected_language) # Note use of double underscore due to how language is a foreign key to expert

    expert_data = []
    years_weight = float(user.aichat_userprofile.weight_years)
    industry_weight = float(user.aichat_userprofile.weight_industry)
    role_weight = float(user.aichat_userprofile.weight_role)
    topic_weight = float(user.aichat_userprofile.weight_topic)
    geography_weight = float(user.aichat_userprofile.weight_geography)

    for expert in related_experts:
        experiences = expert.experiences.all() # type: ignore
        first_experience = experiences[0] if len(experiences) > 0 else None
        second_experience = experiences[1] if len(experiences) > 1 else None
        
        total_years = str(sum(experience.years for experience in expert.experiences.all())) # type: ignore

        
        # Split extracted terms into individual words
        extracted_terms_words = str(extracted_terms_translated).split()
        logger.debug(f'running retrieve_experts() ... extracted_terms_words is: { extracted_terms_words }')


        # Initialize scores
        industry_score = 0
        role_score = 0
        topic_score = 0
        years_score = 0
        geography_score = 0

        # Calculate years score
        for experience in experiences:
            years_score += round(float(experience.years) * years_weight, 2)

        # Calculate industry score
        for experience in experiences:
            industry_matches = sum(1 for term in extracted_terms_words if term.lower() in experience.industry.lower())
            logger.debug(f'running retrieve_experts() ... for expert: { expert.name_first } { expert.name_last }, experience: { experience.role }, { experience.employer }, industry_matches is: { industry_matches }')
            industry_score += industry_matches * industry_weight

        # Calculate role score
        for experience in experiences:
            role_matches = sum(1 for term in extracted_terms_words if term.lower() in experience.role.lower())
            logger.debug(f'running retrieve_experts() ... for expert: { expert.name_first } { expert.name_last }, experience: { experience.role }, { experience.employer }, role_matches is: { role_matches }')
            role_score += round(role_matches * role_weight, 2)

        # Calculate topic score
        for topic in expert.topics.all(): # type: ignore
            topic_matches = sum(1 for term in extracted_terms_words if term.lower() in topic.topic.lower())
            logger.debug(f'running retrieve_experts() ... for expert: { expert.name_first } { expert.name_last }, experience: { experience.role }, { experience.employer } topic_matches is: { topic_matches }') # type: ignore
            topic_score += round(topic_matches * topic_weight, 2)


        # Calculate geography score
        for experience in experiences:
            if experience.geography:  # Check if geography is not None
                geography_fields = [
                    experience.geography.country,
                    experience.geography.region,
                ]

                # Calculate matches for each geography field
                geography_matches = sum(
                    1 for term in extracted_terms_words 
                    for field in geography_fields 
                    if term.lower() in field.lower()
                )
                logger.debug(f'running retrieve_experts() ... for expert: { expert.name_first } { expert.name_last }, experience: { experience.role }, { experience.employer } geography_fields is: { geography_fields } and extracted_terms_words is: { extracted_terms_words }, resulting in geography_matches of: { geography_matches }')
                


                geography_score += round(geography_matches * geography_weight, 2)

        # Total score
        total_score = round(years_score + industry_score + role_score + topic_score + geography_score, 2)

        logger.debug(f'running retrieve_experts() ... expert is: {expert}, total_score is: {total_score}, years_score is: {years_score}, industry_score is: {industry_score}, role_score is: {role_score}, topic_score is: {topic_score}, geography_score is: {geography_score}')

        # Check if the current expert as been favorited by the logged-in user
        # Check if this expert is a favorite of the user
        is_favorite = expert.added_as_favorite_by.filter(user=user).exists() # type: ignore

        expert_data.append({
            'id': expert.id, # type: ignore
            'is_favorite': is_favorite,
            'name_first': expert.name_first,
            'name_last': expert.name_last,
            'photo': expert.photo,
            'role1': first_experience.role if first_experience else None,
            'employer1': first_experience.employer if first_experience else None,
            'regionCode1': first_experience.geography.region_code if first_experience else None,
            'role2': second_experience.role if second_experience else None,
            'employer2': second_experience.employer if second_experience else None,
            'regionCode2': second_experience.geography.region_code if second_experience else None,
            'total_years': total_years,
            'total_score': total_score,
            'languages_spoken': ', '.join([language.language.name for language in expert.languages.all()]) # type: ignore

        })
        
    
    # Sort experts by total_score in descending order
    expert_data.sort(key=lambda x: x['total_score'], reverse=True)

    # Return top 3 experts
    return expert_data[:number_of_experts]
