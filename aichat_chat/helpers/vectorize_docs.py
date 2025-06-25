from django.utils import timezone
from django.contrib.auth.models import User
import fitz
from langchain_text_splitters import RecursiveCharacterTextSplitter
import logging
from ..models import Vector
import os
from pinecone import PineconeException
import spacy
from translations.helpers.translate import detect_language
from .vectorize_helpers import create_vector_id, CustomEmbeddings, connect_to_pinecone, Document, preprocess, select_preprocessing_model
from translations.helpers.translate import detect_language


logger = logging.getLogger('django')

__all__ = ['vectorize_docs']

# The function below vectorizes pdf documents, returning all_document_splits
def vectorize_docs(files, pc, summary_method, user ):
    logger.info(f'running vectorize_docs() ... function started, '
                 f'files is: { files }, '
                 f'pc is: { pc }, '
                 f'summary_method is: { summary_method }, '
                 f'user is: { user } '
                 )

    

    # Step 1: Connect to Pinecone index
    deleted_existing_index, index, namespace = connect_to_pinecone(user)
    logger.debug(f'running vectorize_docs() ... index is: { index } and namespace is: { namespace }')

    
    # Step 2: Determine the preprocessing model is specified (e.g. not auto-select).
    userprofile = user.aichat_userprofile
    preprocessing_model = userprofile.preprocessing_model
    preprocessing = userprofile.preprocessing
    
    # If auto-detect is turned on, then do not set the preprocessing model yet. It will be set based on the language detected later.
    if preprocessing_model == 'auto-detect':
        auto_detect_preprocessing_model = True
    else:
        auto_detect_preprocessing_model = False
    logger.info(f'running vectorize_docs() ... auto_detect_preprocessing_model is: { auto_detect_preprocessing_model }')


    # Step 3: Upload the documents
    docs = []
    logger.debug(f'running vectorize_docs() ... docs[] intialized to: { docs }')

    for file in files:  # Process each uploaded file
        file_content = file.read()  # Load the file content into memory
        
        # Debugging: Print the size of the file content
        logger.debug(f"File {file.name} size: {len(file_content)} bytes")

        if not file_content:
            logger.error(f"File {file.name} is empty")
            continue
        
        document = fitz.open(stream=file_content, filetype="pdf")
        filename = file.name
        logger.debug(f'running vectorize_docs() ... '
                     f'opened filename: { filename } ')

        # Detect language for the entire document based on the first three pages
        if preprocessing:
            
            # If auto-detect, then detect the language and load the appropriate preprocessing model
            if auto_detect_preprocessing_model:
                combined_text = ""
                for page_num in range(min(3, document.page_count)):
                    page = document.load_page(page_num)
                    text = page.get_text()
                    combined_text += f" {text}"  # Accumulate text from the first three pages
                
                # Detect the language of the combined text
                if combined_text.strip():
                    language = detect_language(combined_text) or None
                preprocessing_model_key = select_preprocessing_model(language_code=language)
                
        else:
            language = None

        
        # Detect human language for current page
        for page_num in range(document.page_count):
            page = document.load_page(page_num)
            text = page.get_text()

            # Create a Document object for that page
            docs.append(Document(
                page_content=text, # page_content represents the raw text of the page, which will be the actual content that the vectorization model uses to create embeddings
                metadata={
                    'source': filename,
                    'page_number': int(page_num + 1),
                    'text': text,
                    'language': language,
                    } # text is also saved here, as this is the origional version and can will not be chunked, unlike page_content above
            ))
        # Close the document to free resources
        document.close()

    logger.debug(f'running vectorize_docs() ... docs[] now populated with: { docs }')
    logger.debug(f'running vectorize_docs() ... docs[] now populated')

    # Step 4: Chunk the data using LangChain's RecursiveCharacterTextSplitter
    chunk_size_int = int(userprofile.chunk_size)
    chunk_overlap_float = float(userprofile.chunk_overlap)
    chunk_overlap_int = int(chunk_overlap_float * chunk_size_int) 

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size = chunk_size_int,
        chunk_overlap = chunk_overlap_int,
        add_start_index=True
    )
    logger.debug(f'running vectorize_docs() ... text_splitter now set to { text_splitter }')


    all_document_splits = text_splitter.split_documents(docs)
    logger.debug(f'running vectorize_docs() ...' 
                 f'text_splitter is: { text_splitter },'
                 f'all_document_splits is: { all_document_splits }'
                 )


    # Step 5: Create vectors (incl. metadata) and corresponding SQLite records
    all_document_splits_vectorized = [] # Instantiate the list that will hold the vectorized version of all_document_splits
    logger.debug(f'running vectorize_docs() ... all_document_splits_vectorized instiantiated to : { all_document_splits_vectorized }')

    vector_ids_created = []
    vectors_for_sql = []
    logger.debug(f'running vectorize_docs() ... '
                 f'vector_ids_created instiantiated to : { vector_ids_created } and '
                 f'vectors_for_sql instantiated to: { vectors_for_sql }')

    # Instantiates the mechanism from vectorize_helpers.py by which the doc embeddings will be generated
    embedding_generator = CustomEmbeddings(user=user)
    logger.info(f'running vectorize_docs() ... embedding_generator is: { embedding_generator }')


    # Step 6: Iterate over each item in all_document_splits
    for document_split in all_document_splits:
        
        type= 'document' # Specified here b/c repeatedly used below
        date_accessed = str(timezone.now().date())

        # Vectorization steps----------------------------
        
        # If preprocessing is turned on, preprocess first, then generate vectors
        if preprocessing:

            # If auto-detect, load the model based on the key (e.g. the detected language)
            if auto_detect_preprocessing_model:
                preprocessing_model_loaded = spacy.load(preprocessing_model_key)
                logger.info(f'running vectorize_docs() ... '
                            f'auto_detect_preprocessing_model is active, '
                            f'preprocessing_model_loaded is: { preprocessing_model_loaded }')
                
            # If auto-detect is off, then just load the appropriate preprocessing model from the userprofile
            else:
                preprocessing_model_loaded = spacy.load(preprocessing_model)

            preprocessed_text = preprocess(nlp=preprocessing_model, text=document_split.page_content)
            embedding = embedding_generator.embed_documents([preprocessed_text])[0]
            logger.debug(f'running vectorize_docs() ... '
                         f'preprocessed_text is: { preprocessed_text } and '
                         f'embedding is: { embedding }')

        # If preprocessing is turned off, disregard preprocessing and proceed directly to vector generation
        else:
            # Note that embed_documents expects a list, so despire being inside the loop and thus are passing only one item, we use list notation
            embedding = embedding_generator.embed_documents([document_split.page_content])[0]
            logger.debug(f'running vectorize_docs() ... '
                         f'embedding is: { embedding }')

        
        
        # Vector metadata and ID steps----------------------------
        # Attaches the metadata to the vector
        metadata = {
            'source': document_split.metadata['source'], # Used 'source' above b/c it's returned by WebBasedLoader.  See: https://python.langchain.com/v0.2/docs/integrations/document_loaders/web_base/
            'text': document_split.metadata['text'],
            'page_number': document_split.metadata['page_number'], #  Uses the page number from the document split's metadata
            'date_accessed': date_accessed,
            'type': type,
            'user': user.id, # Updating because Pinecone cannot accept a full User object
            #'language': language, # Commented out because if NOT auto_detect_preprocessing_model, language is Null, which isn't allowed by Pinecone
        }

        # Combine the vector and metadata
        # Note: Below, we affix an id to each chunk that is a hashed version of the chunk's content. 
        # Therefore, if the chunk remains unchanged from one run to another, the new chunk's ID will be the same as the old chunk's ID.
        vector_id = create_vector_id(vector_content=document_split.page_content, user=user)

        vector = {
            'id': vector_id,  # Unique ID for each chunk
            'values': embedding,
            'metadata': metadata
        }

        # Append the newly-created vector to the list of all vectorized splits
        all_document_splits_vectorized.append(vector)
        vector_ids_created.append(vector_id) # Append id of newly-created vector for comparison against DB
        logger.debug(f'running vectorize_docs() ...'
                     f'all_document_splits_vectorized updated to: { all_document_splits_vectorized }'
                     f'vector_ids_created updated to: { vector_ids_created }')
    
        # SQL Update or Create Record using update_or_create
        vector_object_for_sql = Vector(
            vector_id=vector_id,
            source=document_split.metadata['source'],
            date_accessed=date_accessed,
            type=type,
            embedding=embedding,
            user=user,
            text=document_split.metadata['text'],
            language=language,
        )
        vectors_for_sql.append(vector_object_for_sql)
    
    # Step 9: Delete obsolite vectors from Pinecone
    # For the Docs being RAGed, pull the obsolite vector IDs from SQL and delete those vectors in Pinecone
    # The SQL query below returns vectors that (a) are for the Docs being RAGed and (b) have IDs that differ from those just created.
    sql_vectors_to_delete = Vector.objects.filter(source__in=files, user=user).values_list('vector_id', flat=True) # Returns a list of vector_ids that match the criteria above
    sql_vectors_to_delete = list(sql_vectors_to_delete)  # Convert queryset to list
    logger.debug(f'running vectorize_docs() ...'
                 f'sql_vectors_to_delete is: { sql_vectors_to_delete }'
                 )
    logger.info(f'running vectorize_docs() ...'
                 f'number of sql_vectors_to_delete: { len(sql_vectors_to_delete) }'
                 )

    # Delete from Pinecone the vectors pulled from SQL above
    if sql_vectors_to_delete:
        try:
            Vector.objects.filter(vector_id__in=sql_vectors_to_delete).delete()  # Delete matching vectors from the database
            logger.debug(f'running vectorize_docs() ... deleted {len(sql_vectors_to_delete)} vectors from SQL database.')
            
            # Delete all vectors in Pinecone that have IDs in sql_vectors_to_delete
            logger.info(f'running vectorize_docs() ...'
                        f'Deleted {len(sql_vectors_to_delete)} vectors'
                        f'from Pinecone index: { index }'
                        )
        except PineconeException as e:
            logger.error(f'running vectorize_docs() ...'
                         f'Error deleting vectors from Pinecone: {e}'
                         )
    else:
        logger.debug('running vectorize_docs() ... no vectors to delete from Pinecone.')


    # Once all document splits are processed, perform a bulk insert
    Vector.objects.bulk_create(vectors_for_sql)
    logger.debug(f'running vectorize_docs() ... inserted { len(vectors_for_sql)} into SQL DB')


    # Step 10: Upsert all the newly-created vectors to Pinecone
    # Note, upsert = update + insert, so if a vector with the same ID already exists in the database, it will be updated.
    namespace = str(user.id)
    index.upsert(vectors=all_document_splits_vectorized, namespace=namespace)
    logger.debug(
        f'running vectorize_docs() ... user: {user} stored '
        f'{ len(all_document_splits_vectorized) } document vectors in Pinecone index.'
        )
    
    