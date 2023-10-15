from urllib.robotparser import RequestRate
from flask import Blueprint, Response, jsonify, request, url_for, render_template_string, redirect, render_template, flash
import pymongo
from folder.config import users, misc
from folder.functions import Authentication, secret_key, unauth_mess
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo.errors import DuplicateKeyError
import jwt, bson, datetime,random, secrets
from bson.errors import InvalidId
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from bson import ObjectId
import os
# from flask_mail import Mail, Message


template_folder = os.getcwd() + "/folder/templates"

admin_others = Blueprint("admin_others", __name__, template_folder=template_folder)


@admin_others.route("/providersCategories", methods=['POST', "GET", "DELETE"])        
@Authentication.token_required
def prov_cat():
    token =  request.headers.get("Authorization")
    decoded_data =  jwt.decode(token, key=secret_key, algorithms=["HS256"])
    try:
        user_id = decoded_data["id"]
    except Exception:
        return jsonify({"message":unauth_mess, "detail":{}, "success":False, "token":""}), 401
    admin_check = users.find_one({"_id":ObjectId(user_id), "role":"admin"})

    if admin_check!= None:
        if request.method == "GET":
            it_check = misc.find_one({"tag":"categories"})
            try:
                data =  {"cat_list":it_check["categories"]}
            except Exception:
                data = {"cat_list":[]}
            return jsonify({"message":"", "detail":data, "success":True, "token":""}), 200
        
        if request.method =="POST":
            category_name = request.json.get("category_name")
            abbrv = request.json.get("abbrv")
            cat_check = misc.find_one({"tag":"categories"})
            pushed_data = {
                "categories":{
                    "name":category_name,
                    "abbrv":abbrv
                }
            }
            if cat_check != None:
                misc.update_one({"tag":"categories"}, {"$push":pushed_data})
            else:
                pushed_data["tag"] = "categories"
                misc.insert_one(pushed_data)
            return jsonify({"message":"New Service Provider Category uploaded.", "detail":{}, "success":True, "token":""}), 200

        if request.method == "DELETE":
            category_name = request.args.get("cat_name")
            misc.update_one({"tag":"categories"}, {"$pull":{"categories":{"name":category_name}}})
            return jsonify({"message":"Service Provider Category deleted", "detail":{}, "success":True, "token":""}), 200    
    
    else:
        return jsonify({"message":unauth_mess, "detail":{}, "success":False, "token":""}), 401

@admin_others.route("providerCredentials", methods=["POST", "GET", "PUT", "DELETE"])
@Authentication.token_required
def prov_credentials():
    token =  request.headers.get("Authorization")
    decoded_data =  jwt.decode(token, key=secret_key, algorithms=["HS256"])
    try:
        user_id = decoded_data["id"]
    except Exception:
        return jsonify({"message":unauth_mess, "detail":{}, "success":False, "token":""}), 401
    
    admin_check = users.find_one({"_id":ObjectId(user_id), "role":"admin"})
    if admin_check != None:
        if request.method == "GET":
            cred_check = misc.find_one({"tag":"credentials"})
            try:
                data =  {"cred_list":cred_check["prov_cred"]}
            except Exception:
                data = {"cred_list":[]}
            return jsonify({"message":"", "detail":data, "success":True, "token":""}), 200

        if request.method == "POST":
            provider_category = request.json.get("category")
            credentials = request.json.get("credentials") # this is a list of credentials

            data = {
                "cred_list":{
                    {"category":provider_category,
                     "credentials":credentials}
                }
            }

            cred_check = misc.find_one({"tag":"credentials"})
            if cred_check != None:
                misc.find_one_and_update({"tag":"credentials"}, {"$push":data})
            else:
                data["tag"] = "credentials"
                misc.insert_one(data)
            return jsonify({"message":"Service provider required credentials uploaded.", "detail":{}, "success":True, "token":""}), 200 
            
    else:
        return jsonify({"message":unauth_mess, "detail":{}, "success":False, "token":""}), 401
    