from django.apps import AppConfig


class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'

    def ready(self):
        try:
            from django.contrib.auth.models import Group
            Group.objects.get_or_create(name='Employee')
        except Exception:
            pass  # DB chưa sẵn sàng (trước migrate lần đầu)
