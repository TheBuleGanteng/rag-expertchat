from django.conf import settings
import logging
import torch
from transformers import AutoModel, AutoTokenizer

logger = logging.getLogger('django')

__all__ = ['generate_embeddings_open_source', 'OpenSourceEmbeddings', 'preprocess' ]




class OpenSourceEmbeddings:
    def __init__(self, tokenization_and_vectorization_model):
        self.huggingface_model = AutoModel.from_pretrained(tokenization_and_vectorization_model)
        self.tokenizer = AutoTokenizer.from_pretrained(tokenization_and_vectorization_model)
        self.max_length = min(
            self.tokenizer.model_max_length,
            settings.TOKENIZER_MAX_LENGTH_FIXED
        )
        logger.debug(f'OpenSourceEmbeddings initialized with max_length: {self.max_length}')


    def generate_embedding(self, text):
        """Generate embeddings for a single piece of text"""
        inputs = self.tokenizer(
            text,
            padding=True,
            truncation=True,
            return_tensors="pt",
            max_length=self.max_length
        )
        
        # Get model outputs
        outputs = self.huggingface_model(**inputs)
        
        # Use mean pooling of the last hidden state as the embedding
        embeddings = outputs.last_hidden_state.mean(dim=1)
        
        # Convert to list and return the first (and only) embedding
        return embeddings[0].detach().numpy().tolist()

    def embed_documents(self, sources):
        """Generate embeddings for multiple documents"""
        logger.debug(f'running OpenSourceEmbeddings.embed_documents ... embedding sources: {sources}')
        return [self.generate_embedding(text) for text in sources]

    def embed_query(self, query):
        """Generate embedding for a single query"""
        logger.debug(f'running OpenSourceEmbeddings.embed_query ... embedding query: {query}')
        return self.generate_embedding(query)

    def __call__(self, query):
        """Make the object callable"""
        return self.embed_query(query)


# Function 12: Preprocess data
def preprocess(nlp, text):
    logger.debug(f'running preprocesses() ... function started, '
                 f'nlp is: { nlp }, text is: { text }'
                 )
    
    # Convert the text to lowercase
    text = text.lower()
    
    # Apply SpaCy NLP processing
    doc = nlp(text)
    return ' '.join([token.lemma_ for token in doc if not token.is_stop])




# Function: Generate embeddings using a open source model    
def generate_embeddings_open_source(tokenization_and_vectorization_model, text_list, is_single=False):
    similarity_tokenizer = AutoTokenizer.from_pretrained(tokenization_and_vectorization_model)
    tokenizer_max_length = similarity_tokenizer.model_max_length
    max_length_set = min(tokenizer_max_length, settings.TOKENIZER_MAX_LENGTH_FIXED)

    inputs = similarity_tokenizer(
        text_list,
        padding=True,
        truncation=True,
        max_length=max_length_set,
        return_tensors='pt'
    )
    
    with torch.no_grad():
        similarity_model = AutoModel.from_pretrained(tokenization_and_vectorization_model)
        outputs = similarity_model(**inputs)
        
        # Check if attentions are available
        if hasattr(outputs, 'attentions') and outputs.attentions is not None:
            attention_weights = torch.mean(outputs.attentions[-1], dim=1)  # Use last layer
            hidden_states = outputs.last_hidden_state
            weighted_states = hidden_states * attention_weights.unsqueeze(-1)
            embeddings = torch.mean(weighted_states, dim=1)
        else:
            # Fallback: Use pooler_output if available, or average last hidden state
            if hasattr(outputs, 'pooler_output') and outputs.pooler_output is not None:
                embeddings = outputs.pooler_output
            else:
                embeddings = outputs.last_hidden_state.mean(dim=1)
    
    return embeddings