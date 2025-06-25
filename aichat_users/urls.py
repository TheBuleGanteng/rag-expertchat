from django.urls import path

from . import views
from .aichat_admin import aichat_admin_site

app_name = 'aichat_users'  # Namespace for the users app

urlpatterns = [
    #Admin
    path('admin/', aichat_admin_site.urls),  # Admin site for aichat_chat and aichat_users
    # End points
    path('check_email_registered/', views.check_email_registered, name='check_email_registered'),
    path('check_password_strength/', views.check_password_strength, name='check_password_strength'),
    path('check_password_valid/', views.check_password_valid, name='check_password_valid'),
    path('check_username_registered/', views.check_username_registered, name='check_username_registered'),
    path('update_favorites/', views.update_favorites, name='update_favorites'),
    # Views
    path('favorites/', views.favorites_view, name='favorites'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('password_change/', views.password_change_view, name='password_change'),
    path('password-reset/', views.password_reset_view, name='password_reset'),
    path('password-reset-confirmation/', views.password_reset_confirmation_view, name='password_reset_confirmation'),
    path('register/', views.register_view, name='register'),
    path('register_confirmation/', views.register_confirmation_view, name='register_confirmation'),

]