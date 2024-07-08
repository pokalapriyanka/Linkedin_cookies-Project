from django.db import models

# Create your models here.

# Create your models here.
class Message(models.Model):
    profile_name = models.CharField(max_length=255)
    emails = models.TextField()
    phones = models.TextField()
    links = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.profile_name