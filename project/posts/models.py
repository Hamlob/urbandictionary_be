from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    def __str__(self):
        return self.username

class Post(models.Model):

    post_title = models.CharField(max_length = 255)
    post_text = models.CharField(max_length = 10000)
    post_example = models.CharField(max_length = 10000)
    publish_date = models.DateTimeField("date published")
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    upvotes = models.PositiveIntegerField(default=0)
    downvotes = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.post_title

class PostUnverified(models.Model):
    post_title = models.CharField(max_length = 255)
    post_text = models.CharField(max_length = 10000)
    post_example = models.CharField(max_length = 10000)
    author = models.ForeignKey(User, on_delete=models.CASCADE, null=True)
    verification_token = models.CharField(max_length=50) #uuid =36chars
    
class UserVerificationToken(models.Model):
    value = models.CharField(max_length=50)
    user = models.ForeignKey(User, on_delete=models.CASCADE)