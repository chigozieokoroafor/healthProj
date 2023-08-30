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

base_user = Blueprint("base_user", __name__)

@base_user.route("/userProfile", methods=["GET", "POST"])
@Authentication.token_required
def userProfile():
    token = request.headers.get("Authorization")
    decoded_data = jwt.decode(token, secret_key,["HS256"])
    try:
        user_id = decoded_data["id"]
        user_type = decoded_data["u_type"]
    except:
        return jsonify({"detail":"Unauthorized access", "success":False}), 400

    # create a refresh_token feature here
    refresh_t = ""
    user_check = users.find_one({"_id":ObjectId(user_id)})
    if user_check != None:
        if request.method == "GET":
            popping_list = ["s_t", "pwd", "timestamp", "_id", "verified", "first_timer", "contact_info"]
            for i in popping_list:
                try:
                    user_check.pop(i)
                except:
                    pass
            return jsonify({"detail":user_check, 'success':True, "message":""}), 200
    
        if request.method == "POST":
            updateable_list = ["FName", "LName", "gender", "dob"]
            info = request.json
            data = {}
            for i in updateable_list:
                info_check = info.get(i)
                if info_check != None:
                    data[i] = info_check
            users.update_one({"_id":ObjectId(user_id)},{"$set":data})
            return jsonify({"message":"Info updated", "success":True, 'detail':{}}), 200

 
    return jsonify({"message":"Unauthorized Access", "success":False, "detail":{}}), 400


@base_user.route("/contactInformation", methods=["GET", "POST"])    
@Authentication.token_required
def contactInfo():
    token = request.headers.get("Authorization")
    decoded_data = jwt.decode(token, secret_key,algorithms=["HS256"])
    refresh_t = Authentication.tokenExpCheck(decoded_data["exp"], decoded_data)
    try:
        user_id = decoded_data["id"]
        user_type = decoded_data["u_type"]
    except:
        return jsonify({"message":"Unauthorized access", "success":False, "detail":{}}), 400

    # create a refresh_token feature here
    user_check = users.find_one({"_id":ObjectId(user_id)})
    if user_check != None:
        if request.method == "GET":
            popping_list = ["zipcode", "apartment_no", "city", "state", "country", "phone"]
            data = {}
            for i in popping_list:
                data[i] = user_check["contact_info"][i]

            return jsonify({"detail":data, "message":"",'success':True, "token":refresh_t}), 200
    
        if request.method == "POST":
            updateable_list = ["zipcode", "apartment_no", "city", "state", "country", "phone", "address"]
            info = request.json
            data = {}
            for i in updateable_list:
                info_check = info.get(i)
                if info_check != None:
                    data["contact_info."+ i] = info_check
            users.update_one({"_id":ObjectId(user_id)},{"$set":data})
            return jsonify({"message":"Info updated", "success":True, "token":refresh_t}), 200


    return jsonify({"message":"Unauthorized Access", "success":False, "detail":{}, "token":""}), 400


@base_user.route("/payment_info", methods=["GET", "POST"])
@Authentication.token_required
def payment():
    pass

# do route for phone number verification seperately
 

 