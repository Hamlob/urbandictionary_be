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



    
