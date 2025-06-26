from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from aichat_chat.models import Expert
from django.utils.timezone import now
from decimal import Decimal

class UserProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='aichat_userprofile')
    user_employer = models.CharField(max_length=100, null=True, blank=True, default='Kebayoran Technologies')
    data_source = models.CharField(max_length=64, null=True, blank=True, default='hist_rag')
    suggest_experts = models.BooleanField(null=True, blank=True, default=True)
    experts_suggested_number = models.IntegerField(null=True, blank=True, default=3, validators=[MinValueValidator(0), MaxValueValidator(10)])
    expert_speaks_my_lang = models.BooleanField(null=True, blank=True, default=False)
    weight_years = models.IntegerField(null=True, blank=True, default=5, validators=[MinValueValidator(0), MaxValueValidator(10)])
    weight_industry = models.IntegerField(null=True, blank=True, default=5, validators=[MinValueValidator(0), MaxValueValidator(10)])
    weight_role = models.IntegerField(null=True, blank=True, default=5, validators=[MinValueValidator(0), MaxValueValidator(10)])
    weight_topic = models.IntegerField(null=True, blank=True, default=5, validators=[MinValueValidator(0), MaxValueValidator(10)])
    weight_geography = models.IntegerField(null=True, blank=True, default=5, validators=[MinValueValidator(0), MaxValueValidator(10)])
    response_length = models.IntegerField(null=True, blank=True, default=4, validators=[MinValueValidator(1), MaxValueValidator(200)])
    chat_history_window = models.IntegerField(null=True, blank=True, default=5, validators=[MinValueValidator(0), MaxValueValidator(200)])
    temperature = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, default=Decimal('0.30'), validators=[MinValueValidator(0.00), MaxValueValidator(1.00)])
    top_p = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True, default=Decimal('1.0'), validators=[MinValueValidator(0.00), MaxValueValidator(1.00)])
    chunk_size = models.IntegerField(default=1000, validators=[MinValueValidator(100), MaxValueValidator(30000)], null=True, blank=True)
    chunk_overlap = models.DecimalField(max_digits=2, decimal_places=2, default=Decimal('0.30'), validators=[MinValueValidator(Decimal('0.00')), MaxValueValidator(Decimal('0.75'))], null=True, blank=True)
    langchain_k = models.IntegerField(null=True, blank=True, default=5, validators=[MinValueValidator(0), MaxValueValidator(20)])
    preferred_language = models.CharField(max_length=6, null=True, default='en', blank=True)
    rag_sources_shown = models.CharField(max_length=100, null=True, blank=True, default='all') # Can be 'website', 'document' or 'all'
    rag_sources_used = models.CharField(max_length=100, null=True, blank=True, default='all') # Can be 'website', 'document' or 'all'
    tokenization_and_vectorization_model = models.CharField(max_length=100, null=True, blank=True, default='gpt-4o')
    preprocessing_model = models.CharField(max_length=100, null=True, blank=True, default='en_core_web_sm')
    similarity_metric = models.CharField(max_length=100, null=True, blank=True, default='cosine')
    retriever_model = models.CharField(max_length=100, null=True, blank=True, default='gpt-4o-mini')
    preprocessing = models.BooleanField(null=True, blank=True, default=False)
    conversation_id = models.CharField(null=True, blank=True, max_length=200)


    class Meta:
        db_table = 'aichat_userprofile'  # Rename the table here

    def __str__(self):
        return f"{self.user.username}'s Profile"
    

class Favorites(models.Model):

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='aichat_favorite')
    expert = models.ForeignKey(Expert, on_delete=models.CASCADE, related_name='added_as_favorite_by')
    added = models.DateField(default=now, null=True, blank=True)

    class Meta:
        db_table = 'aichat_favorites'  # Rename the table here

    def __str__(self):
        return f"{self.user.username} (id {self.user.id}) likes {self.expert.name_first} {self.expert.name_last} (id {self.expert.pk})"