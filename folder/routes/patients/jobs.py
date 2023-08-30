from flask import Blueprint, request, jsonify 
from folder.config import shifts, users, misc, default_image_url
from folder.functions import Authentication, secret_key, gen_tag
import jwt
from bson import ObjectId
from datetime import datetime

user_jobs = Blueprint("user_jobs", __name__)


@user_jobs.route("/shifts", methods=["GET", "POST", "DELETE"])
@Authentication.token_required
def sh():
    token = request.headers.get("Authorization")
    decoded_data = jwt.decode(token, secret_key,algorithms=["HS256"])
    refresh_t = Authentication.tokenExpCheck(decoded_data["exp"], decoded_data)
    try:
        user_id = decoded_data["id"]
        user_type = decoded_data["u_type"]
    except:
        return jsonify({"message":"Unauthorized access", "success":False, "detail":{}}), 400

    
    check = users.find_one({"_id":ObjectId(user_id)})
    if check != None:
        if request.method == "GET":
            shift_type = request.args.get("type")
            users_shifts = shifts.find({"creator_id":user_id})
            users_shifts = list(users_shifts)
            try:
                
                if shift_type == "active" or  shift_type == None:
                    shift_list = list(filter(lambda i: i["status"]=="active", users_shifts))
                else:
                    shift_list = list(filter(lambda i: i["status"]!="active", users_shifts))

                message = ""
                if len(shift_list) <=  0 and shift_type == "active":
                    message = "No active jobs available"
                elif len(shift_list) <=  0 and shift_type != "active":
                    message = "No jobs have been completed"
                

                return jsonify({"message":message, "detail":{"shifts":shift_list},"success":True, "token":refresh_t}), 200
            except TypeError as e:
                # print(e)
                return jsonify({"message":"No active jobs created", "detail":{"shifts":[]}, "success":True, "token":refresh_t}), 200
            
        if request.method == "POST":
            info =  request.json
            data =  {
                "description":info.get("description"),
                "start_time":info.get("start_time"),
                "end_time":info.get("end_time"),
                "start_date":info.get("start_date"),
                "provider_category":info.get("provider_category"),
                "tasks_list":[], # will contain task and completed.
                "provider_details":{"name":"",
                                    "user_id":"",
                                    "img_url":default_image_url},
                "price_per_hour":info.get("price_per_hour"),
                "status":"active",
                "timestamp":datetime.timestamp(datetime.utcnow()),
                "_id":gen_tag(),
                "current_status":1
            }

            tasks = info.get("tasks_list")  # list
            if tasks != None or len(tasks) > 0:
                ls = []
                for i in tasks:
                    task_data = {
                        "task":i,
                        "completed":False
                    }
                    ls.append(task_data)

            data["tasks_list"] = ls
            data["creator_details"] = {
                "_id":user_id,
                "name":f'{check["FName"] } {check["LName"]}',
                "img_url":check["img_url"]
            }

            shifts.insert_one(data)
            return jsonify({"message":"Job uploaded", "detail":{},"success":True, "token":refresh_t}), 200
      
        if request.method == "DELETE": # to cancel.
            job_id = request.json.get("job_id")
            all_shifts = shifts.find_one({"_id":ObjectId(user_id)})
            spec_shift = list(filter(lambda i: i["job_id"] == job_id, all_shifts["shifts"]))
            if len(spec_shift) != 0:
                if spec_shift[0]["current_status"] != "not_picked":
                    return jsonify({"message":"Job selected cannot be deleted as it has been taken up by a personnel", "detail":{},"success":False, "token":refresh_t}), 400
            shifts.update_one({"_id":ObjectId(user_id), "shifts.job_id":job_id}, {"$pull":{"shifts":{"job_id":job_id}}})
            return jsonify({"message":"Job Cancelled", "detail":{},"success":True, "token":refresh_t}), 200

    else:
        return jsonify({"message":"User not found", "detail":{},"success":False, "token":refresh_t}), 404

@user_jobs.route("/shifts/<job_id>", methods=["GET", "PUT", "DELETE"])
@Authentication.token_required
def specJob(job_id):
    token = request.headers.get("Authorization")
    decoded_data = jwt.decode(token, secret_key,algorithms=["HS256"])
    refresh_t = Authentication.tokenExpCheck(decoded_data["exp"], decoded_data)
    try:
        user_id = decoded_data["id"]
        user_type = decoded_data["u_type"]
    except:
        return jsonify({"message":"Unauthorized access", "success":False, "detail":{}}), 400
    
    if request.method == "GET":
        # shift_type = request.args.get("type")
        # users_shifts = shifts.find_one({"_id":ObjectId(user_id)})
        # try:
        #     shift_data = list(filter(lambda i: i['job_id']==job_id, users_shifts["shifts"]))
        shift_data = shifts.find_one({"_id":job_id})
        if shift_data == None:
            return jsonify({"message":"Shift unavailable", "detail":{}, "success":True, "token":refresh_t}), 200
        shift_data.pop("creator_id")
        return jsonify({"message":"", "detail":shift_data,"success":True, "token":refresh_t}), 200
            


    if request.method == "PUT":
        req_work = ["tasks_list", "job_id", "timestamp", "status", 'current_status', "provider_details"]
        info =  request.json
        keys =  [i for i in info.keys() if i in req_work]
        data = {}
        for i in keys:
            data[i] = info.get(i) 
        
        tasks = info.get("tasks_list")  # list
        if tasks != None or len(tasks) > 0:
            ls = []
            for i in tasks:
                task_data = {
                    "task":i,
                    "completed":False
                }
                ls.append(task_data)

        data["tasks_list"] = ls
        data["timestamp"] = datetime.timestamp(datetime.utcnow())

        shifts.update_one({"_id":job_id}, {"$set":data})
        ch = shifts.find_one({"_id":user_id})
        ch.pop("creator_id")
        return jsonify({"message":"Job updated", "detail":ch,"success":True, "token":refresh_t}), 200


    if request.method == "DELETE":
        spec_shift = shifts.find_one({"_id":job_id})
        if spec_shift["current_status"] != "not_picked":
                return jsonify({"message":"Job selected cannot be deleted as it has been taken up by a personnel", "detail":{},"success":False, "token":refresh_t}), 400
        shifts.delete_one({"_id":job_id})
        return jsonify({"message":"Job Cancelled", "detail":{},"success":True, "token":refresh_t}), 200 


@user_jobs.route("/providerCat", methods = ["GET"])
def fetchProviderCat():
    check = misc.find_one({"tag":"categories"})
    try:
        return jsonify({"message":"success", "detail":{
            "categories":check["categories"]
        }, "success":True, "token":""}), 200
    except TypeError:
        return jsonify({"message":"Unable to fetch categories at current time", "detail":{}, "success":False, "token":""}), 400