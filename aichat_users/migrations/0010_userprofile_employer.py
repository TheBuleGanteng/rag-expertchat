# Generated by Django 5.1 on 2024-09-10 08:17

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('aichat_users', '0009_alter_userprofile_user'),
    ]

    operations = [
        migrations.AddField(
            model_name='userprofile',
            name='employer',
            field=models.CharField(blank=True, default='Kebayoran Technologies', max_length=100, null=True),
        ),
    ]
