from django.contrib import admin
from posts.models import *

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    pass

@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    pass

@admin.register(PostUnverified)
class PostUnverifiedAdmin(admin.ModelAdmin):
    pass

@admin.register(UserVerificationToken)
class UserVerificationTokenAdmin(admin.ModelAdmin):
    pass