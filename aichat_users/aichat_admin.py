from django.contrib.admin import AdminSite
from aichat_chat.models import ChatHistory, Expert, Experience, Topic, Geography
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib import admin

# Get the User model
User = get_user_model()

class AiChatAdminSite(AdminSite):
    site_header = 'AiChat Admin'
    site_title = 'AiChat Admin Portal'
    index_title = 'Welcome to the AiChat Admin Portal'

aichat_admin_site = AiChatAdminSite(name='aichat_admin')

# Custom UserAdmin to manage users in the admin panel
class AichatUserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)
    filter_horizontal = ('groups', 'user_permissions',)

# Register your models here
aichat_admin_site.register(ChatHistory)
aichat_admin_site.register(Expert)
aichat_admin_site.register(Experience)
aichat_admin_site.register(Topic)
aichat_admin_site.register(Geography)
aichat_admin_site.register(User, AichatUserAdmin)
