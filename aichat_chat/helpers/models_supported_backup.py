from django.utils.translation import gettext_lazy as _


__all__ = ['preprocessing_models_supported', 'retriever_models_supported', 'similarity_metric', 'tokenization_and_vectorization_models_supported']



preprocessing_models_supported = {
    'xx_ent_wiki_sm': {
        'model_name': 'spaCy xx_ent_wiki_sm'+' ('+_('Multilingual')+')',
        'link_description': 'https://spacy.io/models/xx',
        'link_download': 'https://github.com/explosion/spacy-models/releases/download/xx_ent_wiki_sm-3.8.0/xx_ent_wiki_sm-3.8.0-py3-none-any.whl',
        'human_language': _('Multilingual')+' (Multilingual)',
    },
    'xx_sent_ud_sm': {
        'model_name': 'spaCy xx_sent_ud_sm'+' ('+_('Multilingual')+')',
        'link_description': 'https://spacy.io/models/xx',
        'link_download': 'https://github.com/explosion/spacy-models/releases/download/xx_sent_ud_sm-3.8.0/xx_sent_ud_sm-3.8.0-py3-none-any.whl',
        'human_language': _('Multilingual')+' (Multilingual)',
    },    
    'en_core_web_sm': {
        'model_name': 'spaCy en_core_web_sm'+' ('+_('English')+')',
        'link_description': 'https://spacy.io/models/en',
        'link_download': 'https://github.com/explosion/spacy-models/releases/download/en_core_web_sm-3.8.0/en_core_web_sm-3.8.0-py3-none-any.whl',
        'human_language': _('English')+' (English)',
        'language_code': 'en',
    },
    'en_core_web_md': {
        'model_name': 'spaCy en_core_web_md'+' ('+_('English')+')',
        'link_description': 'https://spacy.io/models/en',
        'link_download': 'https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.8.0/en_core_web_md-3.8.0-py3-none-any.whl',
        'human_language': 'English',
        'language_code': 'en',
    },
    'en_core_web_lg': {
        'model_name': 'spaCy en_core_web_lg'+' ('+_('English')+')',
        'link_description': 'https://spacy.io/models/en',
        'link_download': 'https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.8.0/en_core_web_lg-3.8.0-py3-none-any.whl',
        'human_language': 'English',
        'language_code': 'en',
    },
    'ja_core_news_md': {
        'model_name': 'spaCy ja_core_news_md'+' ('+_('Japanese')+')',
        'link_description': 'https://spacy.io/models/ja',
        'link_download': 'https://github.com/explosion/spacy-models/releases/download/en_core_web_lg-3.8.0/en_core_web_md-3.8.0-py3-none-any.whl',
        'human_language': 'Japanese',
        'language_code': 'ja',
    },
    'ko_core_news_md': {
        'model_name': 'spaCy ko_core_news_md'+' ('+_('Korean')+')',
        'link_description': 'https://spacy.io/models/ko',
        'link_download': 'https://github.com/explosion/spacy-models/releases/download/ko_core_news_md-3.8.0/ko_core_news_md-3.8.0-py3-none-any.whl',
        'human_language': 'Korean',
        'language_code': 'ko',
    },
    'es_core_news_md': {
        'model_name': 'spaCy es_core_news_md'+' ('+_('Spanish')+')',
        'link_description': 'https://spacy.io/models/es',
        'link_download': 'https://github.com/explosion/spacy-models/releases/download/es_core_news_md-3.8.0/es_core_news_md-3.8.0-py3-none-any.whl',
        'human_language': 'Spanish',
        'language_code': 'es',
    },

}


similarity_metric = {
    'cosine':{
        'metric': 'cosine',
        'link': 'https://www.pinecone.io/learn/vector-similarity/',
        'short_description': 'This metric measures the cosine of the angle between two vectors. It is often used in text analysis and recommendation systems. Measures: Only the direction (not magnitude).',
    },
    'euclidean': {
        'metric': 'euclidean',
        'link': 'https://www.pinecone.io/learn/vector-similarity/',
        'short_description': 'This metric calculates the straight-line distance between two vectors in a multidimensional space. Measures: the magnitude and direction of the vectors',
    },
    'dotproduct': {
        'metric': 'dotproduct',
        'link': 'https://www.pinecone.io/learn/vector-similarity/',
        'short_description': 'This metric is calculated by multiplying corresponding elements of two vectors and summing the results. Measures: the magnitude and direction of the vectors',
    },
}




tokenization_and_vectorization_models_supported = {
    'bert-base-multilingual-cased':{
        'model_name': 'Multilingual BERT, Cased (Hugging Face)',
        'link': 'https://huggingface.co/docs/transformers/en/model_doc/bert',
        'loader_specialized': 'BertModel.from_pretrained',
        'vector_dimensions': '768',
        'tokenizer_specialized': 'BertTokenizer.from_pretrained',
        'similarity_metric': 'cosine',
    },
    'sentence-transformers/all-MiniLM-L6-v2': {
        'model_name': 'Sentence Transformers Mini (Hugging Face)',
        'link': 'https://huggingface.co/sentence-transformers',
        'loader_specialized': 'AutoTokenizer.from_pretrained',
        'vector_dimensions': '384',
        'tokenizer_specialized': 'AutoTokenizer.from_pretrained',
        'similarity_metric': 'cosine',
    },
    'allenai/longformer-base-4096': {
        'model_name': 'longformer-base-4096 (Hugging Face)',
        'link': 'https://huggingface.co/allenai/longformer-base-4096',
        'loader_specialized': 'AutoTokenizer.from_pretrained',
        'vector_dimensions': '768',
        'tokenizer_specialized': 'AutoTokenizer.from_pretrained',
        'similarity_metric': 'cosine',
    },
    'xlm-roberta-base': {
        'model_name': 'xlm-roberta-base (Hugging Face)',
        'link': 'https://huggingface.co/docs/transformers/en/model_doc/xlm-roberta',
        'loader_specialized': 'AutoTokenizer.from_pretrained',
        'vector_dimensions': '768',
        'tokenizer_specialized': 'AutoTokenizer.from_pretrained',
        'similarity_metric': 'cosine',
    },
    'gpt-4o-mini': {
        'model_name': 'gpt-4o-mini (OpenAI)',
        'link': 'https://platform.openai.com/docs/models/gpt-4o-mini',
        'loader_specialized': None,
        'vector_dimensions': '1536',
        'tokenizer_specialized': None,
        'similarity_metric': 'cosine',
    },
    'gpt-4o': {
        'model_name': 'gpt-4o (OpenAI)',
        'link': 'https://platform.openai.com/docs/models#gpt-4o',
        'loader_specialized': None,
        'vector_dimensions': '1536',
        'tokenizer_specialized': None,
        'similarity_metric': 'cosine',
    }


    

}

retriever_models_supported = {
    'gpt-4o-mini': {
        'model_name': 'gpt-4o-mini (OpenAI)',
        'model_provider': 'OpenAI',
        'link': 'https://platform.openai.com/docs/models/gpt-4o-mini',
    },    
    'gpt-4o': {
        'model_name': 'gpt-4o (OpenAI)',
        'model_provider': 'OpenAI',
        'link': 'https://platform.openai.com/docs/models#gpt-4o',
    },    
    'claude-3-5-sonnet-latest': {
        'model_name': 'Claude 3.5 Sonnet (Antropic)',
        'model_provider': 'Anthropic',
        'link': 'https://docs.anthropic.com/en/docs/about-claude/models#model-comparison-table',
    },
    'claude-3-haiku-20240307': {
        'model_name': 'Claude 3 Haiku (Antropic)',
        'model_provider': 'Anthropic',
        'link': 'https://docs.anthropic.com/en/docs/about-claude/models#model-comparison-table',
    },
}


