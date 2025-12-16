from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("complaints", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="complaint",
            name="status",
            field=models.CharField(
                max_length=20,
                default="OPEN",
                choices=[
                    ("OPEN", "Open"),
                    ("IN_PROGRESS", "In Progress"),
                    ("RESOLVED", "Resolved"),
                    ("CLOSED", "Closed"),
                ],
            ),
        ),
    ]
