# Generated manually for Contract and ContractTemplate

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('reservations', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContractTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=200)),
                ('contract_type', models.CharField(choices=[('sale', 'Vente'), ('rent', 'Location')], default='sale', max_length=20)),
                ('body', models.TextField(help_text="Contenu du contrat. Placeholders: {{client_name}}, {{property_title}}, {{amount}}, {{scheduled_date}}, etc.")),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
            options={
                'db_table': 'contract_templates',
                'verbose_name': 'Modèle de contrat',
                'verbose_name_plural': 'Modèles de contrat',
                'ordering': ['contract_type', 'name'],
            },
        ),
        migrations.CreateModel(
            name='Contract',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('contract_type', models.CharField(choices=[('sale', 'Vente'), ('rent', 'Location')], default='sale', max_length=20)),
                ('status', models.CharField(choices=[('draft', 'Brouillon'), ('sent', 'Envoyé au client'), ('signed', 'Signé'), ('archived', 'Archivé')], default='draft', max_length=20)),
                ('document', models.FileField(blank=True, max_length=500, null=True, upload_to='contracts/documents/%Y/%m/')),
                ('signed_document', models.FileField(blank=True, max_length=500, null=True, upload_to='contracts/signed/%Y/%m/')),
                ('sent_at', models.DateTimeField(blank=True, null=True)),
                ('signed_at', models.DateTimeField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('notes', models.TextField(blank=True)),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_contracts', to=settings.AUTH_USER_MODEL)),
                ('reservation', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='contract', to='reservations.reservation')),
                ('signed_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='signed_contracts', to=settings.AUTH_USER_MODEL)),
                ('template', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='contracts', to='reservations.contracttemplate')),
            ],
            options={
                'db_table': 'contracts',
                'verbose_name': 'Contrat',
                'verbose_name_plural': 'Contrats',
                'ordering': ['-created_at'],
            },
        ),
        migrations.AddIndex(
            model_name='contract',
            index=models.Index(fields=['reservation'], name='contracts_reservat_idx'),
        ),
        migrations.AddIndex(
            model_name='contract',
            index=models.Index(fields=['status'], name='contracts_status_idx'),
        ),
        migrations.AddIndex(
            model_name='contract',
            index=models.Index(fields=['contract_type'], name='contracts_contract_idx'),
        ),
    ]
