from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("complaints", "0004_seed_departments"),
    ]

    operations = [
        migrations.AddField(
            model_name="complaint",
            name="person_in_charge",
            field=models.CharField(max_length=255, blank=True, null=True),
        ),
        migrations.AddField(
            model_name="complaint",
            name="resolution_signature",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.CreateModel(
            name="ResolutionProofImage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("image", models.ImageField(upload_to="complaints/proof/")),
                (
                    "complaint",
                    models.ForeignKey(
                        on_delete=models.deletion.CASCADE,
                        related_name="resolution_proofs",
                        to="complaints.complaint",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
    ]
