from django.utils import timezone
from langchain_community.document_loaders import WebBaseLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
import logging
from ..models import Vector
import os
import spacy
from translations.helpers.translate import detect_language
from urllib.parse import urlparse
from .vectorize_helpers import clean_website_content, create_vector_id, CustomEmbeddings, connect_to_pinecone, preprocess, select_preprocessing_model, Website 


# Set the settings module and logger
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homepage.settings')
logger = logging.getLogger('django')

__all__ = ['vectorize_web']


# Function to vectorize website and store it in Pinecone
def vectorize_web( 
        index,
        namespace,
        summary_method, # Options: 'mean_last_layer' or 'CLS'
        urls, # A list of websites to RAG
        user,
        ):
    logger.info(f'running vectorize_web() .... function started,'
                 f'summary_method is: { summary_method }, '
                 f'urls is: { urls }, '
                 f'user is: { user } '
                 )
    
    
    # Step 1: Connect to Pinecone index
    deleted_existing_index, index, namespace = connect_to_pinecone(user)
    logger.debug(f'running vectorize_web() ... index is: { index } and namespace is: { namespace }')

    
    # Step 2: Determine the preprocessing model is specified (e.g. not auto-select).
    userprofile = user.aichat_userprofile
    preprocessing_model = userprofile.preprocessing_model
    preprocessing = userprofile.preprocessing
    
    if preprocessing_model == 'auto-detect':
        auto_detect_preprocessing_model = True
    else:
        auto_detect_preprocessing_model = False
    logger.info(f'running vectorize_web() ... auto_detect_preprocessing_model is: { auto_detect_preprocessing_model }')


    # Step 2: Load the urls via LangChain's WebBaseLoader
    loader = WebBaseLoader(web_paths=urls)
    website_data = loader.load()
    logger.debug(f'running vectorize_web() ... website_data is: { website_data }')


    # Step 3: Attach metadata to each website and create a Website instance for that website    
    websites = [] # Initialize a list to hold the website content
    logger.debug(f'running vectorize_web() ... websites[] intialized to: { websites }')    
   

    # Step 4: Instantiates the mechanism from vectorize_helpers.py by which the doc embeddings will be generated
    embedding_generator = CustomEmbeddings(user=user)
    logger.info(f'running vectorize_web() ... embedding_generator is: { embedding_generator }')


    # Step 5: Cycle through the websites and create a 'Website' data structure for each website
    for website in website_data:
        source = website.metadata['source']  # Note that LangChain's WebBasedLoader returns url as 'source'  See: https://python.langchain.com/v0.2/docs/integrations/document_loaders/web_base/
        top_level_domain = urlparse(source).netloc
        title = website.metadata.get('title', 'No Title Available')  # Optionally extract the title, if available
        date_accessed = str(timezone.now().date())  # Optionally extract the date of access, if available
        text = clean_website_content(website.page_content.strip())
        logger.debug(f'running vectorize_web() ... '
                    f'source is: { source }, '
                    f'top_level_domain is: { top_level_domain }, '
                    f'title is: { title }, '
                    f'date_accessed is: { date_accessed }, '
                    f'text is: { text }')


        # For efficiency, we only detect the language if auto_detect_preprocessing_model is turned on
        if not auto_detect_preprocessing_model:
            language = None
        else:
            language = detect_language(website.page_content)


        # Create an instance of the Website class to hold the data retrieved above
        websites.append(Website(
            page_content = text,  # Note: Using page_content here, as it's the form returned by WebBaseLoader (used above)
            metadata={
                'source': source, 
                'top_level_domain': top_level_domain,
                'title': title,
                'text': text,
                'date_accessed': date_accessed,
                'user': user, # This doesn't need to be user.id, because the info doesn't go into pinecone
                'language': language,
            }
        ))
        #websites.append(website_instance) # Append the newly-creaded Website instance to websites[]
    logger.info(f'running vectorize_web() ... finnished appending to websites[], websites[] is: { websites }')


    # Step 6: Split the text from the specified websites
    chunk_size_int = int(user.aichat_userprofile.chunk_size)
    chunk_overlap_float = float(user.aichat_userprofile.chunk_overlap)
    chunk_overlap_int = int(chunk_overlap_float * chunk_size_int) 
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size_int,
        chunk_overlap=chunk_overlap_int
    )
    #all_website_splits = text_splitter.split_documents(website_data)
    all_website_splits = text_splitter.split_documents(websites)
    logger.debug(f'running vectorize_web() ...' 
                 f'text_splitter is: { text_splitter },'
                 f'all_website_splits is: { all_website_splits }'
                 )


    # Step 7: Create vectors (incl. metadata) and corresponding SQLite records
    all_website_splits_vectorized = [] # Instantiate the list that will hold the vectorized version of all_website_splits
    logger.debug(f'running vectorize_web() ... all_website_splits_vectorized instiantiated to : { all_website_splits_vectorized }')


    vector_ids_created = []
    logger.debug(f'running vectorize_web() ... vector_ids_created instiantiated to : { vector_ids_created }')

    
    # Vectorization steps----------------------------  
    # Iterate over each item in all_website_splits
    for website_split in all_website_splits:

        type= 'website' # Specified here b/c repeatedly used below

        # If preprocessing, load the model, preprocess, and generate the vectors
        if preprocessing:
            if auto_detect_preprocessing_model:
                language = website_split.metadata.get('language', 'en')  # Default to 'en'
                preprocessing_model_key = select_preprocessing_model(language_code=language)
                preprocessing_model_loaded = spacy.load(preprocessing_model_key)
            else:
                preprocessing_model_loaded = spacy.load(preprocessing_model)
                
            logger.info(f'running vectorize_web() ... '
                        f'language_code is: { language } '
                        f'preprocessing_model_key is: { preprocessing_model_key } '
                        f'preprocessing_model_loaded is: { preprocessing_model_loaded }')
        
            # Preprocess the content of the split using SpaCy.
            preprocessed_text = preprocess(nlp=preprocessing_model_loaded, text=website_split.page_content)
            embedding = embedding_generator.embed_documents([preprocessed_text])[0]
            logger.debug(f'running vectorize_web() ... '
                         f'preprocessed_text is: { preprocessed_text } and '
                         f'embedding is: { embedding }')

        # If not preprocessing, generate the vectors
        else:
            # Note that embed_documents expects a list, so despire being inside the loop and thus are passing only one item, we use list notation
            embedding = embedding_generator.embed_documents([website_split.page_content])[0]
            logger.debug(f'running vectorize_web() ... preprocessing is: { userprofile.preprocessing }')
            logger.debug(f'running vectorize_web() ... embedding is: { embedding }')

        # Attaches the metadata to the vector
        metadata = {
            'source': website_split.metadata['source'], # Used 'source' above b/c it's returned by WebBasedLoader.  See: https://python.langchain.com/v0.2/docs/integrations/document_loaders/web_base/
            'title': website_split.metadata.get('title', 'No Title Available'),
            'date_accessed': website_split.metadata.get('date_accessed', 'Unknown'),
            'text': website_split.metadata['text'],
            'type': type,
            'user': user.id, # Updating because Pinecone cannot accept a full User object
            #'language': language, Commented out b/c can't have Null for a metadata field in Pinecone
        }

        # Combine the vector and metadata
        # Note: Below, we affix an id to each chunk that is a hashed version of the chunk's content. 
        # Therefore, if the chunk remains unchanged from one run to another, the new chunk's ID will be the same as the old chunk's ID.
        vector_id = create_vector_id(vector_content=website_split.page_content, user=user)

        vector = {
            'id': vector_id,  # Unique ID for each chunk
            'values': embedding,
            'metadata': metadata
        }
        # Append the newly-created vector to the list of all vectorized splits
        all_website_splits_vectorized.append(vector)
        vector_ids_created.append(vector_id) # Append id of newly-created vector for comparison against DB
        logger.debug(f'running vectorize_web() ...'
                     f'all_websites_splits_vectorized updated to: { all_website_splits_vectorized }'
                     f'vector_ids_created updated to: { vector_ids_created }')
    
        # SQL Update or Create SQL record using update_or_create
        Vector.objects.update_or_create(
            vector_id=vector_id,
            defaults={
                'source': metadata['source'],
                'top_level_domain': top_level_domain,
                'date_accessed': date_accessed,
                'type': type,
                'embedding': embedding,
                'user': user,
                'language': language,
                'text': website_split.metadata['text'],

            }
        )
        logger.debug(f'running vectorize_web() ...'
                     f'update_or_create run for new Vector object in SQL')
    
    logger.debug(f'running vectorize_web() ...' 
                 f'vectorization of all_website splits is complete,'
                 f'all_website_splits_vectorized is: { all_website_splits_vectorized }'
                 )
    logger.info(f'running vectorize_web() ...' 
                 f'vectorization of all_website splits is complete,'
                 f'length of all_website_splits_vectorized is: { len(all_website_splits_vectorized) }'
                 )


    # Step 10: Upsert all the newly-created vectors to Pinecone
    # Note, upsert = update + insert, so if a vector with the same ID already exists in the database, it will be updated.
    index.upsert(vectors=all_website_splits_vectorized, namespace=namespace)
    logger.debug(f"running vectorize_web() ... stored {len(all_website_splits_vectorized)} website vectors in Pinecone index.")
