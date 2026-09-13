from django.contrib import admin
from .models import Game, UserProfile, PlayHistory


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    list_display = ('order', 'title', 'slug', 'game_file', 'cover_image', 'demo_gif', 'plays')
    list_editable = ('plays',)
    search_fields = ('title',)
    prepopulated_fields = {'slug': ('title',)}


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'total_plays', 'created_at')


@admin.register(PlayHistory)
class PlayHistoryAdmin(admin.ModelAdmin):
    list_display = ('user', 'game', 'played_at')
    list_filter = ('game', 'user')