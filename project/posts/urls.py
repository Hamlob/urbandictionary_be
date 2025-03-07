from django.urls import include, path
from django.contrib.auth.views import LoginView, LogoutView

from . import views

urlpatterns = [
    path('', views.feed, name = 'feed'),
    path('random/', views.random, name = 'random'),
    path('create_post/', views.create_post, name = 'create_post'),
    path('login/', views.login, name = 'login'),
    path('logout/', views.logout, name = 'logout'),
    path('register/', views.register, name = 'register'),
    path('account/', views.account, name = 'account'),
]