# Generated manually for Agency.logo

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('custom_auth', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='agency',
            name='logo',
            field=models.ImageField(blank=True, null=True, upload_to='agencies/logos/'),
        ),
    ]
