from flask import Blueprint, jsonify, request, url_for, render_template_string, redirect, render_template
from folder.config import users, misc, default_image_url
from folder.functions import Authentication, secret_key
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo.errors import DuplicateKeyError
import bson, datetime
from itsdangerous import URLSafeTimedSerializer, SignatureExpired

import os


template_folder = os.getcwd() + "/folder/templates"

auth = Blueprint("auth", __name__, template_folder=template_folder)
s = URLSafeTimedSerializer(secret_key)
tags = {
    "provider":"worker",
    "patient":"patient",
    "admin":"admin"
}

@auth.route("/createAccount", methods=["POST"])
def sign_up():
    info = request.json
    keys = [i for i in info.keys()]
    data = {}
    for i in keys:
        data[i] = info.get(i)
    try:
        email = data["email"]
        password = data["password"]
        first_name = data["FName"]
        last_name = data["LName"]
        role =  data["role"]
    except KeyError as e:
        return {"detail":{}, "success":False, "message":f"{str(e)} field missing or empty"}, 400
    
    roles =  ["patient", "admin", "worker"]
    if data["role"] not in roles:
        return jsonify({"detail":{}, "success":False, "message":"Kindly specify a role; service_provider or patient"}), 400
    user_check = users.find_one({"email":email})
    # if role == "patient" or role == "worker":
        
    if role == "admin":
        
        fetch_key =  misc.find_one({"tag":"admin_key"})
        admin_key = request.json.get("admin_key")
        if admin_key == None:
            return jsonify({"detail":{}, "success":False, "message":"kindly provide admin_key parameter with appropriate admin secret key"}), 400
        pwd_check = check_password_hash(fetch_key["key"],admin_key)
        if pwd_check == False:
            return jsonify({"detail":{}, "success":False, "message":"Invalid key provided. Kindly request an admin to grant you access"}), 400



    if user_check == None:
        pwd_hashed = generate_password_hash(password, salt_length=32)
        data["pwd"] = pwd_hashed
        data["verified"] = False
        data["role"] = role
        data["timestamp"] = datetime.datetime.timestamp(datetime.datetime.now())
        data["first_timer"] = True
        data["contact_info"] = {
            "zipcode":"", 
            "apartment_no":"", 
            "city":"", 
            "state":"", 
            "country":"",
            "phone":""
        }
        data["img_url"] = default_image_url
        
        data.pop("password")
        try:
            data.pop("admin_key")
        except Exception:
            pass
        otp_data = Authentication.generate_otp()
        code = otp_data["otp"]
        temp = render_template("verification.html", code=code, year=datetime.datetime.utcnow().year)
        token = s.dumps(otp_data, salt="otpData")
        data["s_t"] = token
        
        try :
            mail_send = Authentication.mail_send(email, temp, "Verify Your Account")
            if mail_send["status"] == "success":
                users.insert_one(data)
            else:
                return jsonify({"detail":{},"success":False, "message":"Error occured while creating account"}), 400   
                      
        except DuplicateKeyError as e:
            return jsonify({"detail":{},"success":False, "message":"Email address already used"}), 400
        return jsonify(detail={"verified":False}, success=True, message="Account Created. Check Email For Verification Mail."), 200
    
    else:
        return jsonify(detail={}, success=False, message="Account with email address provided exists"), 400

@auth.route("/emailCheck", methods=["POST"])
def emailcheck():
    email = request.json.get("email")

    email_check = users.find({"email":email})
    enail_list = list(email_check)
    if len(enail_list) > 0:
        message = jsonify({"detail":"Email address already used.", "success":False}), 400
        return message
    message = jsonify({"detail":{},"success":True, "message":"Email address can be used."}),200
    return message


@auth.route("/signin/<u_type>", methods=["POST"])
def signin_admin(u_type):
    info = request.json
    email = info.get("email")
    password = info.get("password")
    worker_type = tags[u_type]
    user_check = users.find_one({"email":email, "role":worker_type})
    
    if user_check != None :
        user = user_check
        pwd_check = check_password_hash(user["pwd"], password)
        if pwd_check:
            user_id = str(bson.ObjectId(user["_id"]))
            d = {"id": user_id, "u_type":user["role"]}
            # print(d)
            token = Authentication.generate_access_token(d)
            user["token"] = token
            message = ""
            if user["verified"] == False:
                user["token"] = ""
                message = "Kindly verify email address"
                return jsonify({"detail":{"verified":False}, "success":True, "message":message}), 200
            users.update_one({"_id":user["_id"]}, {"$set":{"first_timer":False}})
            user.pop("_id")
            user.pop("pwd")
            try:
                user.pop("s_t")
            except Exception as e:
                pass
            
            return jsonify({"detail":user, "success":True, "message":message}), 200
        return jsonify({"detail":{}, "success":False, "message":"Email and password do not match"}), 401
        
    return jsonify({"detail": {}, "success":False, "message":f"Account not found for {email}"}), 404


@auth.route("/emailVerification", methods=["POST"])
def email_verification():
    email = request.json.get("email")
    users.update_one({"email":email}, {"$set":{"verified":False}})
    token = s.dumps(email, salt="email_confirm")
    url = url_for("providers.auth.confirm_email", token=token, _external=True)
    temp = render_template("reset_mail.html", action_url=url) 
    
    st = Authentication.mail_send(email, str(temp), "Verify your account")
    if st["status"] == "success":
        return jsonify({"detail":{}, "success":True, "message":"use verification link sent to mail provided"}), 200
    else:
        return jsonify({"detail":{}, "success":False, "message":"There was an error while sending verification mails, check back later"}), 400 
 
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
            url = url_for("providers.auth.res_pass", token=token, _external=True)
            return render_template("pwd_reset.html", post_url=url),  200
            # user would be redirected to password reset page
        
            
    except SignatureExpired:
        return render_template_string("<h1> link expired </h1>")


@auth.route("/postPassword", methods=["POST"])
def res_pass():
    if request.method == "POST":
        token = request.args.get("token")
        email = s.loads(token, salt="email_confirm", max_age=300 )
        password = request.form.get("newPassword")
        hashed_pwd = generate_password_hash(password, "pbkdf2:sha256")
        users.update_one({"email":email}, {"$set":{"pwd":hashed_pwd, "verified":True}})
        return jsonify({"detail":{}, "success":True, "message":"Password Successfully Updated"}), 200


@auth.route("/sendOTP", methods=["POST"])
def send_otp():
    email = request.json.get("email")
    check = users.find({"email":email})
    if check != None:
        otp_data = Authentication.generate_otp()
        code = otp_data["otp"]
        temp = render_template("verification.html", code=code)
        token = s.dumps(otp_data, salt="otpData")
        Authentication.mail_send(email, temp, "OTP Verification")
        users.update_one({"email":email}, {"$set":{"s_t":token}})
        return jsonify({"detail":{}, "success":True, "message":"OTP Sent"}), 200
    return jsonify({"detail":{}, "success":False, "message":f"No account found for '{email}'"}), 400 


@auth.route("/verifyOTP", methods=["POST"])
def ver_otp():
    email = request.json.get("email")
    otp = request.json.get("otp")
    check = users.find_one({"email":email})
    if check  != None:
        token = check["s_t"]
        try:
            t_data = s.loads(token, salt="otpData", max_age=600)
        except SignatureExpired as e:
            return jsonify({"detail":"The OTP provided has expired.", "success":False}), 400 
        initial_verify = check["verified"]
        verify = False
        if t_data["otp"] == otp:
            verify = True
    if verify == True:
        data = {}
        if initial_verify != True and check["role"] == "worker":
            d = {"id": str(check["_id"]), "u_type":check["role"]}
            token = Authentication.generate_access_token(d)
            data = {"token":token}
            
        users.update_one({"email":email}, {"$set":{"s_t":"", "verified":True}})
        return jsonify({"detail":data, "success":True, "message":"Account verified"}), 200
    return jsonify({"detail":{}, "success":False, "message":"Incorrect OTP"}), 400
            