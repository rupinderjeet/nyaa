import re

import flask
from sqlalchemy import desc

from nyaa import models
from nyaa.api import metadata_science
from nyaa.api.nyaa_api import ID_PATTERN, error, PAGE_NUMBER_PATTERN, MAX_PAGE_LIMIT, COMMENTS_PER_PAGE
from nyaa.extensions import db

app = flask.current_app
comments_api_blueprint = flask.Blueprint('v3-comments', __name__, url_prefix='/api/v3')

@comments_api_blueprint.route('/info/<torrent_id>/comments/', methods=['GET'])
@comments_api_blueprint.route('/info/<torrent_id>/comments/<page>/', methods=['GET'])
# @basic_auth_user
# @api_require_user
def get_comments(torrent_id, page=-1):

    """
    Used to fetch comments on a torrent

    comments/     : returns all data at once (same as comments/0)
    comments/page : returns data from mentioned page number

    :param torrent_id: ID of the torrent for which you want to get comments
    :param page: (optional) Page number of the comment list
    :return: found comments as JSON

    see sample_comments.json
    """

    id_match = re.match(ID_PATTERN, torrent_id)
    if not id_match:
        return error('Torrent id was not a valid id.')

    # check if this torrent is deleted
    viewer = flask.g.user
    torrent = models.Torrent.by_id(torrent_id)
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
        .filter_by(torrent_id=torrent_id)\
        .order_by(desc(models.Comment.id))

    if page:
        comments_result = comments_result.paginate(page, COMMENTS_PER_PAGE, error_out=False).items

    if not comments_result:
        return error('No data found')

    comments = []
    if comments_result:

        for comment in comments_result:
            if comment:

                comment_metadata = metadata_science.get_comment_metadata(comment)
                comments.append(comment_metadata)

    return flask.jsonify(comments), 200

@comments_api_blueprint.route('/info/<torrent_id>/comment/add', methods=['POST'])
# @basic_auth_user
# @api_require_user
def add_comment (torrent_id):

    """
    Used to add comment on a torrent

    :param torrent_id: ID of the torrent on which you want to add comment
    :arg text: comment text
    :return: added comment as JSON, or bunch of errors

    see sample_comments_add.json

    TODO: check if comments are disabled:
    """

    viewer = flask.g.user

    if not viewer:
        return error('Not allowed.', 403)

    torrent = models.Torrent.by_id(torrent_id)
    if not torrent:
        return error('Torrent not found.', 404)

    # check if this torrent is deleted
    if torrent.deleted and not viewer.is_superadmin:
        # this torrent is deleted and viewer is not an admin
        return error('Torrent not found.', 404)

    comment_text = flask.request.form.get('text', default="", type=str)
    if not comment_text or len(comment_text) == 0:
        return error("Comment can\'t be empty.", 403)

    comment = models.Comment
    comment.torrent_id = torrent.id
    comment.user_id = 1                 # TODO change to viewer.id (or flask.g.user.id)
    comment.text = comment_text

    db.session.add(comment)
    db.session.flush()
    torrent.update_comment_count()
    db.session.commit()

    return flask.jsonify(metadata_science.get_comment_metadata(comment)), 201

@comments_api_blueprint.route('/info/<torrent_id>/comment/edit', methods=['POST'])
@comments_api_blueprint.route('/info/<torrent_id>/comment/edit/<comment_id>', methods=['POST'])
# @basic_auth_user
# @api_require_user
def edit_comment (torrent_id, comment_id=-1):

    """
    Used to edit comment on a torrent

    :param (in url) torrent_id: ID of the torrent from which you want to delete comment
    :param comment_id: ID of the comment to be deleted
    :arg text: new text for this comment
    :return: deleted comment as JSON, or bunch of errors

    see sample_comments_edit.json
    """

    if comment_id is -1:
        return error('Comment ID not found in request.', 400)

    viewer = flask.g.user
    if not viewer:
        return error('Not allowed.', 403)

    torrent = models.Torrent.by_id(torrent_id)
    if not torrent:
        return error('Torrent not found.', 404)

    comment = models.Comment.query.get(comment_id)
    if not comment:
        return error('Comment not found.', 404)

    if not comment.user.id == flask.g.user.id:
        return error('Not allowed.', 403)

    if comment.editing_limit_exceeded:
        return error('Editing time limit exceeded.', 400)

    new_text = flask.request.form.get('text', default="", type=str)
    if not new_text or len(new_text) == 0:
        return error('Comment can\'t be empty.', 400)

    comment.text = new_text
    db.session.commit()

    return flask.jsonify(metadata_science.get_comment_metadata(comment)), 200