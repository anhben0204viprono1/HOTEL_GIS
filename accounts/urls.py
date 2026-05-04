from django.urls import path
from django.contrib.auth import views as auth_views
from django.urls import reverse_lazy
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/',       views.register,     name='register'),
    path('verify-email/',   views.verify_email, name='verify_email'),
    path('resend-otp/',     views.resend_otp,   name='resend_otp'),
    path('login/',    views.user_login, name='login'),
    path('logout/',   views.user_logout, name='logout'),
    path('profile/',  views.profile, name='profile'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('password/change/', views.password_change, name='password_change'),

    # ── Quên mật khẩu (Django built-in views) ─────────────────────────────
    path('password-reset/',
         auth_views.PasswordResetView.as_view(
             template_name='registration/password_reset_form.html',
             email_template_name='registration/password_reset_email.html',
             subject_template_name='registration/password_reset_subject.txt',
         ),
         name='password_reset'),
    path('password-reset/done/',
         auth_views.PasswordResetDoneView.as_view(
             template_name='registration/password_reset_done.html',
         ),
         name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(
             template_name='registration/password_reset_confirm.html',
             success_url=reverse_lazy('accounts:password_reset_complete')
         ),
         name='password_reset_confirm'),
    path('reset/done/',
         auth_views.PasswordResetCompleteView.as_view(
             template_name='registration/password_reset_complete.html',
         ),
         name='password_reset_complete'),
]