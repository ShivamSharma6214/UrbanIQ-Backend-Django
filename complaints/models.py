from django.db import models
from django.conf import settings

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
    is_active = models.BooleanField(default=True)
    timeline = models.JSONField(blank=True, null=True)
    complaint_type = models.CharField(choices=ComplaintType.choices, max_length=50)

    def __str__(self):
        return self.title
