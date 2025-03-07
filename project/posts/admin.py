from django.contrib import admin
from posts.models import Post, User

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    pass

@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    pass