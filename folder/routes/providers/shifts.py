from folder.config import users, shifts
from folder.functions import Authentication, secret_key
from flask import Blueprint, request, jsonify
import jwt
from bson import ObjectId

shifts = Blueprint("prov_shifts", __name__)

@shifts.route("/shifts", methods=["GET", "POST"])
@Authentication.token_required
def handleShifts():
    token = request.headers.get("Authorization")
    decoded_data = jwt.decode(token, secret_key, ["HS256"])
    try:
        user_id = decoded_data["id"]
        user_type = decoded_data["u_type"]
    except:
        return jsonify({"message":"Unauthorized access", "success":False}), 400
    
    user_check = users.find_one({"_id":ObjectId(user_id), "role":"worker"})
    if user_check != None:
        if request.method == "GET":
            pass
        if request.method == "POST":
            shift_id = request.json.get("shift_id")
            shifts.find_one({""})

    else:
        return  jsonify({"message":"Unauthorized Access", "success":False, "detail":{}}), 400