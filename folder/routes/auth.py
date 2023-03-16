from urllib.robotparser import RequestRate
from flask import Blueprint, Response, jsonify, request, url_for, render_template_string, redirect
import pymongo
from folder.config import users
from folder.functions import Authentication, secret_key
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo.errors import DuplicateKeyError
import jwt, bson, datetime,random, secrets
from bson.errors import InvalidId
from itsdangerous import URLSafeTimedSerializer, SignatureExpired


auth = Blueprint("auth", __name__, url_prefix="/api")
s = URLSafeTimedSerializer(secret_key)


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
        return {"detail":f"{str(e)} field missing or empty", "status":"error"}, 400

    pwd_hashed = generate_password_hash(password, salt_length=32)
    data["pwd"] = pwd_hashed
    data["verified"] = False
    data["role"] = ["user"]
    data["timestamp"] = datetime.datetime.now()
    data.pop("password")
    token = s.dumps(email, salt="email_confirm")
    link = url_for("auth.confirm_email", token=token, _external=True)
    try :
        mail_send = Authentication.sendMail(email, link)
        if mail_send["status"] == "success":
            users.insert_one(data)
        else:
            return jsonify({"detail":"Error occured while creating account","status":"fail"}), 400
        #users.find_one_and_update({"email":email}, {"$set":{"otp_data":otp_data}})
        
    except DuplicateKeyError as e:
        return jsonify({"detail":"Email address already used","status":"fail"}), 400
    return jsonify(detail="account created successfully", status="success", verified=False), 200
    
@auth.route("/emailCheck", methods=["POST"])
def emailCheck():
    email = request.json.get("email")

    email_check = users.find({"email":email}).hint("email_1")
    enail_list = list(email_check)
    if len(enail_list) > 0:
        message = jsonify({"detail":"Email address already used.", "status":"fail"}), 400
        return message
    message = jsonify({"detail":"Email address can be used.","status":"success"}),200
    return message

@auth.route("/signin", methods=["POST"])
def signin():
    info = request.json
    email = info.get("email")
    password = info.get("password")
    user_check = users.find({"email":email}).hint("email_1")
    user_list = list(user_check)
    if len(user_list) > 0 :
        user = user_list[0]
        pwd_check = check_password_hash(user["pwd"], password)
        if pwd_check:
            user["id"] = str(bson.ObjectId(user["_id"]))
            d = {"id": user["id"]}
            token = Authentication.generate_access_token(d)
            user["token"] = token
            user.pop("_id")
            user.pop("pwd")
            return jsonify({"detail":user, "status":"success"}), 200
        return jsonify({"detail":"Incorrect Details", "status":"fail"}), 401
        
    return jsonify({"detail": f"Account not found for {email}", "status":"fail"}), 404

@auth.route("/sendOTP", methods=["POST"])
def send_otp():
    email = request.json.get("email")
    email_check = users.find({"email":email}).hint("email_1")
    email_list = list(email_check)
    if len(email_list) > 0:
        otp_data = Authentication.generate_otp()
        users.find_one_and_update({"email":email}, {"$set":{"otp_data":otp_data}})
        mail_send = Authentication.sendMail(email, otp_data["otp"])
        if mail_send["status"]=="success":
            return jsonify({"detail":"OTP sent", "status":"success"}), 200
        else:
            return jsonify({"detail":"Error occured while sending mail","status":"fail"}),400

    return jsonify({"detail":"Account with provided email not found", "status":"error"}), 404

@auth.route("/emailVerification", methods=["POST"])
def email_verification():
    email = request.json.get("email")
    users.update_one({"email":email}, {"$set":{"verified":False}})
    token = s.dumps(email, salt="email_confirm")
    link = url_for("auth.confirm_email", token=token, _external=True)
    Authentication.mailSend(email=email, link=link)
    return jsonify({"detail":"use verification link sent to mail provided"}), 200
    

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
        return jsonify({"detail":"Incorrect token provided", "status":"error"}), 401
    user_cursor = users.find({"email":email}).hint("email_1")
    user_list = list(user_cursor)
    user = user_list[0]
    choice_length = random.choice([16,32,64])
    new_hash = generate_password_hash(new_password,salt_length=choice_length)
    users.find_one_and_update({"_id":user["_id"]}, {"$set":{"pwd":new_hash}})
    
    return jsonify({"detail":"Password Updated Successfully", "status":"success"}), 200

@auth.route("/confirm_email/<token>")
def confirm_email(token):
    try:
            email = s.loads(token, salt="email_confirm", max_age=300 )
            log_key = secrets.token_hex(32)
            user = users.find_one({"email":email})
            user_id = user["_id"]
            users.find_one_and_update({"email":email},{"$set":{"verified":True}})
            
    except SignatureExpired:
        return render_template_string("<h1> link expired </h1>")
    return redirect("https://vbatrade.com/", 302)