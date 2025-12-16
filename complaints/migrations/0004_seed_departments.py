from django.db import migrations

DEPARTMENTS = [
    "Municipal",
    "Police",
    "Traffic",
    "Electricity",
    "Water",
    "Sanitation",
]

def seed_departments(apps, schema_editor):
    Department = apps.get_model("complaints", "Department")
    for name in DEPARTMENTS:
        Department.objects.get_or_create(name=name)


def unseed_departments(apps, schema_editor):
    Department = apps.get_model("complaints", "Department")
    Department.objects.filter(name__in=DEPARTMENTS).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("complaints", "0003_department_authority_and_fields"),
    ]

    operations = [
        migrations.RunPython(seed_departments, reverse_code=unseed_departments),
    ]
