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
from flask import request, jsonify, render_template
from functools import wraps
from jwt.exceptions import ExpiredSignatureError, DecodeError
from bson import ObjectId
from folder.config import users, misc
# from flask import render_template, render_template_string
import os
from dotenv import load_dotenv
from sendgrid.helpers.mail import Mail, Content
from sendgrid import SendGridAPIClient
from werkzeug.security import generate_password_hash



load_dotenv("./.env")

# grid_key= os.getenv("grid_key")

support_mail = "okoroaforc14@gmail.com"
password = "ecmhllyxrchptmqo"

secret_key = "FBSrzPmdkaLjjahzLahmpSEUGowxSBdarIvRBbgaGtgolvQrTuVldTYMDlpUesoa"

class Authentication:
    
    def generate_access_token(data, minutes=60):
        exp = datetime.datetime.now() + datetime.timedelta(minutes=minutes)
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
            em["subject"] = mail_title
            

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
                return jsonify({"message": "Token is missing","success":True}), 403
            try:          
                data = jwt.decode(bearer_token, secret_key,algorithms=["HS256"])
            except ExpiredSignatureError as e:
                return jsonify({"message":"Token Expired", "success":False}), 400
            except DecodeError as d:
                return jsonify({"message":"Incorrect Token", "success":False}), 400
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

    def tokenExpCheck(exp:float, data:dict):
        now = datetime.datetime.now()

        #convert exp to datetime
        exp_date = datetime.datetime.fromtimestamp(exp)

        diff =  exp_date - now
        
        if diff.total_seconds() < 300:
            
            user_data = users.find_one({"_id":ObjectId(data["id"])})
            token = ""
            if user_data != None:
                roles = user_data["role"]

                new_exp = datetime.datetime.now() + datetime.timedelta(minutes=60)
                data["exp"] = datetime.datetime.timestamp(new_exp)
                data["role"] = roles
                token = Authentication.generate_access_token(data)

        else:
            token = ""
        
        return token

def gen_tag():
    key = "JOB_"+ "".join(random.choices(string.ascii_letters, k=6))
    return key

# turn this to a cron job later on.
def create_admin_key():
    def mailSend(email,admin_key, mail_title):
        try:
            email_sender = "okoroaforc14@gmail.com"
            email_password = "ecmhllyxrchptmqo"

            email_reciever = email
            template_folder = os.getcwd() + "/folder/templates/admin_mail.html"
            # file = open("./templates/admin_mail.html")
            file = open(template_folder)
            mail = file.read().format(code=admin_key, support_mail=email_sender, date=datetime.datetime.utcnow().year)
            
            em = MIMEText(mail,"html")
            em["From"] = email_sender
            em["To"] = email_reciever
            em["subject"] = "Updated Admin Key"
            

            context = ssl.create_default_context()

            with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
                smtp.login(email_sender, email_password)
                smtp.sendmail(email_sender, email_reciever, em.as_string())
            return {"detail":"verification mail sent", "status":"success"}
        except smtplib.SMTPAuthenticationError as e:
            return {"detail":"error sending verification mail", "status":"fail"}
        
    key = "".join(random.choices(string.ascii_uppercase, k=3)) + "".join(random.choices(string.digits, k=4))
    hashed_password =  generate_password_hash(key, method="pbkdf2:sha256", salt_length=32)
    check = misc.find_one({"tag":"admin_key"})
    mailSend("okoroaforc14@gmail.com",key ,"Update key") # to always send me the key incase of issues.
    cursor = users.find({"role":"admin"})
    admins_ = list(cursor)
    if len(admins_)>0:
        for i in admins_ :
            mailSend(i["email"],key ,"Update key")
    if check == None:
        
            misc.insert_one({"tag":"admin_key", "key":hashed_password})

    else:
        misc.update_one({"tag":"admin_key"}, {"$set":{"key":hashed_password}})
        