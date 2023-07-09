from flask import Blueprint
from folder.routes.patients.auth import auth
from folder.routes.patients.medical_info import medicals
from folder.routes.patients.users import base_user
# from folder.routes.patients.auth import auth
# from folder.routes.patients.auth import auth

patient = Blueprint("patient", __name__)

patient.register_blueprint(auth)
patient.register_blueprint(medicals)
patient.register_blueprint(base_user)