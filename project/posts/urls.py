from django.urls import include, path
from django.contrib.auth.views import LoginView, LogoutView

from . import views

urlpatterns = [
    path('', views.feed, name = 'feed'),
    path('random_post/', views.random_post, name = 'random_post'),
    path('create_post/', views.create_post, name = 'create_post'),
    path('verify_post/<str:token>/', views.verify_post, name = 'verify_post'),
    path('login/', views.login, name = 'login'),
    path('logout/', views.logout, name = 'logout'),
    path('register/', views.register, name = 'register'),
    path('verify_user/<str:token>/', views.verify_user, name = 'verify_user'),
    path('account/', views.account, name = 'account'),
    path('change_password/', views.change_password, name = 'change_password'),
    path('user_posts/', views.user_posts, name = 'user_posts'),
    path('search/', views.search, name = 'search'),
    path('<int:post_id>/react/', views.toggle_reaction, name='toggle_reaction')
]