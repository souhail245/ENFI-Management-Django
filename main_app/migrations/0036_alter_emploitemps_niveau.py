# Generated by Django 5.1.1 on 2025-01-21 18:27

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0035_remove_emploitemps_end_time_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='emploitemps',
            name='niveau',
            field=models.CharField(choices=[('3eme année', '3ème année'), ('4eme année', '4ème année'), ('5eme année', '5ème année'), ('6eme année', '6ème année')], default='3eme année', max_length=20),
        ),
    ]
