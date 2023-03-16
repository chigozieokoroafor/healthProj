from flask import Flask
from flask_cors import CORS
from folder.functions import secret_key
from folder.routes.auth import auth

app = Flask(__name__)

app.config["SECRET_KEY"] = secret_key

CORS(app)

app.register_blueprint(auth)