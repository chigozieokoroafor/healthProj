from flask import Blueprint
# from folder.routes.auth import auth
from folder.routes.providers.others import others
from folder.routes.providers.shifts import prov_shifts

provider = Blueprint("provider", __name__)

provider.register_blueprint(others)
provider.register_blueprint(prov_shifts)
