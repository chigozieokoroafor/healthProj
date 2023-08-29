from urllib.robotparser import RequestRate
from flask import Blueprint, Response, jsonify, request, url_for, render_template_string, redirect, render_template, flash
import pymongo
from folder.config import users, misc
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

admin_others = Blueprint("admin_others", __name__, template_folder=template_folder)
s = URLSafeTimedSerializer(secret_key)

@admin_others.route("/providersCategories", methods=['POST', "GET"])        
@Authentication.token_required
def provCat():
    token =  request.headers.get("Authorization")
    decoded_data =  jwt.decode(token, key=secret_key, algorithms=["HS256"])
    try:
        user_id = decoded_data["id"]
        user_type = decoded_data["u_type"]
    except:
        return jsonify({"message":"Unauthorized access", "success":False}), 400
    admin_check = users.find_one({"_id":ObjectId(user_id), "role":"admin"})

    if admin_check!= None:
        if request.method == "GET":
            it_check = misc.find_one({"tag":"categories"})
            try:
                data =  {"cat_list":it_check["categories"]}
            except:
                data = {"cat_list":[]}
            return jsonify({"message":"", "detail":data, "success":True, "token":""}), 200
        
        if request.method =="POST":
            category_name = request.json.get("category_name")
            cat_check = misc.find_one({"tag":"categories"})
            pushed_data = {
                "categories":category_name
            }
            if cat_check != None:
                misc.update_one({"tag":"categories"}, {"$push":pushed_data})
            else:
                misc.insert_one({"tag":"categories", "categories":[category_name]})
            return jsonify({"message":"New Service Provider Category uploaded.", "detail":{}, "success":True, "token":""}), 200

        if request.method == "DELETE":
            category_name = request.args.get("cat_name")
            misc.update_one({"tag":"categories"}, {"$pull":{"categories":category_name}})
            return jsonify({"message":"Service Provider Category deleted", "detail":{}, "success":True, "token":""}), 200    
    
    else:
        return jsonify({"message":"Unauthorized Access", "detail":{}, "success":False, "token":""}), 400

    