# Generated manually for QR verification

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("reservations", "0003_rename_contracts_reservat_idx_contracts_reserva_ff1969_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="contract",
            name="verification_code",
            field=models.CharField(
                blank=True,
                db_index=True,
                help_text="Code unique pour vérification du contrat (QR code)",
                max_length=32,
                null=True,
                unique=True,
            ),
        ),
        migrations.AddField(
            model_name="contract",
            name="viewed_at",
            field=models.DateTimeField(
                blank=True,
                help_text="Date de première consultation du contrat (scan QR ou validation)",
                null=True,
            ),
        ),
        migrations.AddIndex(
            model_name="contract",
            index=models.Index(fields=["verification_code"], name="contracts_verific_idx"),
        ),
    ]
