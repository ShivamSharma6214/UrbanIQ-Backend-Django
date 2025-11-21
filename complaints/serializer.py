from complaints.models import Complaint
from rest_framework import serializers


class ComplaintSerializer(serializers.ModelSerializer):
	# `source='user_id'` is redundant because the field name matches the attribute.
	user_id = serializers.IntegerField(read_only=True)

	class Meta:
		model = Complaint
		fields = (
			"id",
			"title",
			"description",
			"complaint_type",
			"timeline",
			"is_active",
			"user_id",
			"created_at",
			"updated_at",
		)
		read_only_fields = ("id", "is_active", "user_id", "created_at", "updated_at")
