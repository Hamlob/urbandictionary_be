from django.contrib import admin
from posts.models import *

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ('post_title', 'author', 'publish_date')

@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'is_active', 'date_joined')

@admin.register(PostUnverified)
class PostUnverifiedAdmin(admin.ModelAdmin):
    list_display = ('post_title', 'author')

@admin.register(UserVerificationToken)
class UserVerificationTokenAdmin(admin.ModelAdmin):
    list_display = ('user',)

@admin.register(BlockedEmailDomain)
class BlockedEmailDomainAdmin(admin.ModelAdmin):
    pass

@admin.register(SpamRegEx)
class SpamRegExAdmin(admin.ModelAdmin):
    list_display = ('pattern', 'description')
