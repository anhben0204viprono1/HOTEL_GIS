from django.apps import AppConfig
from django.db.models.signals import post_migrate


class AccountsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "accounts"

    def ready(self):
        post_migrate.connect(ensure_default_groups, sender=self)


def ensure_default_groups(*, sender, **kwargs):
    """
    Tạo sẵn group "Employee" để phân quyền truy cập dashboard.
    Chạy sau migrate để đảm bảo Permission đã được tạo.
    """
    from django.contrib.auth.models import Group, Permission

    employee, _ = Group.objects.get_or_create(name="Employee")

    # Gán quyền cơ bản cho nhân viên trên các app nghiệp vụ (hotels, bookings).
    perms = Permission.objects.filter(
        content_type__app_label__in=["hotels", "bookings"]
    )
    if perms.exists():
        employee.permissions.set(perms)

