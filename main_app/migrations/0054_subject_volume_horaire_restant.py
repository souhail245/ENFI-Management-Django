# Generated by Django 5.1.1 on 2025-01-23 18:48

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0053_remove_subject_volume_horaire_restant_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='subject',
            name='volume_horaire_restant',
            field=models.IntegerField(blank=True, null=True),
        ),
    ]
