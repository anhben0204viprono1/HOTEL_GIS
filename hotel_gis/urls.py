from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('hotels.urls')),
    path('accounts/', include('accounts.urls')),
    path('bookings/', include('bookings.urls')),
    path('dashboard/', include('dashboard.urls')),
    # Dashboard admin (staff/superuser)
    path('dashboard/',  include('dashboard.urls', namespace='dashboard')),

    # ── MỚI: Staff portal (nhân viên khách sạn) ──
    path('staff/',      include('staff.urls', namespace='staff')),

    # Public-facing (nếu có)
    # path('', include('hotels.urls')),
    # path('bookings/', include('bookings.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)