from django.db import models
from django.conf import settings
import uuid

# Create your models here.

class TimestampModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Complaint(TimestampModel):
    class ComplaintType(models.TextChoices):
        GARBAGE = 'Garbage', 'Garbage'
        ROAD = 'Road', 'Road'
        WATER = 'Water', 'Water'
        ELECTRICITY = 'Electricity', 'Electricity'
        OTHER = 'Other', 'Other'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    location = models.CharField(max_length=255, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    timeline = models.JSONField(blank=True, null=True)
    complaint_type = models.CharField(choices=ComplaintType.choices, max_length=50)
    video = models.FileField(upload_to="complaints/videos/", blank=True, null=True)
    # New tracking id for external tracking
    tracking_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    person_in_charge = models.CharField(max_length=255, blank=True, null=True)
    resolution_signature = models.TextField(blank=True, null=True)
    class Status(models.TextChoices):
        OPEN = 'open', 'Open'
        IN_PROGRESS = 'in_progress', 'In Progress'
        RESOLVED = 'resolved', 'Resolved'
        CLOSED = 'closed', 'Closed'
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)

    def __str__(self):
        return self.title


class ComplaintImage(TimestampModel):
    complaint = models.ForeignKey(Complaint, related_name="images", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="complaints/images/")

    def __str__(self):
        return f"Image for complaint {self.complaint_id}"

# Department and Authority mapping
class Department(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class AuthorityProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="authority_profile")
    department = models.ForeignKey(Department, on_delete=models.PROTECT, related_name="authorities")

    def __str__(self):
        return f"{self.user} -> {self.department}"

# Add department assignment to complaint (indexed for filtering)
Complaint.add_to_class(
    'assigned_department',
    models.ForeignKey(Department, on_delete=models.PROTECT, related_name='complaints', null=True, db_index=True)
)


class ResolutionProofImage(TimestampModel):
    complaint = models.ForeignKey(Complaint, related_name="resolution_proofs", on_delete=models.CASCADE)
    image = models.ImageField(upload_to="complaints/proof/")

    def __str__(self):
        return f"Proof for complaint {self.complaint_id}"
