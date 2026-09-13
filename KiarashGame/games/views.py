from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.contrib import messages
from django.http import JsonResponse
from .models import Game, UserProfile, PlayHistory
import os
from django.conf import settings
import subprocess
import threading
import sys


def home(request):
    games = Game.objects.all()

    # Search
    query = request.GET.get('q', '').strip()
    if query:
        games = games.filter(title__icontains=query)

    context = {
        'games': games,
        'total_games': Game.objects.count(),
        'total_plays': sum(g.plays for g in Game.objects.all()),
        'query': query,
    }

    if request.user.is_authenticated:
        profile, _ = UserProfile.objects.get_or_create(user=request.user)
        context['profile'] = profile
        context['user_history'] = PlayHistory.objects.filter(user=request.user)[:5]

    return render(request, 'games/home.html', context)

def game_detail(request, slug):
    """صفحه‌ی جزئیات بازی"""
    game = get_object_or_404(Game, slug=slug)

    # بازی‌های مشابه (بر اساس order)
    similar_games = Game.objects.exclude(id=game.id).order_by('order')[:4]

    # اگه کاربر لاگین باشه، ببین قبلاً این بازی رو کرده یا نه
    last_played = None
    if request.user.is_authenticated:
        last_played = PlayHistory.objects.filter(
            user=request.user,
            game=game
        ).first()

    context = {
        'game': game,
        'similar_games': similar_games,
        'last_played': last_played,
    }
    return render(request, 'games/game_detail.html', context)


@login_required
def play_game(request, slug):
    """اجرای بازی انتخاب‌شده"""
    game = get_object_or_404(Game, slug=slug)

    # افزایش تعداد بازی‌ها
    game.plays += 1
    game.save()

    # ثبت در تاریخچه
    PlayHistory.objects.create(user=request.user, game=game)

    # افزایش total_plays پروفایل
    try:
        profile = request.user.profile
        profile.total_plays += 1
        profile.save()
    except UserProfile.DoesNotExist:
        UserProfile.objects.create(user=request.user, total_plays=1)

    # مسیر فایل بازی
    game_file_path = os.path.join(settings.BASE_DIR, 'Game', game.game_file)

    # اجرای بازی در thread جداگانه
    def run_game():
        try:
            # روش اول: اجرا به صورت جداگانه (بهتره چون django رو block نمی‌کنه)
            subprocess.Popen([sys.executable, game_file_path])
        except Exception as e:
            print(f"Error running game: {e}")

    # اجرای بازی
    thread = threading.Thread(target=run_game)
    thread.daemon = True
    thread.start()

    messages.success(request, f"🎮 {game.title} is running ... ")
    return redirect('home')


def signup_view(request):
    """ثبت‌نام"""
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # ساخت پروفایل
            UserProfile.objects.create(user=user)
            # ورود خودکار
            login(request, user)
            messages.success(request, f"🎉 welcome {user.username}!")
            return redirect('home')
        else:
            for error in form.errors.values():
                messages.error(request, error)
    else:
        form = UserCreationForm()
    return render(request, 'games/signup.html', {'form': form})


def login_view(request):
    """ورود"""
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"👋 welcome back {user.username}!")
            return redirect('home')
        else:
            messages.error(request, "❌invalid username !")
    else:
        form = AuthenticationForm()
    return render(request, 'games/login.html', {'form': form})


def logout_view(request):
    """خروج"""
    logout(request)
    messages.success(request, "👋 goodbye !")
    return redirect('home')


@login_required
def profile_view(request):
    """صفحه‌ی پروفایل کاربر"""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=request.user)

    history = PlayHistory.objects.filter(user=request.user)[:20]

    context = {
        'profile': profile,
        'history': history,
    }
    return render(request, 'games/profile.html', context)