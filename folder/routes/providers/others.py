from flask import Blueprint, request, jsonify
from folder.functions import Authentication, secret_key
from bson import ObjectId
from folder.config import *
import jwt
from datetime import datetime

others =  Blueprint("prov_others", __name__)

# gets 5 random available shifts the provider falls under along  with a totality of his completed shifts and wallet_balance
@others.route("/home")
@Authentication.token_required
def home():
    token = request.headers.get("Authorization")
    decoded_data = jwt.decode(token, secret_key,algorithms=["HS256"])
    refresh_t = Authentication.tokenExpCheck(decoded_data["exp"], decoded_data)
    try:
        user_id = decoded_data["id"]
        user_type = decoded_data["u_type"]
    except:
        return jsonify({"message":"Unauthorized access", "success":False, "detail":{}}), 400
    
    user_check = users.find_one({"_id":ObjectId(user_id), "role":"worker"})
    if user_check != None:
        wallet_balance =  0.0
        completed_shifts = shifts.count_documents({"provider_details.user_id":user_id, "current_status":3})
        try:
            user_cat = user_check["category"] #very important.
        except KeyError as e:
            return jsonify({"detail":{}, "message":"Kindly pick provider category user falls under", "success":False}), 400
        
        cat_shifts = list(shifts.aggregate(
            [
                {"$match":{"provider_category":user_cat,
                           "current_status":1}},
                {"$sample":{"size":5}}
            ]
            )
            )
        
        for i in cat_shifts:
            popping_items = ["provider_details", "status", "timestamp", "current_status", "tasks_list"]
            for x in popping_items:
                i.pop(x)
            
        data = {
            "wallet_balance":wallet_balance,
            "completed_shifts":completed_shifts, # this is a integer
            "avail_shifts": cat_shifts
        }
        return jsonify({"detail":data, "message":"", "success":True, "token":refresh_t}), 200
    else:
        return jsonify({"detail":{}, "message":"User not found", "success":False}), 400

@others.route("/certificates", methods=["GET", "POST"])
@Authentication.token_required
def certs():
    token = request.headers.get("Authorization")
    decoded_data = jwt.decode(token, secret_key,algorithms=["HS256"])
    refresh_t = Authentication.tokenExpCheck(decoded_data["exp"], decoded_data)
    try:
        user_id = decoded_data["id"]
        user_type = decoded_data["u_type"]
    except:
        return jsonify({"message":"Unauthorized access", "success":False, "detail":{}}), 400

    user_check = users.find_one({"_id":ObjectId(user_id), "role":"worker"})
    if user_check != None :
        if request.method == "GET":
            check = credentials.find_one({"_id":ObjectId(user_id)})
            if check != None:
                return jsonify({"detail":{"credentials":check["credentials"]}, "token":refresh_t, "success":True, "message":""}), 200
            else:return jsonify({"message":"No credentials uploaded", "success":True, "detail":{}, "token":refresh_t}), 200
        if request.method == "POST":
            info = request.json
            cert_url = info.get("cred_url")
            cert_name = info.get("cred_name")
            date = datetime.utcnow()
            timestamp = datetime.timestamp(date)
            date = date.date()
            data = {
                "cert_url":cert_url,
                "cert_name":cert_name,
                "date":date,
                "timestamp":timestamp
            }
            cred_check = credentials.find_one({"_id":ObjectId(user_id)})
            if cred_check != None:
                credentials.update_one({"_id":ObjectId(user_id)}, {"$push":{"credentials":data}})
            else:
                credentials.insert_one({"_id":ObjectId(user_id), "credentials":[data]})
            return jsonify({"message":"Credential uploaded", "success":True, "detail":{}, "token":refresh_t}), 200
    else:
        return jsonify({"message":"User not a service provider.", "success":False, "detail":{}}), 400

@others.route("/categories", methods=["POST", "GET"])
@Authentication.token_required
def catSel():
    pass

@others.route("/profile_info", methods = ["GET", "POST"])
@Authentication.token_required
def profile():
    token = request.headers.get("Authorization")
    decoded_data = jwt.decode(token, secret_key,algorithms=["HS256"])
    refresh_t = Authentication.tokenExpCheck(decoded_data["exp"], decoded_data)
    try:
        user_id = decoded_data["id"]
        # user_type = decoded_data["u_type"]
    except:
        return jsonify({"message":"Unauthorized access", "success":False, "detail":{}}), 400

    user_check = users.find_one({"_id":ObjectId(user_id), "role":"worker"})
    if user_check != None:
        if request.method == "POST":
            pass
        if request.method == "GET":
            data = {
                "FName":user_check["FName"],
                "LName":user_check["LName"],
                "email":user_check["email"],
                "phone_no":user_check["contact_info"]["phone"]
            }
    else:
        return