from django.contrib.auth import get_user_model, authenticate
from django.db import transaction
from django.core.files.base import ContentFile
from django.conf import settings
import io
import os
import subprocess
from PIL import Image
import shutil
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework_simplejwt.tokens import RefreshToken

from complaints.models import Complaint, ComplaintImage, Department, AuthorityProfile
from .serializers import ComplaintSerializer, UserSerializer, DepartmentSerializer

User = get_user_model()


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        name = request.data.get("name")
        email = request.data.get("email")
        password = request.data.get("password")
        if not all([name, email, password]):
            return Response({"error": "Missing fields"}, status=400)
        if User.objects.filter(email=email).exists():
            return Response({"error": "Email already registered"}, status=400)
        username = email.split("@")[0]
        user = User.objects.create_user(username=username, email=email, password=password)
        user.first_name = name
        user.save()
        refresh = RefreshToken.for_user(user)
        return Response({"success": True, "token": str(refresh.access_token), "refresh": str(refresh)}, status=201)


class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        if not all([email, password]):
            return Response({"error": "Missing credentials"}, status=400)
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({"error": "Invalid credentials"}, status=400)
        user_auth = authenticate(username=user.username, password=password)
        if not user_auth:
            return Response({"error": "Invalid credentials"}, status=400)
        refresh = RefreshToken.for_user(user_auth)
        return Response({
            "token": str(refresh.access_token),
            "refresh": str(refresh),
        })


class MeView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)


class ComplaintListCreateView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        page = int(request.query_params.get('page', 1))
        page_size = int(request.query_params.get('page_size', 10))

        # Role-based visibility
        user = request.user
        if user.is_superuser:
            qs = Complaint.objects.filter(is_active=True)
        elif user.is_staff:
            # Authority: limit to their department
            try:
                dept = user.authority_profile.department
                qs = Complaint.objects.filter(is_active=True, assigned_department=dept)
            except AuthorityProfile.DoesNotExist:
                qs = Complaint.objects.none()
        else:
            # Citizen: only own
            qs = Complaint.objects.filter(is_active=True, user=user)

        qs = qs.select_related("user", "assigned_department").prefetch_related("images").order_by('-created_at')
        total = qs.count()
        start = (page - 1) * page_size
        end = start + page_size
        serializer = ComplaintSerializer(qs[start:end], many=True, context={"request": request})
        return Response({
            "results": serializer.data,
            "page": page,
            "page_size": page_size,
            "count": total,
            "total_pages": (total + page_size - 1) // page_size,
        })

    @transaction.atomic
    def post(self, request):
        title = request.data.get("title")
        description = request.data.get("description")
        location = request.data.get("location")
        complaint_type = request.data.get("complaint_type", "Other")
        dept_id = request.data.get("assigned_department_id") or request.data.get("assigned_department")

        if not title or not description or not dept_id:
            return Response({"error": "Title, description and assigned_department_id are required"}, status=400)
        try:
            department = Department.objects.get(pk=dept_id)
        except Department.DoesNotExist:
            return Response({"error": "Invalid department"}, status=400)

        complaint = Complaint.objects.create(
            user=request.user,
            title=title,
            description=description,
            location=location,
            complaint_type=complaint_type,
            assigned_department=department,
        )
        # Handle video compression if provided
        video = request.FILES.get("video")
        if video:
            try:
                compressed_video = self._compress_video(video)
                if compressed_video:
                    complaint.video.save(compressed_video.name, compressed_video, save=True)
            except Exception as e:
                # Log but do not fail the request
                print(f"Video compression failed: {e}")
                complaint.video = video
                complaint.save()
        # Handle images compression
        images = request.FILES.getlist("images")
        for img in images:
            try:
                optimized_image = self._compress_image(img)
                ComplaintImage.objects.create(complaint=complaint, image=optimized_image)
            except Exception as e:
                print(f"Image compression failed: {e}")
                ComplaintImage.objects.create(complaint=complaint, image=img)
        serializer = ComplaintSerializer(complaint, context={"request": request})
        # Fire-and-forget notifications
        try:
            from .services import notify_report_created
            notify_report_created(complaint)
        except Exception as e:
            print(f"notify_report_created failed: {e}")
        return Response({"success": True, "report": serializer.data}, status=201)

    def _compress_image(self, uploaded):
        """Compress/resize image to max width keeping aspect ratio; return ContentFile."""
        MAX_WIDTH = int(getattr(settings, "IMAGE_MAX_WIDTH", 1280))
        QUALITY = int(getattr(settings, "IMAGE_JPEG_QUALITY", 70))
        img = Image.open(uploaded)
        img_format = (img.format or "JPEG").upper()
        if img.width > MAX_WIDTH:
            ratio = MAX_WIDTH / float(img.width)
            new_size = (MAX_WIDTH, int(img.height * ratio))
            img = img.resize(new_size, Image.LANCZOS)
        buffer = io.BytesIO()
        save_kwargs = {"optimize": True}
        if img_format in ("JPEG", "JPG"):
            save_kwargs["quality"] = QUALITY
            img_format = "JPEG"
        else:
            img_format = "PNG"  # fallback
        img.save(buffer, format=img_format, **save_kwargs)
        buffer.seek(0)
        base_name = os.path.splitext(uploaded.name)[0]
        new_name = f"{base_name}_compressed.{ 'jpg' if img_format=='JPEG' else 'png'}"
        return ContentFile(buffer.read(), name=new_name)

    def _compress_video(self, uploaded):
        """Compress video using ffmpeg if available; returns ContentFile or None."""
        if shutil.which("ffmpeg") is None:
            return None
        import tempfile, shutil
        with tempfile.NamedTemporaryFile(suffix=os.path.splitext(uploaded.name)[1], delete=False) as in_tmp:
            for chunk in uploaded.chunks():
                in_tmp.write(chunk)
            in_path = in_tmp.name
        out_path = in_path + "_out.mp4"
        cmd = [
            "ffmpeg", "-y", "-i", in_path,
            "-vf", "scale=-2:720",
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "28",
            "-c:a", "aac", "-b:a", "128k",
            out_path,
        ]
        try:
            subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)
            with open(out_path, "rb") as f:
                data = f.read()
            content = ContentFile(data, name=os.path.splitext(uploaded.name)[0] + "_compressed.mp4")
            return content
        finally:
            try:
                os.remove(in_path)
            except Exception:
                pass
            try:
                os.remove(out_path)
            except Exception:
                pass


class MyReportsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = Complaint.objects.filter(user=request.user, is_active=True).select_related("user", "assigned_department").prefetch_related("images").order_by('-created_at')
        serializer = ComplaintSerializer(qs, many=True, context={"request": request})
        return Response(serializer.data)


class ComplaintDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self, pk, user):
        try:
            obj = Complaint.objects.select_related('user').prefetch_related('images').get(pk=pk, is_active=True)
        except Complaint.DoesNotExist:
            return None
        # Citizen: only own
        if obj.user == user:
            return obj
        # Admin: all
        if user.is_superuser:
            return obj
        # Authority: only same department
        if user.is_staff:
            try:
                dept = user.authority_profile.department
                if obj.assigned_department_id == dept.id:
                    return obj
            except AuthorityProfile.DoesNotExist:
                pass
        return None

    def get(self, request, pk):
        obj = self.get_object(pk, request.user)
        if not obj:
            return Response({'error': 'Not found'}, status=404)
        serializer = ComplaintSerializer(obj, context={'request': request})
        return Response(serializer.data)

    def patch(self, request, pk):
        obj = self.get_object(pk, request.user)
        if not obj:
            return Response({'error': 'Not found'}, status=404)
        status_val = request.data.get('status')
        allowed = {c[0] for c in Complaint.Status.choices}
        if status_val and status_val in allowed:
            obj.status = status_val
            obj.save(update_fields=['status'])
        serializer = ComplaintSerializer(obj, context={'request': request})
        return Response(serializer.data)

    def delete(self, request, pk):
        obj = self.get_object(pk, request.user)
        if not obj:
            return Response({'error': 'Not found'}, status=404)
        obj.is_active = False
        obj.save(update_fields=['is_active'])
        return Response({'success': True}, status=204)


class ReportTrackView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, tracking_id):
        try:
            obj = Complaint.objects.select_related('user', 'assigned_department').get(tracking_id=tracking_id, is_active=True)
        except Complaint.DoesNotExist:
            return Response({'error': 'Not found'}, status=404)

        # Authorize same as detail view
        user = request.user
        if obj.user == user or user.is_superuser:
            serializer = ComplaintSerializer(obj, context={'request': request})
            return Response(serializer.data)
        if user.is_staff:
            try:
                dept = user.authority_profile.department
                if obj.assigned_department_id == dept.id:
                    serializer = ComplaintSerializer(obj, context={'request': request})
                    return Response(serializer.data)
            except AuthorityProfile.DoesNotExist:
                pass
        return Response({'error': 'Forbidden'}, status=403)


class DepartmentListView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = Department.objects.all().order_by('name')
        data = DepartmentSerializer(qs, many=True).data
        return Response(data)