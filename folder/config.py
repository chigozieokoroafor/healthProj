from  pymongo import MongoClient
from dotenv import load_dotenv
import os 


load_dotenv("./.env")

connection_string = os.getenv("connect_string")



client = MongoClient(connection_string)
db = client["healthManager"]
users = db["users"]