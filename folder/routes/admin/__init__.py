from flask import Blueprint
from folder.routes.admin.others import admin_others

admin = Blueprint("admin", __name__)

admin.register_blueprint(admin_others)