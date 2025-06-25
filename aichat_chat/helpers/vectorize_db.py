from dotenv import find_dotenv, load_dotenv
import logging
from django.conf import settings
import os
from pinecone import Pinecone, ServerlessSpec
import sqlite3
import spacy
import sys
import time
from transformers import AutoTokenizer, AutoModel


logger = logging.getLogger('django')
# Load environment variables from .env file
load_dotenv()


# Find the .env file and load environment variables
# Determine the path to the .env file relative to this script
current_dir = os.path.dirname(os.path.abspath(__file__))
env_path = os.path.join(current_dir, '../../gitignored/.env')

# Load the .env file
load_dotenv(env_path)

# Log the path of the .env file being used
if env_path:
    logger.debug(f"Using .env file located at: {env_path}")
else:
    logger.warning("No .env file found. Please ensure it is correctly located.")



# Set the settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'homepage.settings')


PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
logger.info(f'PINECONE_API_KEY is: { PINECONE_API_KEY }')



# Ensure the project root is in the system path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Use absolute import for credentials
#from .credentials import PINECONE_API_KEY, OPENAI_API_KEY


# Initialize Pinecone
if not PINECONE_API_KEY:
    logger.error("Pinecone API key is not set. Please set the PINECONE_API_KEY environment variable.")
    raise ValueError("Pinecone API key is not set.")

pc = Pinecone(api_key=PINECONE_API_KEY)



# Understanding how a Pinecone database works, using a SQLite database as an analog:
# 1. You have a single Pinecone 'index' (akin to a SQLite database)
# 2. Within a Pinecone 'index', you can have multiple vector representations, each representing a single, embedding (e.g. a set of coordinates in high-dimension space). Each vector representation is analgous to SQLite rows.
# 3. Pinecone doesn't use 'tables' to categorize data like SQLite does, but instead attaches metadata (in the format of key:value pairs) to each vector representatation that the user can use to categorize data in the 'Index'.


# Define a function to delete all existing vector DBs
def delete_all_resources():
    # List all indexes
    indexes = pc.list_indexes()

    # Delete each index by its name
    for index in indexes:
        index_name = index['name']  # Extract the name of the index
        logger.debug(f'running aichat_chat/helpers/vectorize_db.py ... deleting index: {index_name}')
        pc.delete_index(index_name)
        logger.debug(f'running aichat_chat/helpers/vectorize_db.py ... index_name: {index_name} deleted successfully')



# The function below cleans and normalizes the text passed in, given the nlp model passed in
def preprocess(text, nlp):
    doc = nlp(text.lower())
    # This line performs two main tasks:
    # (a) Lemmatization: Converts each token (word) to its base or root form (lemma)
    # (b) Stop Word Removal: Excludes common stop words (like "the", "is", "in") that do not contribute much meaning and are often filtered out in NLP tasks
    # More about each component:
    # (a) 'for token in doc' Iterates over each token (word) in the Doc object (doc).
    # (b) 'token.lemma_' Accesses the lemma (base form) of each token. For example, the lemma of "running" would be "run".
    # (c) 'if not token.is_stop' Checks if the token is a stop word. token.is_stop returns True if the token is a stop word, so not token.is_stop filters out these words
    # "' '.join(...)" Joins all the lemmatized tokens that are not stop words into a single string with spaces between them.
    return ' '.join([token.lemma_ for token in doc if not token.is_stop])


def vectorize(text, tokenizer, model):
    
    # The tokenizer arguments explained:
    # (a) text = the text to be tokenized
    # (b) return_tensors='pt' This tells the tokenizer to return the tokenized output in the form of PyTorch tensors. This is necessary because transformer models in Hugging Face are typically trained using PyTorch or TensorFlow, and they expect inputs in this format.
    # (c) truncation=True If the input text is longer than the maximum length allowed by the model, this parameter will truncate the text to fit.
    # (d) padding= True Ensures that all input sequences are of the same length by padding shorter sequences with zeros. This is needed because transformer models require inputs of uniform length
    inputs = tokenizer(
        text, 
        return_tensors="pt", 
        truncation=True, 
        padding=True,
        #clean_up_tokenization_spaces=False,
        )
    
    # Passes the tokenized inputs to the model for processing. The **inputs syntax unpacks the dictionary inputs (which contains input IDs, attention masks, etc.) and passes them as arguments to the model.
    outputs = model(**inputs)
    
    # The output elements explained:
    # (a) outputs.last_hidden_state: The last_hidden_state is a tensor containing the hidden states (embeddings) of the last layer of the transformer model for each token in the input text. The hidden state for each token is a vector that captures its context and meaning in the sentence.
    # (b) mean(dim=1): Takes the mean (average) of the hidden states across the token dimension (dim=1)
    # (c) detach(): Detaches the tensor from the current computation graph. This is important to prevent the computation of gradients, which is unnecessary for inference.
    # (d) numpy(): Converts the PyTorch tensor to a NumPy array, which is a more familiar format for numerical data manipulation in Python.
    # (e) flatten(): Flattens the array into a 1D format to ensure the vector is a simple list of numbers.
    # (f) tolist(): Converts the NumPy array to a regular Python list.
    # In summary, the function below takes input (an experience or topic as used below and creates a single embedding that averages the embeddings assocaited with each token in a given experience, giving a "summary" of that topic or experience.)
    
    # Important note: The approach below generates a summary vector by taking an average of all the embeddings in the final layer
    return outputs.last_hidden_state.mean(dim=1).detach().numpy().flatten().tolist()  # Ensure the output is a list of floats

    # Alternative approach: Extract the summary CLS embedding after the final layer is completed
    # Extract the [CLS] token's embedding
    #cls_embedding = outputs.last_hidden_state[:, 0, :].detach().numpy().flatten().tolist()
    #return cls_embedding




def main():
    # Step 1: Extract data from SQLite3
    logger.debug(f'running aichat_chat/helpers/vectorize_db.py ... starting step 1: Extract data from SQLite3')
    
    # 'conn' represents a connection to the SQLite DB (homepagedb in this case) that allows the function to communicate with the DB
    conn = sqlite3.connect(os.path.join(settings.BASE_DIR, 'homepagedb.sqlite3'))
    
    # 'cursor' represents an 'agent' that can execute DB commands (such as the one below) on the DB connected via 'conn'
    cursor = conn.cursor()
    cursor.execute("SELECT id, name_first, name_last FROM Experts")
    experts = cursor.fetchall()

    # The segment below pulls all the experiences and the associated geography for each experience
    # The use of 'e....' terminology below refers to the use of database aliases.
    # Below, 'e.' is sorthand for 'Experience.', so 'e.expert_id' is an abbreviated version of 'Experience.expert_id'
    # Triple quotes are used to allow the string that forms the query to be broken into multiple lines
    cursor.execute("""
        SELECT e.expert_id, e.employer, e.industry, e.function, e.role, g.country, g.region
        FROM Experience e
        LEFT JOIN Geography g ON e.geography_id = g.id
    """)
    experiences = cursor.fetchall()

    # The segment below pulls all the topics
    cursor.execute("SELECT expert_id, topic FROM Topics")
    topics = cursor.fetchall()

    conn.close()


    # Step 2: Preprocess the Data using spaCy
    # spaCy is a NLP library that splits text into tokens and vectorizes those tokens
    # the model being loaded is en_core_web_sm, a small model trained on English. See https://spacy.io/models
    logger.debug(f'running aichat_chat/helpers/vectorize_db.py ... starting step 2: Preprocess the Data using spaCy')
    nlp = spacy.load('en_core_web_sm')


    # Step : Preprocess each Experience and Topic record.

    # For each Experience, this remove stop words, lemmatizes, and joins the result as a string.
    # See function definition above) and the nlp model loaded above
    preprocessed_experiences = [
        (exp[0], preprocess(exp[1] + ' ' + exp[2] + ' ' + exp[3] + ' ' + exp[4] + ' ' + (exp[5] or '') + ' ' + (exp[6] or ''), nlp)) 
        for exp in experiences
    ]
    logger.debug(f'running vectorize_db.py ... generated preprocessed_experiences')


    # This preprocesses each Toic, repeating the same process done above for experiences
    preprocessed_topics = [(topic[0], preprocess(topic[1], nlp)) for topic in topics]
    logger.debug(f'running vectorize_db.py ... generated preprocessed_topics')


    # Step 3: Vectorize the data using a transformer model from Hugging Face
    # See the following link for more info about Hugging Face models: https://huggingface.co/sentence-transformers
    logger.debug(f'running vectorize_db.py ... starting step 3: Vectorize the data using a transformer model from Hugging Face')
    
    # A tokenizer is a tool that converts raw text into a format suitable for input into the model.
    # It breaks down the text into smaller pieces called tokens. Tokens could be words, subwords, or even characters, depending on the tokenizer's design and assigns IDs to those tokens.
    tokenizer = AutoTokenizer.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")
    
    # The model processes the tokens generated by tokenizer (e.g. the numerical representations of words) and converts them to high-dimension embeddings by vectorizing those tokens.
    model = AutoModel.from_pretrained("sentence-transformers/all-MiniLM-L6-v2")

    # This creates vectors that represent a summary of each experience and topic object.
    # For each experience, it calls the vectorize function, passing:
    # (a) exp[1]: The preprocessed text of an experience.
    # (b) tokenizer and model: The tokenizer and model loaded earlier.
    # The vectorize function returns a single high-dimensional vector (embedding) that represents the semantic meaning of the experience text.
    # The result is a list of tuples: each tuple contains an identifier (exp[0]) and its corresponding vector representation.
    vectorized_experiences = [(exp[0], vectorize(exp[1], tokenizer, model)) for exp in preprocessed_experiences]
    vectorized_topics = [(topic[0], vectorize(topic[1], tokenizer, model)) for topic in preprocessed_topics]

    
    # Step 4: Store Vectors in a Pinecone Vector Database
    logger.debug(f'running aichat_chat/helpers/vectorize_db.py ... starting step 4: Store Vectors in a Pinecone Vector Database')

    # Delete all existing resources
    delete_all_resources()

    # Add a brief delay to ensure the index is deleted
    time.sleep(10)


    # Step : Create a new index (analgous to a SQLite DB) that will store the vector representations (vectorized_experiences and vectorized_tpics) already created and currently stored in memory
    
    # First, check that the 'experts' table doesn't already exist in the pinecone environment
    index_name = 'experts'
    if index_name in [index['name'] for index in pc.list_indexes()]:
        raise Exception(f'running aichat_chat/helpers/vectorize_db.py ... failed to delete existing index: {index_name}')

    # Then, if the 'experts' index doesn't already exist in the Pinecone environment, then create it
    logger.debug(f'running aichat_chat/helpers/vectorize_db.py ... creating new index with index_name: {index_name}')
    pc.create_index(
        name=index_name,
        dimension=384,  # Ensure this matches your model output dimensions
        metric='cosine', # Options include 'cosine', 'euclidean', 'dotproduct'. The metric should ideally match the type of distance or similarity your model was designed to produce. More information here: https://www.pinecone.io/learn/vector-similarity/
        spec=ServerlessSpec( # Configs for Pinecone's offering that handles server for the user. More info here: https://docs.pinecone.io/guides/indexes/create-an-index#create-a-serverless-index
            cloud='aws',
            region='us-east-1'
        )
    )

    # Connect to the newly-created index
    index = pc.Index(index_name)

    # Prepare data for insertion
    vectors = []

    # For each vectorized_experiences vector representation, this appends a dictionary to the vectors[] list containing the following:
    # (a) A unique identifier for the vector, in the experience_1, experience_2 format
    # (b) The numberical represenation of the experience (the embeddings)
    # (c) Some metadata to aid in subseqient retrieval, in the form of type of vector ('type') and the expert's id('expert_id') 
    for exp in vectorized_experiences:
        vectors.append({
            'id': f'experience_{exp[0]}',
            'values': exp[1],
            'metadata': {'type': 'experience', 'expert_id': exp[0]}
        })

    for topic in vectorized_topics:
        vectors.append({
            'id': f'topic_{topic[0]}',
            'values': topic[1],
            'metadata': {'type': 'topic', 'expert_id': topic[0]}
        })

    # Insert vectors into the index
    index.upsert(vectors)
    logger.info(f'running rectorize_db.py ... upserted new expert vectors to DB')

if __name__ == "__main__":
    main()
