from django.urls import path
from .views import RegisterView, LoginView, MeView, ComplaintListCreateView, MyReportsView, ComplaintDetailView, ReportTrackView, DepartmentListView

urlpatterns = [
    path("auth/register", RegisterView.as_view(), name="auth-register"),
    path("auth/login", LoginView.as_view(), name="auth-login"),
    path("user/me", MeView.as_view(), name="user-me"),
    path("reports", ComplaintListCreateView.as_view(), name="reports"),
    path("reports/mine", MyReportsView.as_view(), name="my-reports"),
    path("reports/<int:pk>", ComplaintDetailView.as_view(), name="report-detail"),
    path("reports/<uuid:tracking_id>/track", ReportTrackView.as_view(), name="report-track"),
    path("departments", DepartmentListView.as_view(), name="departments"),
]