from pathlib import Path
import os
os.environ['GDAL_LIBRARY_PATH'] = '/opt/homebrew/opt/gdal/lib/libgdal.dylib'

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = 'django-insecure-change-this-in-production-use-env-variable'
DEBUG = True
ALLOWED_HOSTS = ['*']

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    'crispy_bootstrap5',
    'hotels',
    'dashboard',
    'accounts',
    'bookings',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'hotel_gis.urls'

TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    # Thư mục templates/ ở gốc project — phải đứng TRƯỚC app dirs
    # để admin override (templates/admin/hotels/hotel_change_form.html) hoạt động
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.debug',
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
    ]},
}]

WSGI_APPLICATION = 'hotel_gis.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'hotel_gis',
        'USER': 'postgres',
        'PASSWORD': 'vu2005',
        'HOST': 'localhost',
        'PORT': '5432',
    }
}
LANGUAGE_CODE = 'vi'
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_I18N = True
USE_L10N = False   # Tắt locale number format — tránh dấu phẩy thay dấu chấm trong JS
USE_TZ = True

STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
CRISPY_ALLOWED_TEMPLATE_PACKS = 'bootstrap5'
CRISPY_TEMPLATE_PACK = 'bootstrap5'
LOGIN_URL = '/accounts/login/'
LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# Base URL dùng cho email/QR/link tuyệt đối (override bằng env SITE_URL)
SITE_URL = os.environ.get('SITE_URL', 'http://localhost:8000')

# ── MoMo (Collection Link) ────────────────────────────────
# Bật bằng env: MOMO_ENABLED=1 và set các biến bên dưới
MOMO_ENABLED = os.environ.get('MOMO_ENABLED', '0') == '1'
MOMO_ENDPOINT = os.environ.get('MOMO_ENDPOINT', 'https://test-payment.momo.vn')
MOMO_PARTNER_CODE = os.environ.get('MOMO_PARTNER_CODE', '')
MOMO_ACCESS_KEY = os.environ.get('MOMO_ACCESS_KEY', '')
MOMO_SECRET_KEY = os.environ.get('MOMO_SECRET_KEY', '')
MOMO_STORE_ID = os.environ.get('MOMO_STORE_ID', 'HotelGIS')

# ── Mailtrap Transactional (API) ──────────────────────────
ANYMAIL = {
    "MAILTRAP_API_TOKEN": "<b79bdc57d64e8834f126cfc40310c321>",
}
EMAIL_BACKEND = "anymail.backends.mailtrap.EmailBackend"
DEFAULT_FROM_EMAIL = "Hotel GIS <hello@demomailtrap.co>"
