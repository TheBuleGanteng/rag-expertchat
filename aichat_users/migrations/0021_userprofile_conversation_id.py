# Generated by Django 5.1 on 2024-11-26 09:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aichat_users', '0020_userprofile_preprocessing_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='conversation_id',
            field=models.CharField(blank=True, max_length=200, null=True),
        ),
    ]
