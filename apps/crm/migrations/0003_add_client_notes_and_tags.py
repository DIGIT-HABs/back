# Generated migration for Phase 1 - Client Notes and Tags

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('crm', '0002_initial'),
    ]

    operations = [
        # Add tags field to ClientProfile
        migrations.AddField(
            model_name='clientprofile',
            name='tags',
            field=models.JSONField(blank=True, default=list, help_text="Tags pour catégoriser le client (ex: ['vip', 'investisseur', 'premier_achat'])"),
        ),
        
        # Create ClientNote model
        migrations.CreateModel(
            name='ClientNote',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ('title', models.CharField(blank=True, max_length=200)),
                ('content', models.TextField()),
                ('note_type', models.CharField(choices=[('general', 'Général'), ('meeting', 'Compte-rendu réunion'), ('call', 'Appel téléphonique'), ('follow_up', 'Suivi'), ('alert', 'Alerte'), ('opportunity', 'Opportunité')], default='general', max_length=20)),
                ('is_important', models.BooleanField(default=False)),
                ('is_pinned', models.BooleanField(default=False)),
                ('reminder_date', models.DateTimeField(blank=True, null=True)),
                ('reminder_sent', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('author', models.ForeignKey(help_text='Agent qui a écrit la note', on_delete=django.db.models.deletion.CASCADE, related_name='client_notes_written', to=settings.AUTH_USER_MODEL)),
                ('client_profile', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notes', to='crm.clientprofile')),
            ],
            options={
                'ordering': ['-is_pinned', '-is_important', '-created_at'],
            },
        ),
        
        # Add indexes for ClientNote
        migrations.AddIndex(
            model_name='clientnote',
            index=models.Index(fields=['client_profile', '-created_at'], name='crm_clientn_client__idx'),
        ),
        migrations.AddIndex(
            model_name='clientnote',
            index=models.Index(fields=['author', '-created_at'], name='crm_clientn_author_idx'),
        ),
    ]
