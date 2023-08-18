from flask import Blueprint, request, jsonify 
from folder.config import shifts, users
from folder.functions import Authentication, secret_key, gen_tag
import jwt
from bson import ObjectId
from datetime import datetime

user_jobs = Blueprint("user_jobs", __name__)

@user_jobs.route("/shifts", methods=["GET", "POST", "DELETE"])
@Authentication.token_required
def sh():
    token = request.headers.get("Authorization")
    decoded_data = jwt.decode(token, secret_key,["HS256"])
    try:
        user_id = decoded_data["id"]
        user_type = decoded_data["u_type"]
    except:
        return jsonify({"message":"Unauthorized access", "success":False}), 400

    # create a refresh_token feature here
    refresh_t = ""
    check = users.find_one({"_id":ObjectId(user_id)})
    if check != None:
        if request.method == "GET":
            shift_type = request.args.get("type")
            users_shifts = shifts.find_one({"_id":ObjectId(user_id)})
            try:
                all_shifts = users_shifts["shifts"]
                if shift_type == "active" or  shift_type == None:
                    shift_list = list(filter(lambda i: i["status"]=="active", all_shifts))
                else:
                    shift_list = list(filter(lambda i: i["status"]!="active", all_shifts))

                # for i in shift_list:
                #     i.pop
                return jsonify({"message":"", "detail":{"shifts":shift_list},"success":True, "token":refresh_t}), 200
            except TypeError as e:
                return jsonify({"message":"No active jobs created", "detail":{}, "success":True, "token":refresh_t}), 200
            
        if request.method == "POST":
            info =  request.json
            data =  {
                "description":info.get("task"),
                "start_time":info.get("start_time"),
                "end_time":info.get("end_time"),
                "start_date":info.get("start_date"),
                "end_date":info.get("end_date"),
                "provider_category":info.get("provider_category"),
                "tasks_list":[], # will contain task and completed.
                "provider_details":{"name":"",
                                    "user_id":""},
                "price_per_hour":info.get("price_per_hour"),
                "status":"active",
                "timestamp":datetime.timestamp(datetime.utcnow()),
                "job_id":gen_tag(),
                "current_status":"not_picked"
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

            shift_check = shifts.find_one({"_id":ObjectId(user_id)})
            if shift_check == None:
                shifts.insert_one({
                    "_id":ObjectId(user_id),
                    "shifts":[
                        data
                    ]
                })
            else:
                shifts.update_one({"_id":ObjectId(user_id)}, {"$push":{"shifts":data}})

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
def a(job_id):
    token = request.headers.get("Authorization")
    decoded_data = jwt.decode(token, secret_key,["HS256"])
    try:
        user_id = decoded_data["id"]
        user_type = decoded_data["u_type"]
    except:
        return jsonify({"message":"Unauthorized access", "success":False}), 400

    # create a refresh_token feature here
    refresh_t = ""
    check = users.find_one({"_id":ObjectId(user_id)})
    if check != None:
        if request.method == "GET":
            # shift_type = request.args.get("type")
            users_shifts = shifts.find_one({"_id":ObjectId(user_id)})
            try:
                shift_data = list(filter(lambda i: i['job_id']==job_id, users_shifts["shifts"]))

                return jsonify({"message":"", "detail":shift_data[0],"success":True, "token":refresh_t}), 200
            except (TypeError, IndexError):
                return jsonify({"message":"Shift unavailable", "detail":{}, "success":True, "token":refresh_t}), 200


        if request.method == "PUT":
            req_work = ["tasks_list", "job_id", "timestamp", "status", 'current_status', "provider_details"]
            info =  request.json
            keys =  [i for i in info.keys() if i not in req_work]
            data = {}
            for key in keys:
                data["shifts.$."+key] = info.get(key)
            
            tasks = info.get("tasks_list")  # list
            if tasks != None or len(tasks) > 0:
                ls = []
                for i in tasks:
                    task_data = {
                        "task":i,
                        "completed":False
                    }
                    ls.append(task_data)

            data["shifts.$.tasks_list"] = ls
            data["shifts.$.timestamp"] = datetime.timestamp(datetime.utcnow())

            shifts.update_one({"_id":ObjectId(user_id), "shifts.job_id":job_id}, {"$set":data})
            ch = shifts.find_one({"_id":ObjectId(user_id)})
            updated_shift = list(filter(lambda i: i['job_id']==job_id, ch["shifts"]))
            updated_shift  = updated_shift[0]
            return jsonify({"message":"Job updated", "detail":updated_shift,"success":True, "token":refresh_t}), 200


        if request.method == "DELETE":
            
            all_shifts = shifts.find_one({"_id":ObjectId(user_id)})
            spec_shift = list(filter(lambda i: i["job_id"] == job_id, all_shifts["shifts"]))
            if len(spec_shift) != 0:
                if spec_shift[0]["current_status"] != "not_picked":
                    return jsonify({"message":"Job selected cannot be deleted as it has been taken up by a personnel", "detail":{},"success":False, "token":refresh_t}), 400
            shifts.update_one({"_id":ObjectId(user_id), "shifts.job_id":job_id}, {"$pull":{"shifts":{"job_id":job_id}}})
            return jsonify({"message":"Job Cancelled", "detail":{},"success":True, "token":refresh_t}), 200 

