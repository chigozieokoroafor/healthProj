from  pymongo import MongoClient
from dotenv import load_dotenv
import os 


load_dotenv("./.env")

connection_string = os.getenv("connect_string")

client = MongoClient(connection_string)
db = client["healthManager"]
users = db["users"]
medical_info = db["medRecords"]
credentials =  db["cred"]
shifts = db["jobs"]
misc =  db["misc"]
exp_cert = db["exp_cert"]
