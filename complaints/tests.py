from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Complaint, Department, AuthorityProfile


User = get_user_model()


class DepartmentIsolationTest(TestCase):
	def setUp(self):
		self.client = APIClient()
		# Departments (use get_or_create since seed migration already created them)
		self.police, _ = Department.objects.get_or_create(name="Police")
		self.traffic, _ = Department.objects.get_or_create(name="Traffic")

		# Users
		self.admin = User.objects.create_superuser(username="admin", email="admin@example.com", password="pass")
		self.auth_police = User.objects.create_user(username="ap", email="ap@example.com", password="pass", is_staff=True)
		self.auth_traffic = User.objects.create_user(username="at", email="at@example.com", password="pass", is_staff=True)
		self.citizen = User.objects.create_user(username="cz", email="cz@example.com", password="pass")

		AuthorityProfile.objects.create(user=self.auth_police, department=self.police)
		AuthorityProfile.objects.create(user=self.auth_traffic, department=self.traffic)

		# Complaint assigned to Police by citizen
		self.report = Complaint.objects.create(
			user=self.citizen,
			title="Test",
			description="Something",
			complaint_type=Complaint.ComplaintType.OTHER,
			assigned_department=self.police,
		)

	def test_authority_can_only_see_own_department(self):
		# Police authority can see it
		self.client.force_authenticate(user=self.auth_police)
		res = self.client.get("/api/reports")
		self.assertEqual(res.status_code, 200)
		self.assertEqual(res.data["count"], 1)

		# Traffic authority cannot see it
		self.client.force_authenticate(user=self.auth_traffic)
		res = self.client.get("/api/reports")
		self.assertEqual(res.status_code, 200)
		self.assertEqual(res.data["count"], 0)

	def test_admin_sees_all(self):
		self.client.force_authenticate(user=self.admin)
		res = self.client.get("/api/reports")
		self.assertEqual(res.status_code, 200)
		self.assertEqual(res.data["count"], 1)

	def test_track_endpoint_enforces_department(self):
		url = f"/api/reports/{self.report.tracking_id}/track"
		# Traffic authority forbidden
		self.client.force_authenticate(user=self.auth_traffic)
		res = self.client.get(url)
		self.assertIn(res.status_code, (403, 404))  # should not allow access

		# Police authority allowed
		self.client.force_authenticate(user=self.auth_police)
		res = self.client.get(url)
		self.assertEqual(res.status_code, 200)
