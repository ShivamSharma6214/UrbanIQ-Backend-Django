from django.contrib.auth import get_user_model
from complaints.models import AuthorityProfile

User = get_user_model()

print('\n=== USER ROLES ===')
admin = User.objects.filter(email='alice123@gmail.com').first()
if admin:
    print(f'alice123@gmail.com: is_staff={admin.is_staff}, is_superuser={admin.is_superuser}')
else:
    print('alice123@gmail.com: Not found')

citizen = User.objects.filter(email='citizen1@gmail.com').first()
if citizen:
    print(f'citizen1@gmail.com: is_staff={citizen.is_staff}, is_superuser={citizen.is_superuser}')
else:
    print('citizen1@gmail.com: Not found')

print('\n=== AUTHORITY PROFILES ===')
for ap in AuthorityProfile.objects.all():
    print(f'{ap.user.email} → {ap.department.name}')

print('\n=== VERIFICATION COMPLETE ===\n')
