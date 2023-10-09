import datetime
import jwt


from .models import User
from rest_framework.authentication import BaseAuthentication
from rest_framework import exceptions
from django.conf import settings

class SafeJWTAuthentication(BaseAuthentication):
    '''
        custom authentication class for DRF and JWT
        https://github.com/encode/django-rest-framework/blob/master/rest_framework/authentication.py
    '''

    def authenticate(self, request):
        authorization_header = request.headers.get('Authorization')
        if not authorization_header:
            raise exceptions.AuthenticationFailed("Auth token not provided.")
        try:
            access_token = authorization_header.split(' ')[1]
            payload = jwt.decode(access_token, settings.ENCRYPTION_SECRET_KEYSTRING, algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            raise exceptions.AuthenticationFailed('access_token expired')
        except IndexError:
            raise exceptions.AuthenticationFailed('Token prefix missing')
        except jwt.InvalidSignatureError:
            raise exceptions.AuthenticationFailed('token verification failed')

        user = User(id=payload['user_id'])
        if user is None:
            raise exceptions.AuthenticationFailed('User not found')

        return (user, None)


def generate_access_token(user):

    access_token_payload = {
        'user_id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=90, minutes=5),
        'iat': datetime.datetime.utcnow(),
    }
    access_token = jwt.encode(access_token_payload, settings.ENCRYPTION_SECRET_KEYSTRING, algorithm='HS256')
    return access_token


def generate_refresh_token(user):
    refresh_token_payload = {
        'user_id': user.id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(days=90),
        'iat': datetime.datetime.utcnow()
    }
    refresh_token = jwt.encode(
        refresh_token_payload, settings.ENCRYPTION_SECRET_KEYSTRING, algorithm='HS256')

    return refresh_token





