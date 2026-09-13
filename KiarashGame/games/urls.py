from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('game/<slug:slug>/', views.game_detail, name='game_detail'),  # ← جدید
    path('play/<slug:slug>/', views.play_game, name='play_game'),
    path('signup/', views.signup_view, name='signup'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
]