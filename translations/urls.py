from django.contrib import admin
from django.shortcuts import redirect
from django.urls import include, path
from . import views

app_name = 'translations'  # Namespace for the app

urlpatterns = [
    # End points
    path("translate-text/", views.translate_text, name="translate_text"),
    path("set-session-language/", views.set_session_language, name="set_session_language"),
]