# Generated by Django 3.1.1 on 2025-01-18 14:40

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0020_merge_20250118_1531'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='attendance',
            name='time_from',
        ),
        migrations.RemoveField(
            model_name='attendance',
            name='time_to',
        ),
        migrations.RemoveField(
            model_name='student',
            name='gender',
        ),
        migrations.AddField(
            model_name='student',
            name='dateN',
            field=models.DateField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='student',
            name='lieu',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='student',
            name='session',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='main_app.session'),
        ),
    ]
