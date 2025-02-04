from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('main_app', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='emploitemps',
            name='duration',
            field=models.IntegerField(default=2),
        ),
    ]
