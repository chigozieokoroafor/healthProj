from  pymongo import MongoClient
from dotenv import load_dotenv
import os 


load_dotenv("./.env")

connection_string = os.getenv("connect_string")

statuses = {
    1: "Available",
    2: "Unavailable", # this are tasks that have been picked
    3: "Completed", # for completed tasks
    4: ""
}

client = MongoClient(connection_string)
db = client["healthManager"]
users = db["users"]
medical_info = db["medRecords"]
credentials =  db["cred"]
shifts = db["jobs"]
misc =  db["misc"]
exp_cert = db["exp_cert"]
