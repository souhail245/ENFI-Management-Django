# Generated by Django 3.1.1 on 2025-01-14 13:21

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0005_auto_20250113_2314'),
    ]

    operations = [
        migrations.AddField(
            model_name='student',
            name='address',
            field=models.TextField(default='No address provided'),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='student',
            name='profile_pic',
            field=models.ImageField(default='No address provided', upload_to='profile_pics/'),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='student',
            name='course',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='main_app.course'),
        ),
        migrations.AlterField(
            model_name='student',
            name='matricule',
            field=models.CharField(max_length=20),
        ),
        migrations.AlterField(
            model_name='student',
            name='phone_number',
            field=models.CharField(max_length=15),
        ),
        migrations.AlterField(
            model_name='student',
            name='session',
            field=models.CharField(max_length=50),
        ),
    ]
