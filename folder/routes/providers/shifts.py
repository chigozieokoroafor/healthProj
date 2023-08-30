from folder.config import users, shifts, default_image_url
from folder.functions import Authentication, secret_key
from flask import Blueprint, request, jsonify
import jwt
from bson import ObjectId

prov_shifts = Blueprint("prov_shifts", __name__)

#this get's all the shifts available for a particular category
@prov_shifts.route("/shifts", methods=["GET", "POST"]) 
@Authentication.token_required
def fetchAllShifts():
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
        if request.method == "GET":
            page = request.args.get("page")
            offset = 10
            if page==None:
                page = 1
            else:
                page = int(page)
            skip = (page-1)*offset

            active_shifts = shifts.find({"provider_category":user_check["category"], "current_status":1}).skip(skip).limit(offset)
            ls = list(active_shifts)
            for i in ls:
                popping_items = ["provider_details", "status", "timestamp", "current_status", "tasks_list"]
                for x in popping_items:
                    i.pop(x)

            return jsonify({"message":"", "success":True, "detail":{"shifts":ls}, "token":refresh_t}), 200

        if request.method == "POST": # this is used to accept shifts
            shift_id = request.json.get("shift_id")
            shifts.update_one({"_id":shift_id}, {"$set":{"provider_details.name":f'{user_check["FName"]} {user_check["LName"]}', "provider_details.user_id":user_id, "provider_details.img_url":user_check["img_url"]}})
            return jsonify({"message":"Shift accepted", "success":True, "detail":{}, "token":refresh_t}), 200
    
    else:
        return  jsonify({"message":"Unauthorized Access", "success":False, "detail":{}}), 400
    
@prov_shifts.route("/shifts/<shift_id>", methods=["GET", "POST", "PUT", "DELETE"])
@Authentication.token_required
def handleShifts(shift_id):
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
        if request.method == "GET":
            check = shifts.find_one({"_id":shift_id})
            popping_items = ["provider_details", "status", "timestamp", "current_status"]
            for x in popping_items:
                check.pop(x)
            return jsonify({"message":"", "success":True, "detail":check, "token":refresh_t}), 200

        if request.method == "PUT": # to update the progress or status of task
            pass

        if request.method == "DELETE": # this is to quit a particular shift.
            shifts.update_one({"_id":shift_id}, {"$set":{"provider_details.name":"", "provider_details.user_id":"", "provider_details.img_url":default_image_url}})
            return jsonify({"message":"Successfully ", "success":True, "detail":{}, "token":refresh_t}), 200
        
