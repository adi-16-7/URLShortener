from rest_framework import serializers
from .models import *

class UserEmailLoginSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = User
        fields = ('id', 'name', 'email')

class OTPEmailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTP
        fields = ('id', 'email', 'otp', 'expiration_time')

class ValidationOTPSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTP
        fields = ('id', 'email', 'otp')


class ShortURLSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    class Meta:
        model = ShortURL
        fields = '__all__'

class ShortURLAccessSerializer(serializers.ModelSerializer):
    short_url = serializers.PrimaryKeyRelatedField(queryset=ShortURL.objects.all())
    class Meta:
        model = ShortURLAccess
        fields = '__all__'

class ShortURLAccessRelatedSerializer(serializers.ModelSerializer):
    # short_url = serializers.PrimaryKeyRelatedField(queryset=ShortURL.objects.all())
    class Meta:
        model = ShortURLAccess
        fields = ('id', 'ip_address', 'user_agent', 'access_time')

class ShortURLDetailSerializer(serializers.ModelSerializer):
    usage = ShortURLAccessRelatedSerializer(many=True)
    user = serializers.PrimaryKeyRelatedField(queryset=User.objects.all())
    class Meta:
        model = ShortURL
        fields = '__all__'