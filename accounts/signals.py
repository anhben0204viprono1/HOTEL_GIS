from django.contrib.auth.models import Group
from django.db.models.signals import post_migrate
from django.dispatch import receiver


@receiver(post_migrate)
def ensure_employee_group(sender, **kwargs):
    if getattr(sender, "label", None) != "accounts":
        return
    Group.objects.get_or_create(name="Employee")

