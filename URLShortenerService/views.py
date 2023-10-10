from django.http import JsonResponse
from django.shortcuts import render
from django.db import transaction
from django.utils import timezone
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.generics import GenericAPIView, ListCreateAPIView, ListAPIView
from email_validator import validate_email, EmailNotValidError
import logging
import pyshorteners
import re
from datetime import timedelta, datetime
import uuid
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
import pytz
from django.shortcuts import redirect
import boto3
from django.conf import settings


from .models import *
from .serializer import *
from .utilities.loginUtils import send_otp_email, is_email_valid
from .jwtAuth import generate_access_token, generate_refresh_token
from .scheme import SafeTokenScheme


# Create your views here.

logger = logging.getLogger('django')
BASE_URL = settings.BASE_URL

class SpecAPIView(SpectacularAPIView):
    permission_classes = ([AllowAny])
    authentication_classes = []

class SpecSwaggerView(SpectacularSwaggerView):
    permission_classes = ([AllowAny])
    authentication_classes = []

class SignIn(GenericAPIView):
    queryset = User.objects.all()
    serializer_class = UserEmailLoginSerializer
    permission_classes = ([AllowAny])
    authentication_classes = []

    def put(self, request):
        with transaction.atomic():
            data = request.data
            email = data.get("email", None)

            if is_email_valid(email):
                user_exists = User.objects.filter(email=email).exists()
                if not user_exists:
                    return Response({"error": f"User account doesn't exist with email - {email}"}, status=status.HTTP_403_FORBIDDEN)
                
                user_instance = User.objects.filter(email=email).first()
                customer_serializer = UserEmailLoginSerializer(instance=user_instance)
                output = {}
                output["id"] = customer_serializer.data.get("id")
                output["login_status"] = True
                output["message"] = "OTP sent successfully"

                save_send_otp = send_otp_email(email)
                if isinstance(save_send_otp, tuple):
                    return Response(save_send_otp[1], status=status.HTTP_400_BAD_REQUEST)
                return Response(output, status=status.HTTP_200_OK)
            return Response({"error": f"Not a valid email id - {email}"}, status=status.HTTP_400_BAD_REQUEST)
            
     
class SignUp(GenericAPIView):
    queryset = User.objects.all()
    serializer_class = UserEmailLoginSerializer
    permission_classes = ([AllowAny])
    authentication_classes = []

    def post(self, request):
        with transaction.atomic():
            data = request.data
            email = data.get("email", None)
            if is_email_valid(email):
                user_exists = User.objects.filter(email=email).exists()
                if user_exists:
                    return Response({"error": f"Please SignIn, user account already exists with this email - {email}"}, status=status.HTTP_400_BAD_REQUEST)
                
                user_serializer = UserEmailLoginSerializer(data=data)
                if user_serializer.is_valid():
                    user_serializer.save()
                    save_send_otp = send_otp_email(email)
                    if isinstance(save_send_otp, tuple):
                        return Response(save_send_otp[1], status=status.HTTP_400_BAD_REQUEST)
                    output = user_serializer.data
                    output['mesage'] = "OTP sent successfully"
                    return Response(output, status=status.HTTP_200_OK)
                else:
                    return Response(user_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({"error": f"Not a valid email id - {email}"}, status=status.HTTP_400_BAD_REQUEST)
            

class OTPValidation(GenericAPIView):
    queryset = OTP.objects.all()
    serializer_class = ValidationOTPSerializer
    permission_classes = ([AllowAny])
    authentication_classes = []

    def put(self, request):
        data = request.data
        email = data.get("email")
        otp = data.get("otp")

        otp_bool = OTP.objects.filter(
            email=email, otp=otp,
            expiration_time__gt=timezone.localtime(timezone.now())
        ).exists()

        output = {}
        if otp_bool:
            user = User.objects.filter(email=email).first()
            access_token = generate_access_token(user)
            refresh_token = generate_refresh_token(user)
            output['refresh_token'] = refresh_token
            output['access_token'] = access_token
            output['status'] = True
            output['email'] = user.email
            return Response(output, status=status.HTTP_200_OK)
        else:
            logger.error("OTP boolean = "+str(otp_bool))
            output['status'] = False
            return Response(output, status=status.HTTP_401_UNAUTHORIZED)
                

class Shortener(GenericAPIView):
    queryset = ShortURL.objects.all()
    serializer_class = ShortURLSerializer

    def post(self, request):
        expiration_type = request.GET.get('expiration_type', '')
        data = request.data
        if data['max_usage'] <=0:
            return Response({"error": "max_usage should be greater than 0"}, status=status.HTTP_400_BAD_REQUEST)
        
        if expiration_type=='duration':
            pattern = r'(?:(\d+)\s*days?)?\s*(?:(\d+)\s*hours?)?\s*(?:(\d+)\s*minutes?)?\s*(?:(\d+)\s*seconds?)?'
            matches = re.match(pattern, data['expiration'])
            if matches:
                days = int(matches.group(1) or 0)
                hours = int(matches.group(2) or 0)
                minutes = int(matches.group(3) or 0)
                seconds = int(matches.group(4) or 0)
                expiration_time = timezone.localtime(timezone.now()) + timedelta(days=days, hours=hours, minutes=minutes, seconds=seconds)
            else:
                return Response({"message": "The given duration input is not in proper format."}, status=status.HTTP_400_BAD_REQUEST)
        elif expiration_type=='absolute':
            try:
                expiration_time = datetime.strptime(data['expiration'], "%Y-%m-%d %H:%M:%S").replace(tzinfo=pytz.timezone('Asia/Kolkata'))
            except ValueError as e:
                return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response({"error": "The provided expiration_type is not supported."}, status=status.HTTP_400_BAD_REQUEST)
        
        user_id = request.user.pk
        short_url_serializer_input = {}
        short_url_serializer_input['user'] = user_id
        short_url_serializer_input['max_usage'] = data['max_usage']
        short_url_serializer_input['original_url'] = data['original_url']
        if timezone.localtime(timezone.now()) + timedelta(hours=1) <= expiration_time <= timezone.localtime(timezone.now()) + timedelta(days=365):
            short_url_serializer_input['expiration_timestamp'] = expiration_time
        else:
            return Response({"error": "The expiration time of the url should lie between 1 hour to 1 year from current time."}, status=status.HTTP_400_BAD_REQUEST)

        link_uuid = uuid.uuid4()

        long_url = BASE_URL+'us_svc/open?uuid='+str(link_uuid)
        type_tiny = pyshorteners.Shortener()
        print(long_url)
        short_url = type_tiny.clckru.short(long_url)
        short_url_serializer_input['shortened_url'] = short_url
        short_url_serializer_input['uuid'] = str(link_uuid)
        short_url_serializer = ShortURLSerializer(data=short_url_serializer_input)
        if short_url_serializer.is_valid():
            short_url_serializer.save()
            return Response(short_url_serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(short_url_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        

class Opener(GenericAPIView):
    queryset = ShortURL.objects.all()
    serializer_class = ShortURLSerializer
    permission_classes = ([AllowAny])
    authentication_classes = []

    def get(self, request):
        with transaction.atomic():
            uuid = request.GET.get('uuid')
            try:
                short_url_instance = ShortURL.objects.select_for_update(skip_locked=True).get(uuid=uuid)
            except ShortURL.DoesNotExist:
                return Response({"error": "The url requested is either being accessed parallely or does not exist in the database."}, status=status.HTTP_404_NOT_FOUND)
            
            if short_url_instance:
                if timezone.localtime(timezone.now())<=short_url_instance.expiration_timestamp:
                    if short_url_instance.max_usage > short_url_instance.usage.count():
                        access_input = {}
                        ip_string = request.META.get('HTTP_X_FORWARDED_FOR')
                        if ip_string:
                            ip_address = ip_string.split(',')[0]
                        else:
                            ip_address = request.META.get('REMOTE_ADDR')
                        
                        access_input['ip_address'] = ip_address
                        access_input['user_agent'] = request.META['HTTP_USER_AGENT']
                        access_input['access_time'] = timezone.localtime(timezone.now())
                        access_input['short_url'] = short_url_instance.id
                        access_serializer = ShortURLAccessSerializer(data=access_input)
                        if access_serializer.is_valid():
                            access_serializer.save()
                            return redirect(short_url_instance.original_url, 302)
                        else:
                            return JsonResponse(access_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
                    else:
                        return JsonResponse({"error": "The max number of accesses has reached."}, status=status.HTTP_404_NOT_FOUND)
                else:
                    return JsonResponse({"error": "The url has expired."}, status=status.HTTP_404_NOT_FOUND)
            else:
                return JsonResponse({"error": "The url requested is invalid"}, status=status.HTTP_404_NOT_FOUND)


class ShortURLList(GenericAPIView):
    queryset = ShortURL.objects.all()
    serializer_class = ShortURLDetailSerializer

    def get(self, request):
        user_id = request.user.pk
        user_instance = User.objects.get(pk=user_id)
        short_urls = user_instance.urls
        short_url_serializer = ShortURLDetailSerializer(short_urls, many=True)
        return Response(short_url_serializer.data, status=status.HTTP_200_OK)

class Redeploy(GenericAPIView):
    permission_classes = ([AllowAny])
    authentication_classes = []

    def post(self, request):
        # Configure your AWS credentials and region
        aws_access_key_id = request.data['aws_access_key_id']
        aws_secret_access_key = request.data['aws_secret_access_key']
        aws_region = 'ap-south-1'

        # Create a client for AWS CodePipeline
        client = boto3.client('codepipeline', 
                            aws_access_key_id=aws_access_key_id, 
                            aws_secret_access_key=aws_secret_access_key, 
                            region_name=aws_region)

        # Specify the pipeline name and optional clientRequestToken
        pipeline_name = 'urlshortener-new'

        # Start the pipeline execution
        response = client.start_pipeline_execution(
            name=pipeline_name
        )
        return Response({"message": "Deployment completed."})

    


            
            


