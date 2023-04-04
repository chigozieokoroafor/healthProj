import requests
import jwt
import datetime
# from folder.config import secret_key
import string, random
from email.message import EmailMessage
from email.mime.text import MIMEText
from mimetypes import MimeTypes
import smtplib, ssl
from email import contentmanager
from flask import request, jsonify
from functools import wraps
from jwt.exceptions import ExpiredSignatureError, DecodeError
from bson import ObjectId
from folder.config import users
from flask import render_template, render_template_string
import os
from dotenv import load_dotenv
from sendgrid.helpers.mail import Mail, Content
from sendgrid import SendGridAPIClient


load_dotenv("./.env")

# grid_key= os.getenv("grid_key")

support_mail = "okoroaforc14@gmail.com"
password = "fskrvckzpqiovmnd"

secret_key = "FBSrzPmdkaLjjahzLahmpSEUGowxSBdarIvRBbgaGtgolvQrTuVldTYMDlpUesoa"

class Authentication:
    def generate_access_token(data, minutes=60):
        exp = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
        #data["start"] = datetime.datetime.timestamp(datetime.datetime.now())
        data["exp"] = datetime.datetime.timestamp(exp)
        token = jwt.encode(data, secret_key,algorithm="HS256")
        return token
    
    def generate_otp():
        otpcode = "".join(random.choices(string.digits, k=6))
        expiry = datetime.timedelta(minutes=10.0)
        start_time = datetime.datetime.timestamp(datetime.datetime.now()) 
        stop_time = datetime.datetime.timestamp(datetime.datetime.now() + expiry)
        return {"otp":otpcode, "stoptime":stop_time, "starttime":start_time}
    
    def mailSend(email, temp, mail_title):
        # file = open("folder/templates/verification.html")
        # template = file.read().format(code=otp_code or link, support_mail="support@vbatrade.com")
            
            
        # message = Mail(
        #         from_email = "support@vbatrade.com",
        #         to_emails = email,
        #         subject = 'Email Verification Mail',
        #         html_content = Content("text/html", content=temp))
        # try:
        #     sg = SendGridAPIClient(api_key=grid_key)
        #     response = sg.send(message)
        #     if response.status_code == 202:
        #         return {"detail":"verification mail sent", "status":"success"}
        #     else:
        #         return {"detail":"error sending verification mail", "status":"fail"}
        # except Exception as e:
        #     print(e)
        #     return {"detail":"error sending verification mail", "status":"fail"}

        try:
            email_sender = support_mail
            email_password = password

            email_reciever = email
            #subject = "test"
            #file = open("other/verification.html")
            # file = open("./backend/template/verification.html")
            # subject = file.read().format(code=otp_code, support_mail=email_sender)
            
            em = MIMEText(temp,"html")
            em["From"] = email_sender
            em["To"] = email_reciever
            em["subject"] = "Test Mail"
            

            context = ssl.create_default_context()

            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
                smtp.login(email_sender, email_password)
                smtp.sendmail(email_sender, email_reciever, em.as_string())
            return {"detail":"verification mail sent", "status":"success"}
        except smtplib.SMTPAuthenticationError as e:
            return {"detail":"error sending verification mail", "status":"fail"}

    def token_required(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            bearer_token = request.headers.get("Authorization")
            
            if not bearer_token:
                return jsonify({"detail": "Token is missing","status":"error"}), 403
            try:          
                data = jwt.decode(bearer_token, secret_key,algorithms=["HS256"])
            except ExpiredSignatureError as e:
                return jsonify({"detail":"Token Expired", "status":"fail"}), 400
            except DecodeError as d:
                return jsonify({"detail":"Incorrect Token", "status":"fail"}), 400
            return f(*args, **kwargs)
        return decorated

    def generate_refresh_token(token):
        decoded = jwt.decode(token,secret_key,["HS256"])
        now = datetime.datetime.time(datetime.datetime.now())
        exp = decoded["exp"]

        difference = exp - now
        check = 0<difference<60.0

        if check is True:
            decoded.pop("exp")
            t = Authentication.generate_access_token(decoded)
            return t
        return ""

# class Authentication:
#     def generate_access_token(data, minutes=60):
#         exp = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
#         #data["start"] = datetime.datetime.timestamp(datetime.datetime.now())
#         data["exp"] = datetime.datetime.timestamp(exp)
#         token = jwt.encode(data, secret_key,algorithm="HS256")
#         return token
    
#     def generate_otp():
#         otpcode = "".join(random.choices(string.digits, k=4))
#         expiry = datetime.timedelta(minutes=5.0)
#         start_time = datetime.datetime.timestamp(datetime.datetime.now()) 
#         stop_time = datetime.datetime.timestamp(datetime.datetime.now() + expiry)
#         return {"otp":otpcode, "stoptime":stop_time, "starttime":start_time}
    
#     def mailSend(email, otp_code=None, link=None):
#         file = open("folder/templates/verification.html")
#         template = file.read().format(code=otp_code or link, support_mail="trademanager.com")
            
            
#         message = Mail(
#                 from_email = email_sender, #'Boxin@boxin.ng',
#                 to_emails = email,
#                 subject = 'Email Verification Mail',
#                 html_content = Content("text/html", content=template))
#         try:
#             sg = SendGridAPIClient(api_key=grid_key)
#             response = sg.send(message)
#             if response.status_code == 202:
#                 return {"detail":"verification mail sent", "status":"success"}
#             else:
#                 return {"detail":"error sending verification mail", "status":"fail"}
#         except Exception as e:
#             return {"detail":"error sending verification mail", "status":"fail"}

#     def token_required(f):
#         @wraps(f)
#         def decorated(*args, **kwargs):
#             bearer_token = request.headers.get("Authorization")
            
#             if not bearer_token:
#                 return jsonify({"detail": "Token is missing","status":"error"}), 403
#             try:          
#                 data = jwt.decode(bearer_token, secret_key,algorithms=["HS256"])
#             except ExpiredSignatureError as e:
#                 return jsonify({"detail":"Token Expired", "status":"fail"}), 400
#             except DecodeError as d:
#                 return jsonify({"detail":"Incorrect Token", "status":"fail"}), 400
#             return f(*args, **kwargs)
#         return decorated


#     def tokenExpCheck(exp:float, data:dict):
#         now = datetime.datetime.now()

#         #convert exp to datetime
#         exp_date = datetime.datetime.fromtimestamp(exp)

#         diff =  exp_date - now
        
#         if diff.total_seconds() < 300:
            
#             user_data = users.find_one({"_id":ObjectId(data["id"])})
#             token = ""
#             if user_data != None:
#                 roles = ["base_user"]
#                 if user_data["trade_manager"] == True:
#                     roles = ["manager"]

#                 new_exp = datetime.datetime.now() + datetime.timedelta(minutes=60)
#                 data["exp"] = datetime.datetime.timestamp(new_exp)
#                 data["role"] = roles
#                 token = Authentication.generate_access_token(data)

#         else:
#             token = ""
        
#         return token

