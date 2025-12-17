from django.core.mail import send_mail
from django.conf import settings
from django.utils.text import Truncator
from complaints.models import Complaint
import re

try:
    import dns.resolver  # type: ignore
except Exception:
    dns = None


ALLOWED_GMAIL_DOMAINS = {"gmail.com", "googlemail.com"}
BLOCKED_TEST_DOMAINS = {"test.com", "example.com", "invalid", "fake.com", "localhost"}


def _is_valid_email_format(email: str) -> bool:
    return bool(re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email or ""))


def _has_mx_record(domain: str) -> bool:
    if not dns or not hasattr(dns, "resolver"):
        return True  # cannot verify; do not block
    try:
        answers = dns.resolver.resolve(domain, "MX")  # type: ignore[attr-defined]
        return len(answers) > 0
    except Exception:
        return False


def _validate_recipient(email: str):
    if not _is_valid_email_format(email):
        return False, "Invalid email format"
    domain = email.split("@")[-1].lower()
    if domain in BLOCKED_TEST_DOMAINS:
        return False, "Test or blocked domain"
    if domain not in ALLOWED_GMAIL_DOMAINS:
        return False, "Non-Google domain"
    if not _has_mx_record(domain):
        return False, "No MX record"
    return True, "OK"


def _build_tracking_link(tracking_id):
    # Relative path as required
    return f"/reports/track/{tracking_id}"


def _send_smart_mail(subject: str, message: str, recipient: str):
    if not recipient:
        return False, "Missing recipient"

    ok, reason = _validate_recipient(recipient)
    if not ok:
        info = "Email notifications could not be delivered because this email address is not a valid Google-registered inbox."
        print(f"Email skipped for {recipient}: {reason}")
        return False, info

    if not getattr(settings, "EMAIL_CONFIGURED", False):
        info = "Email configuration is missing; notification was not sent."
        print(info)
        return False, info

    try:
        send_mail(
            subject,
            message,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'no-reply@urbaniq.local'),
            [recipient],
            fail_silently=False,
        )
        return True, "Sent"
    except Exception as e:
        print(f"Email notification failed for {recipient}: {e}")
        return False, "Notification could not be delivered."


def notify_report_created(complaint: Complaint):
    short_desc = Truncator(complaint.description or "").chars(120)
    tracking_link = _build_tracking_link(complaint.tracking_id)
    dept = getattr(complaint.assigned_department, 'name', 'Concerned Department')
    subject = f"Complaint Registered: {complaint.title}"
    greeting = complaint.user.username or complaint.user.email or "Citizen"
    message = (
        f"Dear {greeting},\n\n"
        f"Your complaint has been successfully registered.\n\n"
        f"Complaint ID: {complaint.tracking_id}\n"
        f"Title: {complaint.title}\n"
        f"Description: {short_desc}\n"
        f"Assigned Department: {dept}\n"
        f"Tracking Link: {tracking_link}\n\n"
        f"The concerned department will begin working on your complaint as soon as possible.\n"
        f"Thank you for helping improve our city."
    )
    return _send_smart_mail(subject, message, complaint.user.email)

    try:
        send_sms_placeholder(complaint)
    except Exception as e:
        print(f"SMS placeholder failed: {e}")


def notify_report_in_review(complaint: Complaint, person_in_charge: str):
    dept = getattr(complaint.assigned_department, 'name', 'Concerned Department')
    subject = f"Complaint In Review: {complaint.tracking_id}"
    greeting = complaint.user.username or complaint.user.email or "Citizen"
    message = (
        f"Dear {greeting},\n\n"
        f"Your complaint is currently under review.\n\n"
        f"Complaint ID: {complaint.tracking_id}\n"
        f"Department: {dept}\n"
        f"Person in Charge: {person_in_charge or 'Department Representative'}\n\n"
        f"Your complaint is being handled and we will update you upon completion."
    )
    return _send_smart_mail(subject, message, complaint.user.email)


def notify_report_resolved(complaint: Complaint, person_in_charge: str):
    dept = getattr(complaint.assigned_department, 'name', 'Concerned Department')
    subject = f"Complaint Resolved: {complaint.tracking_id}"
    greeting = complaint.user.username or complaint.user.email or "Citizen"
    message = (
        f"Dear {greeting},\n\n"
        f"Your complaint has been successfully resolved.\n\n"
        f"Complaint ID: {complaint.tracking_id}\n"
        f"Department: {dept}\n"
        f"Person in Charge: {person_in_charge or 'Department Representative'}\n\n"
        f"Proof of resolution has been recorded and is available with the department.\n"
        f"Thank you for helping improve our city."
    )
    return _send_smart_mail(subject, message, complaint.user.email)


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
