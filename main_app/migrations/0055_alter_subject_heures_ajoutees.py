# Generated by Django 5.1.1 on 2025-01-23 18:52

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0054_subject_volume_horaire_restant'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subject',
            name='heures_ajoutees',
            field=models.IntegerField(blank=True, default=0, null=True),
        ),
    ]
