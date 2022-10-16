from flask_httpauth import HTTPBasicAuth
from flask import g, jsonify
from ..models import User
from . import api
from .errors import unauthorized, forbidden

# Because this type of user authentication will be used only in
# the API blueprint, the Flask-HTTPAuth extension is initialized
# in the blueprint package.
auth = HTTPBasicAuth()


@auth.verify_password
def verify_password(email_or_token, password):
    if email_or_token == '':
        return False
    if password == '':
        # If the password is blank, then the email_or_token field is assumed to be a token.
        g.current_user = User.verify_auth_token(email_or_token)
        # To give view functions the ability to distinguish between the two authentication methods.
        g.token_used = True
        return g.current_user is not None
    user = User.query.filter_by(email=email_or_token.lower()).first()
    if not user:
        return False
    g.current_user = user
    g.token_used = False
    return user.verify_password(password)


@auth.error_handler
def auth_error():
    return unauthorized('Invalid credentials')


@api.before_request
@auth.login_required
def before_request():
    if not g.current_user.is_anonymous and not g.current_user.confirmed:
        return forbidden('Unconfirmed account')


@api.route('/tokens/', methods=['POST'])
def get_token():
    # To prevent clients from authenticating to this route using a previously
    # obtained token instead of an email address and password, the g.token_used
    # variable is checked, and requests authenticated with a token are rejected.
    # The purpose of this is to prevent users from bypassing the token expiration
    # by requesting a new token using the old token as authentication.
    if g.current_user.is_anonymous or g.token_used:
        return unauthorized('Invalid credentials')
    return jsonify({'token': g.current_user.generate_auth_token()})
