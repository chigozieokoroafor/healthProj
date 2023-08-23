from flask import Blueprint, request, jsonify
from folder.functions import Authentication, secret_key
from bson import ObjectId
from folder.config import *
import jwt

others =  Blueprint("prov_others", __name__)

@others.route("/home")
@Authentication.token_required
def home():
    token =  request.headers.get("Authorization")
    decoded_data =  jwt.decode(token, secret_key, ['HS256'])
    try:
        user_id = decoded_data["id"]
        user_role =  decoded_data["u_type"]
    except Exception as e:
        # print(e)
        jsonify({"detail":{}, "message":"Unauthorized access", "success":False}), 400
    user_check = users.find_one({"_id":ObjectId(user_id), "role":user_role})
    if user_check != None:
        wallet_balance =  0.0
        completed_shifts = shifts.count_documents({"provider_details.user_id":user_id, "current_status":3})
        try:
            user_cat = user_check["category"]
        except KeyError as e:
            return jsonify({"detail":{}, "message":"User not a service provider not found", "success":False}), 400
        cat_shifts = list(shifts.aggregate(
            [
                {"$match":{"provider_category":user_cat}},
                {"$sample":{"size":5}}
            ]
            )
            )
        for i in cat_shifts:
            i.pop("creator_id")
        data = {
            "wallet_balance":wallet_balance,
            "completed_shifts":completed_shifts,
            "avail_shifts": cat_shifts
        }
        return jsonify({"detail":data, "message":"", "success":True}), 200
    else:
        return jsonify({"detail":{}, "message":"User not found", "success":False}), 400

