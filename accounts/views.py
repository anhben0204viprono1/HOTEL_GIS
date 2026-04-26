from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.core.mail import send_mail
from django.conf import settings
from .forms import RegisterForm, LoginForm, ProfileUpdateForm
from bookings.models import Booking
from bookings.email_utils import send_password_changed
import random


def register(request):
    if request.user.is_authenticated:
        return redirect('hotels:list')
    form = RegisterForm(request.POST or None)
    if form.is_valid():
        user = form.save(commit=False)
        user.is_active = False
        user.save()

        otp = str(random.randint(100000, 999999))
        request.session['verify_otp']     = otp
        request.session['verify_user_id'] = user.pk
        request.session['verify_email']   = user.email

        send_mail(
            subject='[Hotel GIS] Mã xác nhận đăng ký',
            message=(
                f'Xin chào {user.first_name or user.username},\n\n'
                f'Mã xác nhận của bạn là:\n\n'
                f'  {otp}\n\n'
                f'Mã có hiệu lực trong 10 phút. Vui lòng không chia sẻ mã này cho bất kỳ ai.\n\n'
                f'— Hotel GIS'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        messages.info(request, f'📧 Mã xác nhận đã được gửi tới {user.email}.')
        return redirect('accounts:verify_email')

    return render(request, 'accounts/register.html', {'form': form})


def verify_email(request):
    user_id = request.session.get('verify_user_id')
    email   = request.session.get('verify_email')
    otp     = request.session.get('verify_otp')

    if not user_id or not otp:
        messages.error(request, '⚠️ Phiên xác nhận đã hết hạn. Vui lòng đăng ký lại.')
        return redirect('accounts:register')

    if request.method == 'POST':
        entered = request.POST.get('otp', '').strip()
        if entered == otp:
            from django.contrib.auth.models import User
            try:
                user = User.objects.get(pk=user_id)
                user.is_active = True
                user.save()
                for key in ('verify_otp', 'verify_user_id', 'verify_email'):
                    request.session.pop(key, None)
                login(request, user, backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request, f'🎉 Chào mừng {user.first_name or user.username}! Tài khoản đã được xác nhận.')
                return redirect('hotels:list')
            except User.DoesNotExist:
                messages.error(request, 'Tài khoản không tồn tại.')
                return redirect('accounts:register')
        else:
            messages.error(request, '❌ Mã xác nhận không đúng. Vui lòng thử lại.')

    return render(request, 'accounts/verify_email.html', {'email': email})


def resend_otp(request):
    user_id = request.session.get('verify_user_id')
    email   = request.session.get('verify_email')
    if not user_id or not email:
        return redirect('accounts:register')
    otp = str(random.randint(100000, 999999))
    request.session['verify_otp'] = otp
    send_mail(
        subject='[Hotel GIS] Mã xác nhận mới',
        message=f'Mã xác nhận mới của bạn là:\n\n  {otp}\n\n— Hotel GIS',
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[email],
        fail_silently=False,
    )
    messages.success(request, f'📧 Đã gửi mã mới tới {email}.')
    return redirect('accounts:verify_email')


def user_login(request):
    if request.user.is_authenticated:
        return redirect('hotels:list')
    form = LoginForm(request, request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.get_user()
        login(request, user)
        messages.success(request, f'Xin chào {user.first_name or user.username}!')
        return redirect(request.GET.get('next', 'hotels:list'))
    return render(request, 'accounts/login.html', {'form': form})


def user_logout(request):
    logout(request)
    messages.info(request, 'Bạn đã đăng xuất thành công.')
    return redirect('hotels:list')


@login_required
def profile(request):
    bookings = (
        Booking.objects
        .filter(user=request.user)
        .select_related('room__room_type__hotel')
        .order_by('-created_at')
    )
    return render(request, 'accounts/profile.html', {'bookings': bookings})


@login_required
def profile_edit(request):
    form = ProfileUpdateForm(request.POST or None, instance=request.user)
    if request.method == 'POST' and form.is_valid():
        form.save()
        messages.success(request, '✅ Đã cập nhật thông tin tài khoản.')
        return redirect('accounts:profile')
    return render(request, 'accounts/profile_edit.html', {'form': form})


@login_required
def password_change(request):
    form = PasswordChangeForm(user=request.user, data=request.POST or None)
    if request.method == 'POST' and form.is_valid():
        user = form.save()
        update_session_auth_hash(request, user)
        send_password_changed(user)
        messages.success(request, '🔐 Đổi mật khẩu thành công. Chúng tôi đã gửi email xác nhận.')
        return redirect('accounts:profile')
    return render(request, 'accounts/password_change.html', {'form': form})