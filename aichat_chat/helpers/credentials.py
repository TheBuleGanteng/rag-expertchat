import os
from dotenv import load_dotenv

# Define the path to the .env file
dotenv_path = os.path.join(os.path.dirname(__file__), '.env')

# Load environment variables from the .env file
load_dotenv(dotenv_path)


__all__ = ['PINECONE_API_KEY', 'OPENAI_API_KEY']

PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")