from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from .forms import RegisterForm, LoginForm, ProfileUpdateForm
from bookings.models import Booking


def register(request):
    if request.user.is_authenticated:
        return redirect('hotels:list')
    form = RegisterForm(request.POST or None)
    if form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, f'Chào mừng {user.first_name or user.username}! Tài khoản đã được tạo.')
        return redirect('hotels:list')
    return render(request, 'accounts/register.html', {'form': form})


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
        update_session_auth_hash(request, user)  # giữ đăng nhập sau khi đổi mật khẩu
        messages.success(request, '🔐 Đổi mật khẩu thành công.')
        return redirect('accounts:profile')
    return render(request, 'accounts/password_change.html', {'form': form})
