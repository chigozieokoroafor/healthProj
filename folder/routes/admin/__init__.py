from flask import Blueprint
from folder.routes.admin.others import admin_others
from folder.routes.admin.serviceProviders import service

admin = Blueprint("admin", __name__)

admin.register_blueprint(admin_others)
admin.register_blueprint(service)