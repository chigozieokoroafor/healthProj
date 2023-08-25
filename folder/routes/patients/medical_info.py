from urllib.robotparser import RequestRate
from flask import Blueprint, Response, jsonify, request, url_for, render_template_string, redirect, render_template, flash
import pymongo
from folder.config import users, medical_info
from folder.functions import Authentication, secret_key
from werkzeug.security import generate_password_hash, check_password_hash
from pymongo.errors import DuplicateKeyError
import jwt, bson, datetime,random, secrets
from bson.errors import InvalidId
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from bson import ObjectId
import os

medicals = Blueprint("meds", __name__)

# Medical history would be here.
# Medical insurance check would also be here.

# Fetch insurance provider. 
# input insurance id and check if user's data can be found.

# Upload Medical Information
# Bloodgroup
# genotype
# Sugeries and dates
# Allergies
# Medical conditions

@medicals.route("/medicalInfo", methods=["GET", "POST"])
@Authentication.token_required
def medInfo():
    token = request.headers.get("Authorization")
    decoded_data = jwt.decode(token, secret_key,algorithms=["HS256"])
    refresh_t = Authentication.tokenExpCheck(decoded_data["exp"], decoded_data)
    try:
        user_id = decoded_data["id"]
        user_type = decoded_data["u_type"]
    except:
        return jsonify({"message":"Unauthorized access", "success":False, "detail":{}}), 400
    
    user_check = users.find_one({"_id":ObjectId(user_id)})
    if user_check != None:
        if request.method == "GET":
            return "working"
        

        if request.method == "POST":
            test_name = request.json.get("nameOfTest")
            image_url = request.json.get("image_url")

            data = {
                "name":test_name,
                "image_url" : image_url
            }
            med_check = medical_info.find_one({"_id":ObjectId(user_id)})
            if med_check !=  None:
                medical_info.update_one({"_id":ObjectId(user_id)}, {"$push":{"medTests":data}})
            else:
                medical_info.insert_one({"_id":ObjectId(user_id), "medTests":[data]})

            return jsonify({"message":"Medical Info updated", "detail":{},"success":True, "token":refresh_t}), 200

    else:        
        return jsonify({"message":"Unauthorized Access", "detail":{}, "success":False}), 400

