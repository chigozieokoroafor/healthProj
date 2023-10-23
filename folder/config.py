from dotenv import load_dotenv
import os, pymongo


load_dotenv("./.env")

connection_string = os.getenv("connect_string")

statuses = {
    1: "Available", 
    2: "Unavailable", # this are tasks that have been picked
    3: "Completed" #, # for completed tasks
    # 4: "Picked" # this are tasks that have been picked
}
client = pymongo.MongoClient(connection_string)
db = client["healthManager"]
users = db["users"]
medical_info = db["medRecords"]
credentials =  db["cred"]
shifts = db["jobs"]
misc =  db["misc"]
exp_cert = db["exp_cert"]

users.create_index("email", unique=True)

default_image_url = "https://res.cloudinary.com/dgpnmwhra/image/upload/v1674042300/neutron_images/base_photo_rqyzlb.png"
credentials_file_upload = os.getcwd()+"/folder/credentials"
