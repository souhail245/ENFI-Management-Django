# Generated by Django 3.1.1 on 2025-01-20 11:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0027_auto_20250120_0155'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notificationstudent',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to='ENFI-Management-Django\\media'),
        ),
    ]
