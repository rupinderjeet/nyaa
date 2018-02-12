import functools
import re

import flask
from sqlalchemy import desc

from nyaa import models

app = flask.current_app
api_v3_blueprint = flask.Blueprint('api-v3', __name__, url_prefix='/api/v3')


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
            return flask.jsonify({'errors': ['Bad authorization']}), 403
        return f(*args, **kwargs)

    return decorator

def safe_print(message):
    print('[debug][local]: {0}'.format(message))

def error(message, status_code=400):
    safe_print('[{0}] {1}'.format(message, status_code))
    return flask.jsonify({'errors': [message]}), status_code

###################### API ROUTES ########################

ID_PATTERN = '^[0-9]+$'
PAGE_NUMBER_PATTERN = '^[0-9]+$'
INFO_HASH_PATTERN = '^[0-9a-fA-F]{40}$'  # INFO_HASH as string

MAX_PAGE_LIMIT = 1000

##############################################
#              Categories
###############################################

@api_v3_blueprint.route('/categories', methods=['GET'])
# @basic_auth_user
# @api_require_user
def v3_api_categories():

    """
    Used to fetch categories

    - no pagination required
    - no params required

    :return: a collection of categories as JSON

    see sample_categories.json
    """

    categories_result = models.MainCategory.query

    if not categories_result:
        return error('Categories not found.')

    # Method 1
    categories = []
    for category in categories_result:

        sub_categories = []

        if category and category.sub_categories:
            for sub_category in category.sub_categories:

                if sub_category:
                    sub_categories.append(
                        {
                            'id': sub_category.id,
                            'name': sub_category.name,
                            'id_as_string': sub_category.id_as_string
                        }
                    )

        main_category_metadata = {
            'id': category.id,
            'name': category.name,
            'id_as_string': category.id_as_string,
            'sub_categories': sub_categories
        }

        categories.append(main_category_metadata)

    # Method 2

    # categories = [
    #     {
    #         'id': category.id,
    #         'name': category.name,
    #         'id_as_string': category.id_as_string,
    #         'sub_categories': [
    #             {
    #                 'id': sub_category.id,
    #                 'id_as_string': sub_category.id_as_string,
    #                 'name': sub_category.name
    #             } for sub_category in category.sub_categories
    #             # TODO: how to check if category.sub_categories is None or not?
    #         ]
    #     } for category in categories_result
    #     # TODO: how to check if category is None or not?
    # ]

    return flask.jsonify(categories), 200

##############################################
#              Torrent Comments
###############################################

COMMENTS_PER_PAGE = 3
@api_v3_blueprint.route('/info/<id>/comments/', methods=['GET'])
@api_v3_blueprint.route('/info/<id>/comments/<page>', methods=['GET'])
# @basic_auth_user
# @api_require_user
def v3_api_torrent_comments(id, page=-1):

    """
    Used to fetch comments on a torrent

    comments/     : returns all data at once (same as comments/0)
    comments/page : returns data from mentioned page number

    :param id: ID of the torrent for which you want to get comments
    :param page: (optional) Page number of the comment list
    :return: found comments as JSON

    see sample_comments.json
    """

    id_match = re.match(ID_PATTERN, id)
    if not id_match:
        return error('Torrent id was not a valid id.')

    # check if this torrent is deleted
    viewer = flask.g.user
    torrent = models.Torrent.by_id(id)
    if (torrent and torrent.deleted) and not (viewer and viewer.is_superadmin):
        # this torrent is deleted and viewer is not an admin
        return error('Query was not a valid id or hash.')

    if page == -1:
        page = None
    else:
        page_match = re.match(PAGE_NUMBER_PATTERN, str(page))
        if page_match:
            page = int(page)

            # (page < 0) check is performed by regex pattern already
            if page > MAX_PAGE_LIMIT:
                return error('Maximum pagination limit reached.')

        else:
            return error('Page Number was not a valid integer.')

    comments_result = models.Comment.query\
        .filter_by(torrent_id=id)\
        .order_by(desc(models.Comment.id))

    if page:
        comments_result = comments_result.paginate(page, COMMENTS_PER_PAGE, error_out=False).items

    if not comments_result:
        return error('No data found')

    comments = [
        {
            'id': comment.id,

            # I think this statement is heavy on performance
            'user': {
                'id': comment.user_id,
                'name': models.User.by_id(comment.user_id).username
            },

            'text': comment.text,
            'created_time': comment.created_time,
            'edited_time': comment.edited_time
        } for comment in comments_result
    ]

    return flask.jsonify(comments), 200
