# Generated by Django 5.1.1 on 2025-01-21 21:20

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0039_remove_emploitemps_jour_emploitemps_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='emploitemps',
            name='jour',
            field=models.CharField(choices=[('Lundi', 'Lundi'), ('Mardi', 'Mardi'), ('Mercredi', 'Mercredi'), ('Jeudi', 'Jeudi'), ('Vendredi', 'Vendredi'), ('Samedi', 'Samedi')], default='Lundi', max_length=10),
        ),
    ]
