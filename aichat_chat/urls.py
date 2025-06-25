from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path
from . import views


app_name = 'aichat_chat'  # Namespace for the app

urlpatterns = [
    # End points
    # Views
    path('', lambda request: redirect('index/', permanent=False)),  # Temporary redirect to /index/
    path('index/', views.index_view, name='index'),

    # API Routes
    path('delete_rag_sources/', views.delete_rag_sources, name = 'delete_rag_sources'),
    path('generate_embeddings/', views.generate_embeddings, name='generate_embeddings'),
    path('rag_docs/', views.rag_docs, name='rag_docs'),
    path('rag_url/', views.rag_url, name='rag_url'),
    path('retrieve-chat-history/', views.retrieve_chat_history, name='retrieve_chat_history'),
    path('stream_response/', views.stream_response, name='stream_response'),
    path('update_profile/', views.update_profile, name='update_profile'),
    path('model_data/', views.retrieve_model_details, name='retrieve_model_details'),

    
]