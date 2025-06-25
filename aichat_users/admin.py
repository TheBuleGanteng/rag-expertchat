from django.contrib import admin
from .models import UserProfile

# Register the UserProfile model if it's not already registered
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    pass
