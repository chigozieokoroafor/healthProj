from urllib.robotparser import RequestRate
from flask import Blueprint, Response, jsonify, request, url_for, render_template_string, redirect, render_template
import pymongo
from folder.config import users
from folder.functions import Authentication, secret_key
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo.errors import DuplicateKeyError
import jwt, bson, datetime,random, secrets
from bson.errors import InvalidId
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from bson import ObjectId
import os
from flask_mail import Mail, Message


template_folder = os.getcwd() + "/folder/templates"

auth = Blueprint("auth", __name__, url_prefix="/api", template_folder=template_folder)
s = URLSafeTimedSerializer(secret_key)
# mail = Mail(auth)




@auth.route("/createAccount", methods=["POST"])
def signup():
    info = request.json
    keys = [i for i in info.keys()]
    data = {}
    for i in keys:
        data[i] = info.get(i)
    try:
        email = data["email"]
        password = data["password"]
    except KeyError as e:
        return {"detail":f"{str(e)} field missing or empty", "success":False}, 400

    pwd_hashed = generate_password_hash(password, salt_length=32)
    data["pwd"] = pwd_hashed
    data["verified"] = False
    data["role"] = ["patient"]
    data["timestamp"] = datetime.datetime.now()
    data["first_timer"] = True

    data.pop("password")
    token = s.dumps(email, salt="email_confirm")
    link = url_for("auth.confirm_email", token=token, _external=True)
    try :
        mail_send = Authentication.sendMail(email, link)
        if mail_send["status"] == "success":
            users.insert_one(data)
        else:
            return jsonify({"detail":"Error occured while creating account","success":False}), 400
        #users.find_one_and_update({"email":email}, {"$set":{"otp_data":otp_data}})
        
    except DuplicateKeyError as e:
        return jsonify({"detail":"Email address already used","success":False}), 400
    return jsonify(detail="account created successfully", success=True, verified=False), 200


@auth.route("/emailCheck", methods=["POST"])
def emailCheck():
    email = request.json.get("email")

    email_check = users.find({"email":email}).hint("email_1")
    enail_list = list(email_check)
    if len(enail_list) > 0:
        message = jsonify({"detail":"Email address already used.", "success":False}), 400
        return message
    message = jsonify({"detail":"Email address can be used.","success":True}),200
    return message

@auth.route("/signin", methods=["POST"])
def signin():
    info = request.json
    email = info.get("email")
    password = info.get("password")
    user_check = users.find_one({"email":email})
    
    if user_check != None :
        user = user_check
        pwd_check = check_password_hash(user["pwd"], password)
        if pwd_check:
            user_id = str(bson.ObjectId(user["_id"]))
            d = {"id": user_id, "u_type":user["role"]}
            token = Authentication.generate_access_token(d)
            user["token"] = token
            users.update_one({"_id":user["_id"]}, {"$set":{"first_timer":False}})
            user.pop("_id")
            user.pop("pwd")
            
            return jsonify({"detail":user, "success":True}), 200
        return jsonify({"detail":"Email and password do not match", "success":False}), 401
        
    return jsonify({"detail": f"Account not found for {email}", "success":False}), 404

# @auth.route("/sendOTP", methods=["POST"])
# def send_otp():
#     email = request.json.get("email")
#     email_check = users.find({"email":email}).hint("email_1")
#     email_list = list(email_check)
#     if len(email_list) > 0:
#         otp_data = Authentication.generate_otp()
#         users.find_one_and_update({"email":email}, {"$set":{"otp_data":otp_data}})
#         mail_send = Authentication.sendMail(email, otp_data["otp"])
#         if mail_send["status"]=="success":
#             return jsonify({"detail":"OTP sent", "success":True}), 200
#         else:
#             return jsonify({"detail":"Error occured while sending mail","success":False}),400

#     return jsonify({"detail":"Account with provided email not found", "success":False}), 404

@auth.route("/emailVerification", methods=["POST"])
def email_verification():
    email = request.json.get("email")
    users.update_one({"email":email}, {"$set":{"verified":False}})
    # token = s.dumps(email, salt="email_confirm")
    # msg = Message()
    # msg.subject = "Email Verification"
    # msg.recipients = [email]
    # # msg.sender = 'username@gmail.com'
    # url = render_template("reset_mail", action_url="https://postmarkapp.com/transactional-email-templates/reset-password") 
    # msg.body = url
    # mail.send(msg)
    
    url = render_template("reset_mail.html", action_url="https://postmarkapp.com/transactional-email-templates/reset-password") 
    # link = url_for("auth.confirm_email", token=token, _external=True)
    s = Authentication.mailSend(email, str(url))
    if s["status"] == "success":
        return jsonify({"detail":"use verification link sent to mail provided", "success":True}), 200
    else:
        return jsonify({"detail":"there was an error while sending verification mails, check back later", "success":False}), 400 
 

@auth.route("/updatePassword", methods=["POST"])
@Authentication.token_required
def newPassword():
    token = request.headers.get("Authorization")
    data = jwt.decode(token, secret_key,algorithms=["HS256"])    
    new_password = request.json.get("newPassword")
    #data["newPassword"] = new_password
    try:
        email = data["email"]
    except KeyError as e:
        return jsonify({"detail":"Incorrect token provided", "success":False}), 401
    user_cursor = users.find({"email":email}).hint("email_1")
    user_list = list(user_cursor)
    user = user_list[0]
    choice_length = random.choice([16,32,64])
    new_hash = generate_password_hash(new_password,salt_length=choice_length)
    users.find_one_and_update({"_id":user["_id"]}, {"$set":{"pwd":new_hash}})
    
    return jsonify({"detail":"Password Updated Successfully", "success":True}), 200

@auth.route("/confirm_email/<token>")
def confirm_email(token):
    try:
        email = s.loads(token, salt="email_confirm", max_age=300 )
        log_key = secrets.token_hex(32)
        user = users.find_one({"email":email})
        if  user["first_timer"]== True:
            # user would be redirected to an email verification successful page
            users.find_one_and_update({"email":email},{"$set":{"verified":True}})
            return render_template_string("<h1> success </h1>"), 200
        else:
            return render_template("reset_mail", action_url="https://postmarkapp.com/transactional-email-templates/reset-password") 
            # user would be redirected to password reset page
        
            
    except SignatureExpired:
        return render_template_string("<h1> link expired </h1>")

@auth.route("passwordReset")
def passwordRes():
    render_template()