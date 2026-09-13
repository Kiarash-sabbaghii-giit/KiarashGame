from django.db import models
from django.contrib.auth.models import User


class Game(models.Model):
    title = models.CharField(max_length=100)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    cover_image = models.CharField(
        max_length=200,
        help_text="Image filename e.g. 1.png"
    )
    demo_gif = models.CharField(
        max_length=200,
        blank=True,
        help_text="Demo GIF filename e.g. demo1.gif (in media/images/)"
    )
    game_file = models.CharField(
        max_length=200,
        help_text="Python filename e.g. neon_racer.py"
    )
    order = models.IntegerField(default=0)
    plays = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title

    def get_cover_url(self):
        return f"/media/images/{self.cover_image}"

    def get_demo_url(self):
        if self.demo_gif:
            return f"/media/images/{self.demo_gif}"
        return self.get_cover_url()


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    total_plays = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"


class PlayHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='play_history')
    game = models.ForeignKey(Game, on_delete=models.CASCADE)
    played_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-played_at']

    def __str__(self):
        return f"{self.user.username} played {self.game.title}"