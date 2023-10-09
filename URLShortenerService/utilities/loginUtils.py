from URLShortener.settings import SENDER, APP_PASSWORD
from ..models import OTP
from ..serializer import *
# from serializer import OTPMobileSerializer, OTPEmailSerializer
import random
import logging
from email_validator import validate_email, EmailNotValidError
from django.utils import timezone
from datetime import timedelta
import smtplib
from email.message import EmailMessage

logger = logging.getLogger('django')

def generate_otp():
	otp = random.randint(1000, 9999)
	return otp

 
def is_email_valid(email):
    try:
      # validate and get info
        v = validate_email(email) 
        # replace with normalized form
        email = v["email"]  
        return True
    except EmailNotValidError as e:
        # email is not valid, exception message is human-readable
        logger.error(str(e))
        return False

def send_otp_email(recipient):
    otp = generate_otp()
    
    str_message = 'Greetings from URLShortener. Your OTP verification code is ' + str(otp)      
    try:
        msg = EmailMessage()
        msg.set_content(str_message)
        msg['Subject'] = 'Verify OTP'
        msg['From'] = SENDER
        msg['To'] = recipient
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(SENDER, APP_PASSWORD)
        server.send_message(msg)
        server.quit()
        print("Email sent! Message ID:"+" to: "+str(recipient))
    except Exception as e:
        return False, str(e)

    otp_serializer_input = {}
    otp_serializer_input["otp"] = otp
    otp_serializer_input["email"] = recipient
    otp_serializer_input["expiration_time"] = timezone.localtime(timezone.now()) + timedelta(minutes=15)

    otp_instance_exists = OTP.objects.filter(email=recipient).exists()
    if otp_instance_exists:
        otp_instance = OTP.objects.filter(email=recipient).first()
        otp_serializer = OTPEmailSerializer(instance=otp_instance, data=otp_serializer_input)
    else:
        otp_serializer = OTPEmailSerializer(data=otp_serializer_input)

    if otp_serializer.is_valid():
        otp_serializer.save()
        logger.info("OTP = "+str(otp)+" for email = "+str(recipient)+" has been saved.")
    else:
        logger.error("Errors in OTP serialization for person with email = "+str(recipient)+" - "+str(otp_serializer.errors))
    
    return str_message