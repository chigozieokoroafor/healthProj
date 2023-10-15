from urllib.robotparser import RequestRate
from flask import Blueprint, Response, jsonify, request, url_for, render_template_string, redirect, render_template, flash
import pymongo
from folder.config import users, misc
from folder.functions import Authentication, secret_key, format_data, unauth_mess
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo.errors import DuplicateKeyError
import jwt, bson, datetime,random, secrets
from bson.errors import InvalidId
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from bson import ObjectId
import os



template_folder = os.getcwd() + "/folder/templates"

service = Blueprint("admin_service_providers", __name__, template_folder=template_folder)

@service.route("/fetchServiceProviders", methods=["GET"])
@Authentication.token_required
def fetch_service_providers():
    token =  request.headers.get("Authorization")
    decoded_data =  jwt.decode(token, key=secret_key, algorithms=["HS256"])
    refresh_t = Authentication.tokenExpCheck(decoded_data["exp"], decoded_data)
    try:
        user_id = decoded_data["id"]
        user_type = decoded_data["u_type"]
    except Exception as e:
        return jsonify({"message":unauth_mess, "detail":{}, "success":False, "token":""}), 401
    admin_check = users.find_one({"_id":ObjectId(user_id), "role":"admin"})
    if admin_check != None:
        if request.method == "GET":
            page = request.args.get("page")
            offset = 10
            if page==None:
                page = 1
            else:
                page = int(page)
            skip = (page-1)*offset

            cursor = users.find({"role":"worker"}).skip(skip).limit(offset).sort("timestamp", pymongo.DESCENDING)
            all_users =  list(cursor)
            popping_items = ["role", "first_timer", "contact_info", "timestamp", "pwd", "verified"]
            providers = list(filter(lambda i: [i.pop(popping_items[0]), i.pop(popping_items[1]), i.pop(popping_items[2]), i.pop(popping_items[3]), i.pop(popping_items[4]), i.pop(popping_items[5])], all_users))
            
            data = format_data(providers)
            return jsonify({"message":unauth_mess, "detail":{"providers":data}, "success":False, "token":refresh_t}), 401
           
        
    else:
        return jsonify({"message":unauth_mess, "detail":{}, "success":False, "token":""}), 401


@service.route("/provider/<provider_id>", methods=["GET", "PUT"])
@Authentication.token_required
def handle_specific_providers(provider_id):
    token =  request.headers.get("Authorization")
    decoded_data =  jwt.decode(token, key=secret_key, algorithms=["HS256"])
    try:
        user_id = decoded_data["id"]
        
    except Exception:
        return jsonify({"message":unauth_mess, "detail":{}, "success":False, "token":""}), 401
    admin_check = users.find_one({"_id":ObjectId(user_id), "role":"admin"})
    if admin_check != None:
        if request.method == "GET":
            provider_find = users.find_one({"_id":ObjectId(provider_id)})
            
            if provider_find == None:
                return jsonify({"message":"User not found", "detail":{}, "success":False, "token":""}), 200
            else:
                provider_find.pop("_id")
                return jsonify({"message":"", "detail":{}, "success":False, "token":""}), 200
   
        
    else:
        return jsonify({"message":unauth_mess, "detail":{}, "success":False, "token":""}), 401

    
# change alll the match cases