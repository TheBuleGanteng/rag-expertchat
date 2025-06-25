from django.contrib import admin
from .models import ChatHistory, Experience, Expert, Topic, Geography, Language, ExpertLanguage

# Register ChatHistory model
@admin.register(ChatHistory)
class ChatHistoryAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'message', 'timestamp')
    search_fields = ('session_id', 'message')
    list_filter = ('timestamp',)


# Define an inline admin descriptor for Experience model
class ExperienceInline(admin.StackedInline):
    model = Experience
    can_delete = True
    verbose_name_plural = 'experiences'


# Define an inline admin descriptor for Topic model
class TopicInline(admin.StackedInline):
    model = Topic
    can_delete = True
    verbose_name_plural = 'topics'


# Define an inline admin descriptor for ExpertLanguage model
class ExpertLanguageInline(admin.TabularInline):
    model = ExpertLanguage
    extra = 1  # Specifies how many empty forms to display
    verbose_name_plural = 'languages'


# Register Expert model with inline
@admin.register(Expert)
class ExpertAdmin(admin.ModelAdmin):
    list_display = ('name_first', 'name_last', 'photo')
    search_fields = ('name_first', 'name_last')
    inlines = [ExperienceInline, TopicInline, ExpertLanguageInline]  # Include the new ExpertLanguageInline


# Register Experience model
@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ('expert', 'employer', 'function', 'role', 'years', 'geography')
    search_fields = ('expert__name_first', 'expert__name_last', 'function', 'employer', 'role', 'geography__country')
    list_filter = ('expert', 'employer', 'function', 'role', 'years', 'geography')


# Register Topic model
@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('expert', 'topic')
    search_fields = ('expert__name_first', 'expert__name_last', 'topic')
    list_filter = ('expert', 'topic')


# Register Geography model
@admin.register(Geography)
class GeographyAdmin(admin.ModelAdmin):
    list_display = ('country', 'country_code', 'region', 'region_code')
    search_fields = ('country', 'country_code', 'region', 'region_code')
    list_filter = ('country', 'region')


# Register Language model
@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    list_display = ('code', 'name')
    search_fields = ('code', 'name')
