from django.core.mail import send_mail
from django.conf import settings
from django.utils.text import Truncator
from complaints.models import Complaint


def _build_tracking_link(tracking_id):
    # Relative path as required
    return f"/reports/track/{tracking_id}"


def notify_report_created(complaint: Complaint):
    try:
        subject = f"Report submitted: {complaint.title}"
        short_desc = Truncator(complaint.description or "").chars(120)
        tracking_link = _build_tracking_link(complaint.tracking_id)
        message = (
            f"Thank you for your report.\n\n"
            f"Title: {complaint.title}\n"
            f"Description: {short_desc}\n"
            f"Report ID: {complaint.id}\n"
            f"Tracking: {tracking_link}\n"
        )
        recipient = complaint.user.email
        if recipient:
            send_mail(
                subject,
                message,
                getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@example.com'),
                [recipient],
                fail_silently=True,
            )
    except Exception as e:
        # Do not block request
        print(f"Email notification failed: {e}")

    # SMS / Message placeholder
    try:
        send_sms_placeholder(complaint)
    except Exception as e:
        print(f"SMS placeholder failed: {e}")


def send_sms_placeholder(complaint: Complaint):
    user = complaint.user
    phone = getattr(user, 'phone_number', None)
    if not phone:
        return
    tracking_link = _build_tracking_link(complaint.tracking_id)
    log_line = (
        f"[SMS PLACEHOLDER] To:{phone} | Report:{complaint.id} | Dept:{getattr(complaint.assigned_department, 'name', '-') } "
        f"| Status:{complaint.status} | Track:{tracking_link}"
    )
    print(log_line)
