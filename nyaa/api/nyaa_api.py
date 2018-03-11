import functools
import json
import re

import flask
from sqlalchemy import desc

from nyaa import models
from nyaa.api import metadata_science
from nyaa.extensions import db
from nyaa.search import DEFAULT_PER_PAGE, search_db
from nyaa.utils import chain_get

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

@api_v3_blueprint.route('/categories/', methods=['GET'])
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

    categories = []
    for category in categories_result:

        sub_categories = []

        if category and category.sub_categories:

            for sub_category in category.sub_categories:
                if sub_category:
                    sub_categories.append(
                        metadata_science.get_category_metadata(sub_category)
                    )

        main_category_metadata = metadata_science.get_category_metadata(category, sub_categories)
        categories.append(main_category_metadata)

    return flask.jsonify(categories), 200


##############################################
#              Browse Torrents
###############################################

TORRENTS_PER_PAGE = 40

@api_v3_blueprint.route('/browse/', methods=['GET'])
# @basic_auth_user
# @api_require_user
def v3_api_browse():

    """
    Used to browse and search torrents

    - 'page=rss' argument is not allowed

    :param:optional argument: q = your search keyword
    :param:optional argument: f = filter selection
    :param:optional argument: c = category selection
    :param:optional argument: p = page number
    :param:optional argument: s = sort key
    :param:optional argument: o = sort order
    :param:optional argument: u = limit search to torrents uploaded by specific user

    :return: a collection of found torrents and a list of applied arguments as JSON

    see sample_browse_torrents.json

    TODO: add show__ arguments to reduce json
    """

    req_args = flask.request.args
    if req_args.get('page') == 'rss':
        return error('RSS is not allowed from this API.')

    search_term = chain_get(req_args, 'q')
    quality_filter = chain_get(req_args, 'f')
    category = chain_get(req_args, 'c')

    # Page Number
    page_number = chain_get(req_args, 'p')
    try:
        page_number = max(1, int(page_number))
    except (ValueError, TypeError):
        page_number = 1

    # Sorting
    sort_key = chain_get(req_args, 's', 'sort_by')
    sort_order = chain_get(req_args, 'o', 'sort_order')

    # torrents by a user
    user_name = req_args.get('u')

    # Check simply if the key exists
    use_magnet_links = 'magnets' in req_args or 'm' in req_args

    results_per_page = app.config.get('RESULTS_PER_PAGE', DEFAULT_PER_PAGE)

    user_id = None
    if user_name:
        user = models.User.by_username(user_name)
        if not user:
            flask.abort(404)
        user_id = user.id

    query_args = {
        'term': search_term or '',
        'user': user_id,
        'sort': sort_key or 'id',
        'order': sort_order or 'desc',
        'category': category or '0_0',
        'quality_filter': quality_filter or '0',
        'page': page_number,
        'per_page': results_per_page
    }

    """
    # not needed I think (for now)

    if flask.g.user:
        query_args['logged_in_user'] = flask.g.user
        if flask.g.user.is_moderator:  # God mode
            query_args['admin'] = True
    """

    # TODO : use as legacy_fallback | shift to ES
    query = search_db(**query_args)
    # change p= argument to whatever you change page_parameter to or pagination breaks

    torrents = []
    if query.items:

        for torrent in query.items:

            if torrent:
                torrent_metadata = metadata_science.get_torrent_metadata(torrent)
                torrents.append(torrent_metadata)

    result = metadata_science.get_torrent_list_metadata(torrents, query_args)
    return flask.jsonify(result), 200

##############################################
#              Torrent Info
###############################################

@api_v3_blueprint.route('/info/<id>/', methods=['GET'])
# @basic_auth_user
# @api_require_user
def v3_api_torrent_info(id):

    """
    Used to fetch information about a torrent

    :param id: ID of the torrent whose information is required
    :param category_as_model: should return category as model or plain_data, default false
    :return: found information as JSON

    see sample_torrent_info.json

    TODO: match by torrent_hash
    TODO: improve error messages
    """

    # enable if has any value assigned to it, lazy for bool-cast
    category_as_model = flask.request.args.get('category_as_model')

    id_match = re.match(ID_PATTERN, id)
    if not id_match:
        return error('Torrent id was not a valid id.')

    torrent = models.Torrent.by_id(id)
    if not torrent:
        return error('Query was not a valid id or hash.')

    viewer = flask.g.user

    # Only allow admins see deleted torrents
    if torrent.deleted and not (viewer and viewer.is_superadmin):
        return error('Query was not a valid id or hash.')

    submitter = None
    if not torrent.anonymous and torrent.user:
        # a user submitted the torrent, and chose not to be anonymous
        submitter = torrent.user
    if torrent.user and (viewer == torrent.user or viewer.is_moderator):
        # a user submitted the torrent,
        # and either he himself or a moderator is trying to view this torrent
        submitter = torrent.user

    # Create a response dict with relevant data
    torrent_metadata = metadata_science.get_torrent_metadata(torrent, submitter, category_as_model)
    return flask.jsonify(torrent_metadata), 200

##############################################
#              Torrent Comments
###############################################

COMMENTS_PER_PAGE = 3
@api_v3_blueprint.route('/info/<id>/comments/', methods=['GET'])
@api_v3_blueprint.route('/info/<id>/comments/<page>/', methods=['GET'])
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

    comments = []
    if comments_result:

        for comment in comments_result:
            if comment:

                # I think this statement is heavy on performance
                comment_author = None
                if comment.user_id:
                    comment_author = models.User.by_id(comment.user_id)

                comment_metadata = metadata_science.get_comment_metadata(comment, comment_author)
                comments.append(comment_metadata)

    return flask.jsonify(comments), 200


##############################################
#              Torrent : Add Comments
###############################################

@api_v3_blueprint.route('/info/<id>/comments/add', methods=['POST'])
# @basic_auth_user
# @api_require_user
def v3_api_torrent_add_comment (id):

    """
    Used to add comment on a torrent

    :param (in url) id: ID of the torrent on which you want to add comment
    :param comment: comment text
    :return: added comment as JSON, or bunch of errors

    see sample_comments_add.json

    TODO: check if comments are disabled:
    """

    id_match = re.match(ID_PATTERN, id)
    if not id_match:
        return error('Torrent id was not a valid id.', 404)

    viewer = flask.g.user
    # if not viewer:
    #     return error('You are not logged in, probably.', 403)
    #
    # check if this torrent is deleted
    torrent = models.Torrent.by_id(id)
    if (torrent and torrent.deleted) and not viewer.is_superadmin:
        # this torrent is deleted and viewer is not an admin
        return error('Torrent does not exist.', 404)

    comment_text = flask.request.form.get('comment', default="", type=str)
    if not comment_text:
        return error("Can't add empty comment.", 403)

    comment = models.Comment(
        torrent_id=torrent.id,
        user_id=1, # TODO change to flask.g.user.id
        text=comment_text
    )

    db.session.add(comment)
    db.session.flush()

    # What does this do?
    torrent_count = torrent.update_comment_count()
    db.session.commit()

    comment_author = None
    if comment.user_id:
        comment_author = models.User.by_id(comment.user_id)

    comment_metadata = metadata_science.get_comment_metadata(comment, comment_author)
    return flask.jsonify(comment_metadata), 201

##############################################
#              Torrent Files
###############################################

@api_v3_blueprint.route('/info/<id>/files/', methods=['GET'])
# @basic_auth_user
# @api_require_user
def v3_api_torrent_files(id):

    """
    Used to fetch list of files in a torrent

    -- pagination not required (not supported too, I think)

    :param id: ID of the torrent for which you want to get list of files
    :return: found list of files in Json stacked as a folder-structure

    see sample_files.json
    """

    id_match = re.match(ID_PATTERN, id)
    if not id_match:
        return error('Torrent id was not a valid id.')

    # check if this torrent is deleted
    viewer = flask.g.user
    torrent = models.Torrent.by_id(id)
    if not torrent:
        return error('Query was not a valid id or hash.')

    if torrent.deleted and not (viewer and viewer.is_superadmin):
        # this torrent is deleted and viewer is not an admin
        return error('Query was not a valid id or hash.')

    # TODO: maybe use direct model
    # files_result = models.TorrentFilelist.query.filter_by(torrent_id=id)
    file_list = torrent.filelist # does the overuse cause memory/performance issues?
    if file_list:

        decoded_file_list = file_list.filelist_blob.decode('utf-8')
        return flask.jsonify(json.loads(decoded_file_list)), 200
    else:
        return error('Unable to get file list for this torrent.')