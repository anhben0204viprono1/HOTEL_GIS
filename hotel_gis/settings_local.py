"""
Settings dùng cho local/dev trong môi trường không có PostgreSQL driver.
Chỉ override DATABASES để chạy các lệnh như makemigrations/check/test nhanh.
"""
from .settings import *  # noqa

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

