from flask import Blueprint, request, jsonify, send_from_directory, url_for
from folder.functions import Authentication, secret_key, unauth_mess
from bson import ObjectId
from folder.config import *
import jwt
from datetime import datetime
from werkzeug.utils import secure_filename
import pathlib
from urllib.parse import urlparse, urlunparse



others =  Blueprint("prov_others", __name__)
ALLOWED_EXTENSIONS = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}



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

@others.route("/certificates", methods=["GET", "POST", "PUT"])
@Authentication.token_required
def handle_certi():
    token = request.headers.get("Authorization")
    decoded_data = jwt.decode(token, secret_key,algorithms=["HS256"])
    refresh_t = Authentication.tokenExpCheck(decoded_data["exp"], decoded_data)
    try:
        user_id = decoded_data["id"]
        # user_type = decoded_data["u_type"]
    except Exception as e:
        return jsonify({"message":unauth_mess, "success":False, "detail":{}}), 401

    user_check = users.find_one({"_id":ObjectId(user_id), "role":"worker"})
    cred_check = credentials.find_one({"_id":ObjectId(user_id)})

    if user_check != None :
        if request.method == "GET":
            check = credentials.find_one({"_id":ObjectId(user_id)})
            if check != None:
                filtered = list(filter(lambda i: [i.pop("timestamp")], check["credentials"]))
                return jsonify({"detail":{"credentials":filtered}, "token":refresh_t, "success":True, "message":""}), 200
            else:return jsonify({"message":"No credentials uploaded", "success":True, "detail":{}, "token":refresh_t}), 200
        
        if request.method == "POST":
            info = request.json
            cert_url = info.get("cert_url")
            cert_name = info.get("cert_name")
            date = datetime.utcnow()
            timestamp = datetime.timestamp(date)
            date = str(date.date())
            data = {
                "cert_url":cert_url,
                "cert_name":cert_name,
                "date":date,
                "timestamp":timestamp,
                "verified":False,
                "c_id":0
            }
            
            if cred_check != None:
                data["c_id"] = len(cred_check["credentials"])
                credentials.update_one({"_id":ObjectId(user_id)}, {"$push":{"credentials":data}})
            else:
                credentials.insert_one({"_id":ObjectId(user_id), "credentials":[data]})
            return jsonify({"message":"Credential uploaded", "success":True, "detail":{}, "token":refresh_t}), 200
        
# fix this request
# it is n't being updated

        if request.method == "PUT":
            info = request.json
            ls = ["cert_url", "cert_name"]
            data = {}
            for i in ls:
                if info.get(i) != "" and info.get (i) != None:
                    data["credentials.$."+i] =  info[i]
            date = datetime.utcnow()
            data["credentials.$.timestamp"] = datetime.timestamp(date)
            data["credentials.$.date"] = str(date.date())

            c_id =  info.get("c_id")   
            check = list(filter(lambda i: [i["c_id"] == int(c_id), i["verified"]==True], cred_check["credentials"]))
            
            if len(check) == 0:
                updated_data = credentials.find_one_and_update({"_id":ObjectId(user_id), "credentials.c_id":int(c_id)}, {"$set":data})           
                new_update = list(filter(lambda i: i["c_id"] == int(c_id), updated_data["credentials"]))
            
                return jsonify({"message":"", "success":True, "detail":{"updated_":new_update[0]}, "token":refresh_t}), 200
            else:
                return jsonify({"message":"Credential cannot be updated, kindly message our customer care email", "success":False, "detail":{}, "token":refresh_t}), 400
            
            
    else:
        return jsonify({"message":"User not a service provider.", "success":False, "detail":{}}), 400

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
            category = request.json.get("category")
            if category == None or category == "":
                return jsonify({"message":"category cannot be empty", "success":False, "detail":{}, "token":refresh_t}), 400  
            users.update_one({"_id":ObjectId(user_id)}, {"$set":{"category":category}})      
            return jsonify({"message":"Category uploaded", "success":True, "detail":{}, "token":refresh_t})


    else:
        return jsonify({"message":"user not found", "success":False, "detail":{}, "token":""}), 400

@others.route("/uploadFile", methods=["POST"])
def file_upload():
    file_ = request.files.get("cred")
    # file_.filename = "new_x.jpg"
    file_name = secure_filename(file_.filename)
    path_check = os.path.exists(credentials_file_upload)
    if path_check == False:
        os.mkdir(credentials_file_upload)
    path = os.path.join(credentials_file_upload, file_name)
    # url_path = pathlib.Path(path).as_uri()
    # print(os.path.exists(path))
    # print(urlunparse(urlparse(url_path)._replace(scheme="file")))
    # misc.insert_one({"path":url_path})
    file_.save(path)
    url_path = url_for("provider.prov_others.view_file",filename = file_.filename, external=True)
    return {
        "detail":{},
        "message":url_path,
        "success":True
    }

@others.route("/viewfile/<filename>", methods=["GET"])
def view_file(filename):
    return send_from_directory(credentials_file_upload,filename)

# @others.route("/viewFile")
# def view_file():
#     absolute_path_string = os.path.join(credentials_file_upload, "new_x.jpg")
#     # x = send_from_directory(credentials_file_upload, )
#     url_path = pathlib.Path(absolute_path_string).as_uri()
#     return {
#         "detail":{},
#         "message":url_path,
#         "success":True
#     }

# @app.route('/upFile', methods=['GET', 'POST'])
# def upload_file():
#     if request.method == 'POST':
#         # check if the post request has the file part
#         if 'file' not in request.files:
#             return "false", 400
#         file = request.files['file']
#         # If the user does not select a file, the browser submits an
#         # empty file without a filename.
#         if file.filename == '':
#             return "false", 400
#         if file and allowed_file(file.filename):
#             filename = secure_filename(file.filename)
#             file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
#             return redirect(url_for('download_file', name=filename))

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