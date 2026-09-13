from django.db import models
from django.contrib.auth.models import User


class Game(models.Model):
    """مدل بازی‌ها"""
    title = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    cover_image = models.CharField(max_length=200, help_text="نام فایل عکس مثل 1.png")
    game_file = models.CharField(max_length=200, help_text="نام فایل پایتون مثل neon_racer.py")
    order = models.IntegerField(default=0, help_text="ترتیب نمایش")
    plays = models.IntegerField(default=0, help_text="تعداد بازی‌ها")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title

    def get_cover_url(self):
        return f"/media/images/{self.cover_image}"


class UserProfile(models.Model):
    """پروفایل کاربر"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    avatar_color = models.CharField(max_length=20, default='#00e6ff')
    total_plays = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class PlayHistory(models.Model):
    """تاریخچه‌ی بازی‌های انجام‌شده"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='play_history')
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    played_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-played_at']

    def __str__(self):
        return f"{self.user.username} played {self.game.title}"