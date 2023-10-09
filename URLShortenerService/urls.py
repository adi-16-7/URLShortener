from django.urls.conf import path

from .views import *

urlpatterns = [
    path('signin/', SignIn.as_view()),
    path('signup/', SignUp.as_view()),
    path('validate/', OTPValidation.as_view()),
    path('shorten', Shortener.as_view()),
    path('open', Opener.as_view()),
    path('url-list', ShortURLList.as_view()),
    # path('redeploy', Redeploy.as_view(), name="redeploy")

]