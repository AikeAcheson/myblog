from flask import Blueprint
from ..models import Permission

main = Blueprint('main', __name__)

from . import views, errors


# Context processors make variables available to all templates during rendering.
@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)
