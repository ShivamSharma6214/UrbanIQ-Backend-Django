from django.urls import path

from .apis import ComplaintListCreateAPIView

urlpatterns = [
	path("complaint/", ComplaintListCreateAPIView.as_view(), name="complaint-list-create"),
]
