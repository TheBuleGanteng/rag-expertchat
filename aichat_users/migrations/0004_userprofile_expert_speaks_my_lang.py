# Generated by Django 5.1 on 2024-08-20 08:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aichat_users', '0003_favorites_added'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='expert_speaks_my_lang',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]
