from flask import Blueprint
# from folder.routes.auth import auth
from folder.routes.providers.others import others

provider = Blueprint("provider", __name__)

provider.register_blueprint(others)
