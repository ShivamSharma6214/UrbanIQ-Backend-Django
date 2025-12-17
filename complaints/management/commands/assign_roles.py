from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from complaints.models import Department, AuthorityProfile

User = get_user_model()


class Command(BaseCommand):
    help = 'Assign roles and departments to existing users based on email IDs'

    def handle(self, *args, **options):
        # Email to role mapping
        role_mapping = {
            'ADMIN': [
                'alice123@gmail.com',
            ],
            'CITIZEN': [
                'citizen1@gmail.com',
                'donshivam234@gmail.com',
            ],
            'AUTHORITY': {
                'police1@gmail.com': 'Police',
                'fire1@gmail.com': 'Fire',
                'municipal1@gmail.com': 'Municipal',
            }
        }

        self.stdout.write(self.style.SUCCESS('\n=== Starting Role Assignment ===\n'))

        # Process ADMIN users
        for email in role_mapping['ADMIN']:
            user = User.objects.filter(email=email).first()
            if not user:
                self.stdout.write(self.style.WARNING(f'⚠ User not found: {email}'))
                continue
            
            user.is_staff = True
            user.is_superuser = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f'✔ Assigned ADMIN to {email}'))

        # Process CITIZEN users
        for email in role_mapping['CITIZEN']:
            user = User.objects.filter(email=email).first()
            if not user:
                self.stdout.write(self.style.WARNING(f'⚠ User not found: {email}'))
                continue
            
            # Citizens are regular users (no special flags)
            user.is_staff = False
            user.is_superuser = False
            user.save()
            
            # Remove AuthorityProfile if it exists
            if hasattr(user, 'authority_profile'):
                user.authority_profile.delete()
            
            self.stdout.write(self.style.SUCCESS(f'✔ Assigned CITIZEN to {email}'))

        # Process AUTHORITY users
        for email, dept_name in role_mapping['AUTHORITY'].items():
            user = User.objects.filter(email=email).first()
            if not user:
                self.stdout.write(self.style.WARNING(f'⚠ User not found: {email}'))
                continue
            
            department = Department.objects.filter(name=dept_name).first()
            if not department:
                self.stdout.write(self.style.WARNING(f'⚠ Department not found: {dept_name}'))
                continue
            
            # Authority should be staff (but not superuser)
            user.is_staff = True
            user.is_superuser = False
            user.save()
            
            # Create or update AuthorityProfile
            authority_profile, created = AuthorityProfile.objects.get_or_create(
                user=user,
                defaults={'department': department}
            )
            if not created and authority_profile.department != department:
                authority_profile.department = department
                authority_profile.save()
            
            self.stdout.write(self.style.SUCCESS(f'✔ Assigned AUTHORITY ({dept_name}) to {email}'))

        self.stdout.write(self.style.SUCCESS('\n=== Role Assignment Complete ===\n'))
