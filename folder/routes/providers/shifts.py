from folder.config import users, shifts
from folder.functions import Authentication, secret_key
from flask import Blueprint, request, jsonify
import jwt
from bson import ObjectId

prov_shifts = Blueprint("prov_shifts", __name__)

#this get's all the shifts available for a particular category
@prov_shifts.route("/shifts", methods=["GET"]) 
@Authentication.token_required
def handleShifts():
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
            offset = 20
            if page==None:
                page = 1
            else:
                page = int(page)
            skip = (page-1)*offset

            active_shifts = shifts.find({"provider_category":user_check["category"], "current_status":1}).skip(skip).limit(offset)
            ls = list(active_shifts)

            return jsonify({"message":"", "success":True, "detail":{"shifts":ls}, "token":refresh_t}), 200

    else:
        return  jsonify({"message":"Unauthorized Access", "success":False, "detail":{}}), 400