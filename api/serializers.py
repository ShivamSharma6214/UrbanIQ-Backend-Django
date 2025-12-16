from django.contrib.auth import get_user_model
from rest_framework import serializers
from complaints.models import Complaint, ComplaintImage, Department


User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "email"]


class ComplaintImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ComplaintImage
        fields = ["id", "image"]


class DepartmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Department
        fields = ["id", "name"]


class ComplaintSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    imageUrls = serializers.SerializerMethodField()
    videoUrl = serializers.SerializerMethodField()
    status = serializers.CharField(read_only=True)
    assigned_department = DepartmentSerializer(read_only=True)
    assigned_department_id = serializers.PrimaryKeyRelatedField(
        source="assigned_department", queryset=Department.objects.all(), write_only=True, required=True
    )

    class Meta:
        model = Complaint
        fields = [
            "id",
            "tracking_id",
            "title",
            "description",
            "location",
            "complaint_type",
            "status",
            "assigned_department",
            "assigned_department_id",
            "imageUrls",
            "videoUrl",
            "created_at",
            "updated_at",
            "user",
        ]

    def get_imageUrls(self, obj):
        request = self.context.get("request")
        urls = []
        for img in obj.images.all():
            if img.image and hasattr(img.image, "url"):
                if request:
                    urls.append(request.build_absolute_uri(img.image.url))
                else:
                    urls.append(img.image.url)
        return urls

    def get_videoUrl(self, obj):
        if obj.video and hasattr(obj.video, "url"):
            request = self.context.get("request")
            return request.build_absolute_uri(obj.video.url) if request else obj.video.url
        return None