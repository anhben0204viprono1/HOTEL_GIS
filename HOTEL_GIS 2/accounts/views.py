from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegisterForm, LoginForm
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