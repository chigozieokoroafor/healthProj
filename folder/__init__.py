from flask import Flask
from flask_cors import CORS
from folder.functions import secret_key
from folder.routes.admin import admin
from folder.routes.patients import patient
from folder.routes.providers import provider
# from flask_mail import Mail

app = Flask(__name__)

app.config["SECRET_KEY"] = secret_key
# app.config['MAIL_SERVER'] = 'smtp.gmail.com'
# app.config['MAIL_PORT'] = 465
# app.config['MAIL_USE_SSL'] = True
# app.config['MAIL_USERNAME'] = "okoroaforc14@gmail.com"
# app.config['MAIL_PASSWORD'] = "weydnmjumtbtzvln"

CORS(app)
# Mail(app)

app.register_blueprint(admin, url_prefix="/api/admin")
app.register_blueprint(patient, url_prefix="/api/patient")
app.register_blueprint(provider, url_prefix="/api/provider")