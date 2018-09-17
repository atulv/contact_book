from django.db import models
from django.contrib.auth.models import User

class UserProfile(models.Model):
    user = models.OneToOneField('auth.User', unique=True, related_name='profile')
    name = models.CharField(max_length=50)
    email = models.CharField(max_length=50, unique=True)
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)

class ContactBook(models.Model):
    email = models.CharField(max_length=50, unique=True)
    info = models.TextField()
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    modified_on = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey('UserProfile', related_name='+')
    
     
