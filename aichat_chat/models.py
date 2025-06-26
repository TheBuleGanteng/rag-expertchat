from django.conf import settings
from django.db import models
from django.utils import timezone

# Create your models here.
class ChatHistory(models.Model):
    session_id = models.TextField()
    message = models.TextField()
    timestamp = models.DateTimeField(default=timezone.now)
    id = models.AutoField(primary_key=True)

    def __str__(self):
        return f'{self.session_id} {self.message}'

    class Meta:
        db_table = 'ChatHistory'
        verbose_name = 'Chat History'
        verbose_name_plural = 'Chat Histories'


class Expert(models.Model):
    name_first = models.CharField(max_length=30, verbose_name='First Name')
    name_last = models.CharField(max_length=30, verbose_name='Last Name')
    photo = models.URLField(max_length=200, verbose_name='Photo URL')

    def __str__(self):
        return f'{self.name_first} {self.name_last}'

    class Meta:
        db_table = 'Experts'
        verbose_name = 'Expert'
        verbose_name_plural = 'Experts'


class Experience(models.Model):
    expert = models.ForeignKey(Expert, on_delete=models.CASCADE, related_name='experiences')
    employer = models.CharField(max_length=100, verbose_name='Employer')
    industry = models.CharField(max_length=100, verbose_name='Industry')
    function = models.CharField(max_length=100, verbose_name='Function')
    role = models.CharField(max_length=100, verbose_name='Role')
    years = models.DecimalField(max_digits=4, decimal_places=1, verbose_name='Years')
    geography = models.ForeignKey('Geography', on_delete=models.CASCADE, related_name='experiences', null=True, blank=True)

    def __str__(self):
        return f'{self.expert.name_first} {self.expert.name_last} - {self.employer} - {self.role} ({self.years} years)'

    class Meta:
        db_table = 'Experience'
        verbose_name = 'Experience'
        verbose_name_plural = 'Experiences'


class Language(models.Model):
    code = models.CharField(max_length=10, verbose_name='Language Code')
    name = models.CharField(max_length=50, verbose_name='Language Name')
    translated_name = models.CharField(max_length=50, verbose_name='Language Name', blank=True, null=True)

    class Meta:
        db_table = 'aichat_language'
    
    def __str__(self):
        return self.name


class ExpertLanguage(models.Model):
    expert = models.ForeignKey(Expert, on_delete=models.CASCADE, related_name='languages')
    language = models.ForeignKey(Language, on_delete=models.CASCADE, related_name='experts')

    class Meta:
        unique_together = ('expert', 'language')  # Prevents duplicate entries
        db_table = 'aichat_expert_language'

    def __str__(self):
        return f'{self.expert.name_first} {self.expert.name_last} speaks {self.language.name}'


class Topic(models.Model):
    expert = models.ForeignKey(Expert, on_delete=models.CASCADE, related_name='topics')
    topic = models.CharField(max_length=500, verbose_name='Topic')

    def __str__(self):
        return f'{self.expert.name_first} {self.expert.name_last} - {self.topic}'

    class Meta:
        db_table = 'Topics'
        verbose_name = 'Topic'
        verbose_name_plural = 'Topics'


class Geography(models.Model):
    country = models.CharField(max_length=100, verbose_name='Country')
    country_code = models.CharField(max_length=20, verbose_name='Country_Short')
    region = models.CharField(max_length=100, verbose_name='Region')
    region_code = models.CharField(max_length=20, verbose_name='Region_Short')

    def __str__(self):
        return f'{self.country} - {self.region}'

    class Meta:
        db_table = 'Geography'
        verbose_name = 'Geography'
        verbose_name_plural = 'Geographies'


class Vector(models.Model):
    vector_id = models.CharField(max_length= 200, null=True, blank=True, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='aichat_vectors')
    source = models.URLField(null=True, blank=True)
    top_level_domain = models.CharField(max_length=100, null=True, blank=True)
    date_accessed = models.DateField(null=True, blank=True)
    VECTOR_TYPE_CHOICES = [
        ("website", "website"),
        ("document", "document"),
        ("image", "image")
    ]
    type= models.CharField(max_length=100, choices=VECTOR_TYPE_CHOICES, null=True, blank=True)
    embedding= models.TextField(null=True, blank=True)
    language=models.CharField(max_length=100, null=True, blank=True, default='en')
    text=models.TextField(null=True, blank=True)

    def __str__(self):
        return f'vector_id: {self.vector_id} - top_level_domain: {self.top_level_domain}'

    class Meta:
        db_table = 'aichat_vector'
        verbose_name = 'Vector'
        verbose_name_plural = 'Vectors'


class RagSource(models.Model):
    VECTOR_TYPE_CHOICES = [
        ('website', 'website'),
        ('document', 'document'),
        ('image', 'image')
    ]
    source = models.CharField(max_length=500, null=True, blank=True) # Note: unique= True doesn't make sense here b/c two diff. users could RAG the same URL
    file_path = models.FileField(upload_to='uploads/', null=True, blank=True)  # New field for document uploads
    file_size = models.FloatField(null=True, blank=True) # File size for docs
    type= models.CharField(max_length=100, choices=VECTOR_TYPE_CHOICES, null=True, blank=True)
    include_subdomains = models.BooleanField(default=False, null=True, blank=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='aichat_ragsources', blank=True, null=True)
    
    
    def __str__(self):
        return f'source: {self.source} - type: {self.type} - user: {self.user}'

    class Meta:
        db_table = 'aichat_ragsource'
        verbose_name = 'RagSource'
        verbose_name_plural = 'RagSources'
        """
        unique_together = [
            ('source', 'user'),
            ('document', 'user')
        ]  # Prevents duplicate URL entries for the same user
        """
