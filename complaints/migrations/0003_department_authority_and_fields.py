from django.db import migrations, models
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db.models import Count


def populate_unique_tracking(apps, schema_editor):
    Complaint = apps.get_model("complaints", "Complaint")
    import uuid as _uuid
    # Set tracking_id for nulls
    for obj in Complaint.objects.filter(tracking_id__isnull=True):
        obj.tracking_id = _uuid.uuid4()
        obj.save(update_fields=["tracking_id"])
    # Fix duplicates: keep first, reassign others
    dup_values = (
        Complaint.objects.values("tracking_id").annotate(c=Count("id")).filter(c__gt=1).values_list("tracking_id", flat=True)
    )
    for val in dup_values:
        qs = Complaint.objects.filter(tracking_id=val).order_by("id")
        first = qs.first()
        for obj in qs.exclude(pk=first.pk):
            obj.tracking_id = _uuid.uuid4()
            obj.save(update_fields=["tracking_id"])


class Migration(migrations.Migration):
    dependencies = [
        ("complaints", "0002_add_status"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Add new fields to Complaint
        # location: guard against duplicate column if it already exists in DB
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        """
                        DO $$
                        BEGIN
                            IF NOT EXISTS (
                                SELECT 1 FROM information_schema.columns
                                WHERE table_name='complaints_complaint' AND column_name='location'
                            ) THEN
                                ALTER TABLE complaints_complaint ADD COLUMN location varchar(255) NULL;
                            END IF;
                        END
                        $$;
                        """
                    ),
                    reverse_sql=(
                        """
                        DO $$
                        BEGIN
                            IF EXISTS (
                                SELECT 1 FROM information_schema.columns
                                WHERE table_name='complaints_complaint' AND column_name='location'
                            ) THEN
                                ALTER TABLE complaints_complaint DROP COLUMN location;
                            END IF;
                        END
                        $$;
                        """
                    ),
                )
            ],
            state_operations=[
                migrations.AddField(
                    model_name="complaint",
                    name="location",
                    field=models.CharField(max_length=255, blank=True, null=True),
                )
            ],
        ),
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        """
                        DO $$
                        BEGIN
                            IF NOT EXISTS (
                                SELECT 1 FROM information_schema.columns
                                WHERE table_name='complaints_complaint' AND column_name='video'
                            ) THEN
                                ALTER TABLE complaints_complaint ADD COLUMN video varchar(100) NULL;
                            END IF;
                        END
                        $$;
                        """
                    ),
                    reverse_sql=(
                        """
                        DO $$
                        BEGIN
                            IF EXISTS (
                                SELECT 1 FROM information_schema.columns
                                WHERE table_name='complaints_complaint' AND column_name='video'
                            ) THEN
                                ALTER TABLE complaints_complaint DROP COLUMN video;
                            END IF;
                        END
                        $$;
                        """
                    ),
                )
            ],
            state_operations=[
                migrations.AddField(
                    model_name="complaint",
                    name="video",
                    field=models.FileField(upload_to="complaints/videos/", blank=True, null=True),
                )
            ],
        ),
        # tracking_id: add column without unique constraint, populate, then enforce uniqueness
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunSQL(
                    sql=(
                        """
                        DO $$
                        BEGIN
                            IF NOT EXISTS (
                                SELECT 1 FROM information_schema.columns
                                WHERE table_name='complaints_complaint' AND column_name='tracking_id'
                            ) THEN
                                ALTER TABLE complaints_complaint ADD COLUMN tracking_id uuid NULL;
                            END IF;
                        END
                        $$;
                        """
                    ),
                    reverse_sql=(
                        """
                        DO $$
                        BEGIN
                            IF EXISTS (
                                SELECT 1 FROM information_schema.columns
                                WHERE table_name='complaints_complaint' AND column_name='tracking_id'
                            ) THEN
                                ALTER TABLE complaints_complaint DROP COLUMN tracking_id;
                            END IF;
                        END
                        $$;
                        """
                    ),
                )
            ],
            state_operations=[
                migrations.AddField(
                    model_name="complaint",
                    name="tracking_id",
                    field=models.UUIDField(editable=False, null=True, db_index=True),
                )
            ],
        ),
        migrations.RunPython(populate_unique_tracking, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name="complaint",
            name="tracking_id",
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True),
        ),
        # Align status choices and default with models (lowercase values)
        migrations.AlterField(
            model_name="complaint",
            name="status",
            field=models.CharField(
                max_length=20,
                default="open",
                choices=[
                    ("open", "Open"),
                    ("in_progress", "In Progress"),
                    ("resolved", "Resolved"),
                    ("closed", "Closed"),
                ],
            ),
        ),

        # Create Department
        migrations.CreateModel(
            name="Department",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(max_length=100, unique=True)),
            ],
            options={"ordering": ["name"]},
        ),

        # Create AuthorityProfile
        migrations.CreateModel(
            name="AuthorityProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="authority_profile",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "department",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="authorities",
                        to="complaints.department",
                    ),
                ),
            ],
        ),

        # Add FK from Complaint to Department (nullable initially)
        migrations.AddField(
            model_name="complaint",
            name="assigned_department",
            field=models.ForeignKey(
                to="complaints.department",
                on_delete=django.db.models.deletion.PROTECT,
                related_name="complaints",
                null=True,
                db_index=True,
            ),
        ),
    ]
