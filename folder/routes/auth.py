from urllib.robotparser import RequestRate
from flask import Blueprint, Response, jsonify, request, url_for, render_template_string, redirect, render_template, flash
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
# from flask_mail import Mail, Message


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
    temp = render_template("reset_mail.html", action_url=link)
    try :
        mail_send = Authentication.mailSend(email, temp)
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

    email_check = users.find({"email":email})
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

@auth.route("/emailVerification", methods=["POST"])
def email_verification():
    email = request.json.get("email")
    users.update_one({"email":email}, {"$set":{"verified":False}})
    token = s.dumps(email, salt="email_confirm")
    url = url_for("auth.confirm_email", token=token, _external=True)
    temp = render_template("reset_mail.html", action_url=url) 
    # link = url_for("auth.confirm_email", token=token, _external=True)
    st = Authentication.mailSend(email, str(temp))
    if st["status"] == "success":
        return jsonify({"detail":"use verification link sent to mail provided", "success":True}), 200
    else:
        return jsonify({"detail":"there was an error while sending verification mails, check back later", "success":False}), 400 
 


@auth.route("/confirm_email/<token>")
def confirm_email(token):
    try:
        email = s.loads(token, salt="email_confirm", max_age=300 )
        
        user = users.find_one({"email":email})
        if  user["first_timer"]== True:
            # user would be redirected to an email verification successful page
            users.find_one_and_update({"email":email},{"$set":{"verified":True}})
            return redirect("https://github.com"), 302 # change this
        else:
            url = url_for("auth.resPass", token=token, _external=True)
            return render_template("pwd_reset.html", post_url=url),  200
            # user would be redirected to password reset page
        
            
    except SignatureExpired:
        return render_template_string("<h1> link expired </h1>")


@auth.route("/postPassword", methods=["POST"])
def resPass():
    if request.method == "POST":
        token = request.args.get("token")
        email = s.loads(token, salt="email_confirm", max_age=300 )
        password = request.form.get("newPassword")
        hashed_pwd = generate_password_hash(password, "pbkdf2:sha256")
        users.update_one({"email":email}, {"$set":{"pwd":hashed_pwd, "verified":True}})
        #email = request.form.get("ema")
        return redirect("https://github.com"), 302