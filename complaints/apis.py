from __future__ import annotations

from typing import Any, Dict

from complaints.serializer import ComplaintSerializer
from rest_framework import permissions, generics

from .models import Complaint

class ComplaintListCreateAPIView(generics.ListCreateAPIView):
	"""DRF view that lists and creates complaints.

	- `GET /complaints/api/` returns active complaints visible to the requesting user.
	- `POST /complaints/api/` creates a complaint; authenticated users only.
	Visibility: staff/superuser see all active complaints; others see their own and complaints
	created by users who share any Group with them.
	"""

	serializer_class = ComplaintSerializer
	permission_classes = [permissions.IsAuthenticated]

	def get_queryset(self):
		user = self.request.user
		qs = Complaint.objects.filter(is_active=True)
		if user.is_staff or user.is_superuser:
			return qs.order_by("-created_at")

		user_group_ids = list(user.groups.values_list("id", flat=True))
		from django.db.models import Q

		return qs.filter(Q(user=user) | Q(user__groups__in=user_group_ids)).distinct().order_by("-created_at")

	def perform_create(self, serializer: Any) -> None:
		serializer.save(user=self.request.user)



