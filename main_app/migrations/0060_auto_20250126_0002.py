# Generated by Django 3.1.1 on 2025-01-25 23:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0059_auto_20250125_0237'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attendancereport',
            name='updated_at',
            field=models.DateTimeField(auto_now_add=True),
        ),
        migrations.AlterField(
            model_name='emploitemps',
            name='horaire',
            field=models.CharField(choices=[('08:00-09:00', '08:00-09:00'), ('09:00-10:00', '09:00-10:00'), ('10:00-11:00', '10:00-11:00'), ('11:00-12:00', '11:00-12:00'), ('12:00-13:00', '12:00-13:00'), ('13:00-14:00', '13:00-14:00'), ('14:00-15:00', '14:00-15:00'), ('15:00-16:00', '15:00-16:00'), ('16:00-17:00', '16:00-17:00'), ('17:00-18:00', '17:00-18:00')], default='08:00-09:00', max_length=20),
        ),
    ]
