# Generated by Django 5.1.1 on 2025-01-22 20:44

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0047_remove_subject_course_alter_subject_niveau'),
    ]

    operations = [
        migrations.AddField(
            model_name='subject',
            name='volume_horaire_total',
            field=models.IntegerField(default=40),
        ),
    ]
