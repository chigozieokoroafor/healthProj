from flask import Blueprint
# from folder.routes.auth import auth
from folder.routes.patients.medical_info import medicals
from folder.routes.patients.users import base_user
from folder.routes.patients.jobs import user_jobs


patient = Blueprint("patient", __name__)

# patient.register_blueprint(auth)
patient.register_blueprint(medicals)
patient.register_blueprint(base_user)
patient.register_blueprint(user_jobs)