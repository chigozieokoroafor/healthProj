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
        if request.method == "GET": # to get list of all shifts
            page = request.args.get("page")
            offset = 10
            if page==None:
                page = 1
            else:
                page = int(page)
            skip = (page-1)*offset

            active_shifts = shifts.find({"provider_category":user_check["category"], "current_status":1}).skip(skip).limit(offset)
            ls = list(active_shifts)
            popping_items = ["provider_details", "status", "timestamp", "current_status", "tasks_list", "provider_category"]
            u_shifts = list(filter(lambda i: [i.pop(popping_items[0]), i.pop(popping_items[1]), i.pop(popping_items[2]), i.pop(popping_items[3]), i.pop(popping_items[4]), i.pop(popping_items[5])], ls))
           
            return jsonify({"message":"", "success":True, "detail":{"shifts":u_shifts}, "token":refresh_t}), 200

        if request.method == "POST": # this is used to accept shifts
            shift_id = request.json.get("shift_id")
            shifts.update_one({"_id":shift_id}, {"$set":{"current_status":2,"provider_details.name":f'{user_check["FName"]} {user_check["LName"]}', "provider_details.user_id":user_id, "provider_details.img_url":user_check["img_url"]}})
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
            updateable_items = ["status", "task"]
            info =  request.json
            keys = [i for i in info.keys() if i in updateable_items]
            

            return jsonify({"message":"Working", "success":True, "detail":{}, "token":refresh_t}), 200

        if request.method == "DELETE": # this is to quit a particular shift.
            shifts.update_one({"_id":shift_id}, {"$set":{"provider_details.name":"", "provider_details.user_id":"", "provider_details.img_url":default_image_url, "current_status":1}})
            return jsonify({"message":"Successfully exited shift ", "success":True, "detail":{}, "token":refresh_t}), 200



@prov_shifts.route("/user_shifts/<shift_type>", methods=["GET"])
@Authentication.token_required
def getUserShifts(shift_type):
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
        
            check = shifts.find({"provider_details.user_id":user_id})
            check =  list(check)
            
            popping_items = ["provider_details", "status", "timestamp", "current_status", "tasks_list", "provider_category"]
            if shift_type == "ongoing":
                u_shifts = list(filter(lambda i: i["status"] == "active" and i["current_status"] == 2, check))
                

            if shift_type == "completed":
                u_shifts = list(filter(lambda i: i["status"] == "active" and i["current_status"] == 3, check))
            
            if len(u_shifts)>0:
                u_shifts = list(filter(lambda i: [i.pop(popping_items[0]), i.pop(popping_items[1]), i.pop(popping_items[2]), i.pop(popping_items[3]), i.pop(popping_items[4]), i.pop(popping_items[5])], u_shifts))
            
            return jsonify({"message":"", "success":True, "detail":{"shifts":u_shifts}, "token":refresh_t}), 200
    
    else:
        return  jsonify({"message":"Unauthorized Access", "success":False, "detail":{}}), 400
        
