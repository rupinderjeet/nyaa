import json
import math
import re

import flask

from nyaa import models
from nyaa.api import metadata_science, API_URL_PREFIX, ID_PATTERN
from nyaa.search import (DEFAULT_MAX_SEARCH_RESULT, DEFAULT_PER_PAGE,
                         search_db, search_elastic)
from nyaa.utils import chain_get
from nyaa.api.base_api import error

app = flask.current_app
torrents_api_blueprint = flask.Blueprint('v3-torrents', __name__, url_prefix=API_URL_PREFIX)


@torrents_api_blueprint.route('/browse/', methods=['GET'])
# @basic_auth_user
# @api_require_user
def browse():

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

    search_term = chain_get(req_args, 'q', 'term')

    # sorting
    sort_key = chain_get(req_args, 's', 'sort_by')
    sort_order = chain_get(req_args, 'o', 'sort_order')

    category = chain_get(req_args, 'c', 'cats')
    quality_filter = chain_get(req_args, 'f', 'filter')

    # torrents by a user
    user_name = chain_get(req_args, 'u', 'user')

    # page number
    page_number = chain_get(req_args, 'p', 'page')
    try:
        page_number = max(1, int(page_number))
    except (ValueError, TypeError):
        page_number = 1

    # Check simply if the key exists
    use_magnet_links = 'magnets' in req_args or 'm' in req_args

    results_per_page = app.config.get('RESULTS_PER_PAGE', DEFAULT_PER_PAGE)

    user_id = None
    if user_name:
        user = models.User.by_username(user_name)
        if not user:
            flask.abort(404)
        user_id = user.id

    # TODO: understand this first
    # special_results = {} @see views/main.py

    query_args = {
        'user': user_id,
        # 'term': search_term or '',
        'sort': sort_key or 'id',
        'order': sort_order or 'desc',
        'category': category or '0_0',
        'quality_filter': quality_filter or '0',
        'page': page_number,
        'per_page': results_per_page
    }

    """
    # not needed I think (for now)
    # we're not supporting admin features yet

    if flask.g.user:
        query_args['logged_in_user'] = flask.g.user
        if flask.g.user.is_moderator:  # God mode
            query_args['admin'] = True
    """

    # If searching, we get results from elastic search
    use_elastic = app.config.get('USE_ELASTIC_SEARCH')

    if use_elastic and search_term:
        query_args['term'] = search_term
        return browse_es(query_args)

    else:
        query_args['term'] = search_term or ''
        return browse_db(query_args)


@torrents_api_blueprint.route('/info/<torrent_id>/', methods=['GET'])
# @basic_auth_user
# @api_require_user
def get_torrent_info(torrent_id):

    """
    Used to fetch information about a torrent

    :param torrent_id: ID of the torrent whose information is required
    :return: found information as JSON

    see sample_torrent_info.json

    TODO: match by torrent_hash
    TODO: improve error messages
    """

    id_match = re.match(ID_PATTERN, torrent_id)
    if not id_match:
        return error('Torrent id was not a valid id.')

    torrent = models.Torrent.by_id(torrent_id)
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
    torrent_metadata = metadata_science.get_torrent_metadata(torrent, submitter)
    return flask.jsonify(torrent_metadata), 200


@torrents_api_blueprint.route('/info/<torrent_id>/files/', methods=['GET'])
# @basic_auth_user
# @api_require_user
def v3_api_torrent_files(torrent_id):

    """
    Used to fetch list of files in a torrent

    -- pagination not required (not supported too, I think)

    :param torrent_id: ID of the torrent for which you want to get list of files
    :return: found list of files in Json stacked as a folder-structure

    see sample_files.json
    """

    id_match = re.match(ID_PATTERN, torrent_id)
    if not id_match:
        return error('Torrent id was not a valid id.')

    # check if this torrent is deleted
    viewer = flask.g.user
    torrent = models.Torrent.by_id(torrent_id)
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


###########################################

def browse_es(query_args):

    results_per_page = query_args['per_page']
    max_search_results = app.config.get('ES_MAX_SEARCH_RESULT', DEFAULT_MAX_SEARCH_RESULT)

    # Only allow up to (max_search_results / page) pages
    max_page = min(query_args['page'], int(math.ceil(max_search_results / results_per_page)))

    query_args['page'] = max_page
    query_args['max_search_results'] = max_search_results

    query_results = search_elastic(**query_args)
    json_result = json.loads(json.dumps(query_results.to_dict()))

    result = metadata_science.get_es_torrent_list_metadata(json_result, query_args)
    return flask.jsonify(result), 200

def browse_db(query_args):

    """
    Used only if elastic search is disabled.
    """

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