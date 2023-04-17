from flask import Flask
from flask_cors import CORS
from folder.functions import secret_key
from folder.routes.auth import auth
from folder.routes.users import base_user
from folder.routes.medical_info import medicals
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

app.register_blueprint(auth)
app.register_blueprint(base_user)
app.register_blueprint(medicals)