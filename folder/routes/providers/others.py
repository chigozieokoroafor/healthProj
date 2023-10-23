from flask import Blueprint, request, jsonify, send_from_directory, url_for
from folder.functions import Authentication, secret_key, unauth_mess
from bson import ObjectId
from folder.config import *
import jwt
from datetime import datetime
from werkzeug.utils import secure_filename
from glob import glob




others =  Blueprint("prov_others", __name__)
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg',"docx"}



# print(others.config)
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
# gets 5 random available shifts the provider falls under along  with a totality of his completed shifts and wallet_balance
@others.route("/home")
@Authentication.token_required
def home():
    token = request.headers.get("Authorization")
    decoded_data = jwt.decode(token, secret_key,algorithms=["HS256"])
    refresh_t = Authentication.tokenExpCheck(decoded_data["exp"], decoded_data)
    try:
        user_id = decoded_data["id"]
        user_type = decoded_data["u_type"]
    except Exception:
        return jsonify({"message":unauth_mess, "success":False, "detail":{}}), 400
    
    user_check = users.find_one({"_id":ObjectId(user_id), "role":"worker"})
    if user_check != None:
        wallet_balance =  0.0
        completed_shifts = shifts.count_documents({"provider_details.user_id":user_id, "current_status":3})
        try:
            user_cat = user_check["category"] #very important.
        except KeyError as e:
            return jsonify({"detail":{}, "message":"Kindly pick provider category user falls under", "success":False}), 400
        
        cat_shifts = list(shifts.aggregate(
            [
                {"$match":{"provider_category":user_cat,
                           "current_status":1}},
                {"$sample":{"size":5}}
            ]
            )
            )
        
        for i in cat_shifts:
            popping_items = ["provider_details", "status", "timestamp", "current_status", "tasks_list"]
            for x in popping_items:
                i.pop(x)
            
        data = {
            "wallet_balance":wallet_balance,
            "completed_shifts":completed_shifts, # this is a integer
            "avail_shifts": cat_shifts
        }
        return jsonify({"detail":data, "message":"", "success":True, "token":refresh_t}), 200
    else:
        return jsonify({"detail":{}, "message":"User not found", "success":False}), 400


@others.route("/categories", methods=["POST", "GET"])
@Authentication.token_required
def cat_sel():
    token = request.headers.get("Authorization")
    decoded_data = jwt.decode(token, secret_key,algorithms=["HS256"])
    refresh_t = Authentication.tokenExpCheck(decoded_data["exp"], decoded_data)
    try:
        user_id = decoded_data["id"]
        user_type = decoded_data["u_type"]
    except Exception:
        return jsonify({"message":unauth_mess, "success":False, "detail":{}}), 401

    user_check = users.find_one({"_id":ObjectId(user_id), "role":"worker"})
    if user_check != None:
        if request.method == "GET":
            
            it_check = misc.find_one({"tag":"categories"})
            try:
                data =  {"cat_list":it_check["categories"]}
            except Exception as e:
                data = {"cat_list":[]}
            return jsonify({"message":"", "detail":data, "success":True, "token":refresh_t}), 200
        
        if request.method == "POST":
            category = request.json.get("category_abbrv")
            if category == None or category == "":
                return jsonify({"message":"category cannot be empty", "success":False, "detail":{}, "token":refresh_t}), 400  
            users.update_one({"_id":ObjectId(user_id)}, {"$set":{"category":category}})
            cred_find = misc.find_one({"tag":"credentials"})     
            specifc_credentials = list(filter(lambda i: i["category"] == category.upper(), cred_find["cred_list"]))
            data = specifc_credentials[0]
            return jsonify({"message":"Category uploaded", "success":True, "detail":data, "token":refresh_t})


    else:
        return jsonify({"message":"user not found", "success":False, "detail":{}, "token":""}), 400

@others.route("/certificates", methods=["GET"])
@Authentication.token_required
def handle_certi():
    token = request.headers.get("Authorization")
    decoded_data = jwt.decode(token, secret_key,algorithms=["HS256"])
    refresh_t = Authentication.tokenExpCheck(decoded_data["exp"], decoded_data)
    try:
        user_id = decoded_data["id"]
        
    except Exception as e:
        return jsonify({"message":unauth_mess, "success":False, "detail":{}}), 401

    user_check = users.find_one({"_id":ObjectId(user_id), "role":"worker"})

    if user_check != None :
        check = credentials.find_one({"_id":ObjectId(user_id)})
        if check != None:
            filtered = list(filter(lambda i: [i.pop("timestamp")], check["credentials"]))
            return jsonify({"detail":{"credentials":filtered}, "token":refresh_t, "success":True, "message":""}), 200
        else:return jsonify({"message":"No credentials uploaded", "success":True, "detail":{}, "token":refresh_t}), 200        

    else:
        return jsonify({"message":"User not a service provider.", "success":False, "detail":{}}), 400


@others.route("/uploadCertificates/<cat_abbrv>", methods=["POST"])
@Authentication.token_required
def file_upload(cat_abbrv:str):
    token = request.headers.get("Authorization")
    decoded_data = jwt.decode(token, secret_key,algorithms=["HS256"])
    refresh_t = Authentication.tokenExpCheck(decoded_data["exp"], decoded_data)
    try:
        user_id = decoded_data["id"]
        user_type = decoded_data["u_type"]
    except Exception as e:
        return jsonify({"message":unauth_mess, "success":False, "detail":{}}), 401
    u_check = users.find_one({"_id":ObjectId(user_id), "role":"worker"})
    if u_check != None:
        cred_abbrv = request.args.get("cred_name")
        file_ = request.files.get("cred")
        file_type = file_.content_type.split("/")[1]

        if file_type not in ALLOWED_EXTENSIONS:
            return {
                "detail":{},
                "message":f"file format '{file_type}' not supported",
                "success":False,
                "token":refresh_t
            }, 400

        actual_file_extension = file_.filename.split(".")[1]
        
        # this part is to replace all spaces with underscores
        cred_name = cred_abbrv
        cred_abbrv = "_".join(cred_abbrv.strip().split(" "))


        file_name_to_upload = f"{str(user_id)}__{cred_abbrv}"
        file_.filename = f"{file_name_to_upload}.{actual_file_extension}"
        check = glob(os.path.join(credentials_file_upload, f"{file_name_to_upload}*"))
        if len(check) != 0:
            for i in check:
                os.remove(i)

        file_name = secure_filename(file_.filename)
        path = os.path.join(credentials_file_upload, file_name)    
        path_check = os.path.exists(credentials_file_upload)
        if path_check == False:
            os.mkdir(credentials_file_upload)
        
        file_.save(path)
        url_path = request.host_url + url_for("provider.prov_others.view_file",filename = file_.filename)

        date = datetime.utcnow()
        timestamp = datetime.timestamp(date)
        date = str(date.date())
        
        data = {
            "cert_url":url_path,
            "cert_name":cred_name,
            "date":date,
            "timestamp":timestamp,
            "verified":False,
            "c_id":0
        }
        
        cred_check = credentials.find_one({"_id":ObjectId(user_id)})
        if cred_check != None:
            spec_cred = list(filter(lambda i:i["cert_name"]==cred_name,cred_check["credentials"]))
            if len(spec_cred) == 0:
                data["c_id"] = len(cred_check["credentials"])
                credentials.update_one({"_id":ObjectId(user_id)}, {"$push":{"credentials":data}})
            else:
                credentials.update_one({"_id":ObjectId(user_id), "credentials.cert_name":cred_name}, 
                                    {"$set":{"credentials.$.date":data["date"], 
                                                "credentials.$.timestamp":data["timestamp"], 
                                                "credentials.$.verified":False,
                                                "credentials.$.cert_url":url_path}})   
        else:
            credentials.insert_one({"_id":ObjectId(user_id), "credentials":[data]})
        return jsonify({"message":"Credential uploaded", "success":True, "detail":{}, "token":refresh_t}), 200
    else:
        return {
                "detail":{},
                "message":"User not found",
                "success":False,
                "token":""
            }, 404
    
@others.route("/viewfile/<filename>", methods=["GET"])
def view_file(filename):
    return send_from_directory(credentials_file_upload,filename)


@others.route("/profile_info", methods = ["GET", "POST"])
@Authentication.token_required
def profile():
    token = request.headers.get("Authorization")
    decoded_data = jwt.decode(token, secret_key,algorithms=["HS256"])
    refresh_t = Authentication.tokenExpCheck(decoded_data["exp"], decoded_data)
    try:
        user_id = decoded_data["id"]
        
    except Exception as e:
        return jsonify({"message":unauth_mess, "success":False, "detail":{}}), 401

    user_check = users.find_one({"_id":ObjectId(user_id), "role":"worker"})
    if user_check != None:
        if request.method == "POST":
            pass
        if request.method == "GET":
            data = {
                "FName":user_check["FName"],
                "LName":user_check["LName"],
                "email":user_check["email"],
                "phone_no":user_check["contact_info"]["phone"]
            }
    else:
        return