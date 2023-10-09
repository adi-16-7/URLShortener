from django.db import models
from django.db.models.fields import BooleanField, CharField, DateField, DateTimeField, IntegerField
from django.db.models.fields.related import ForeignKey

# Create your models here.
class User(models.Model):
    name = CharField(max_length=255, null=True)
    email = CharField(max_length = 255, null=True, unique=True)

class OTP(models.Model):
    email = CharField(max_length = 255, null=True, unique=True)
    otp = IntegerField()
    expiration_time = DateTimeField()

class ShortURL(models.Model):
    original_url = CharField(max_length = 255, null=True)
    shortened_url = CharField(max_length = 255, null=True)
    expiration_timestamp = DateTimeField()
    user = ForeignKey(User, on_delete=models.CASCADE, related_name='urls')
    max_usage = IntegerField()
    uuid = CharField(max_length = 255, null=True, unique=True)

    class Meta:
        unique_together = ('original_url', 'user')

class ShortURLAccess(models.Model):
    ip_address = CharField(max_length = 255, null=True)
    user_agent = CharField(max_length = 255, null=True)
    access_time = DateTimeField()
    short_url = ForeignKey(ShortURL, on_delete=models.CASCADE, related_name='usage')
    
