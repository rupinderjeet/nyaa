import functools

import flask

from nyaa import models
from nyaa.api import metadata_science, API_URL_PREFIX

app = flask.current_app
base_api_blueprint = flask.Blueprint('v3-base', __name__, url_prefix=API_URL_PREFIX)


# #################################### API HELPERS ####################################

def basic_auth_user(f):
    ''' A decorator that will try to validate the user into g.user from basic auth.
        Note: this does not set user to None on failure, so users can also authorize
        themselves with the cookie (handled in views.main.before_request). '''

    @functools.wraps(f)
    def decorator(*args, **kwargs):
        auth = flask.request.authorization
        if auth:
            user = models.User.by_username_or_email(auth.get('username'))
            if user and user.validate_authorization(auth.get('password')):
                flask.g.user = user

        return f(*args, **kwargs)

    return decorator

def api_require_user(f):
    ''' Returns an error message if flask.g.user is None.
        Remember to put after basic_auth_user. '''

    @functools.wraps(f)
    def decorator(*args, **kwargs):
        if flask.g.user is None:
            return error('Bad authorization', 403)
        return f(*args, **kwargs)

    return decorator

def api_require_superadmin(f):
    ''' Returns an error message if flask.g.user is not superadmin.
        Remember to put after api_require_user. '''

    @functools.wraps(f)
    def decorator(*args, **kwargs):

        if not flask.g.user.is_superadmin:
            return error('You\'re not super admin.', 403)
        return f(*args, **kwargs)

    return decorator

def safe_print(message):
    print('[debug][local]: {0}'.format(message))

def error(message, status_code=400):
    safe_print('[{0}] {1}'.format(message, status_code))
    return flask.jsonify({'errors': [message]}), status_code

###################### API ROUTES ########################

@base_api_blueprint.route('/', methods=['GET'])
# @basic_auth_user
# @api_require_user
def get_endpoints():
    return flask.jsonify(metadata_science.get_endpoints_metadata()), 200
