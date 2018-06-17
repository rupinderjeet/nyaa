import flask

from nyaa import models
from nyaa.extensions import db
from nyaa.api import metadata_science
from nyaa.api.nyaa_api import error

app = flask.current_app
categories_api_blueprint = flask.Blueprint('v3-categories', __name__, url_prefix='/api/v3')

@categories_api_blueprint.route('/categories/', methods=['GET'])
# @basic_auth_user
# @api_require_user
def get_categories():

    """
    Used to fetch categories

    - no pagination required
    - no params required

    :return: a collection of categories as JSON
    """

    # TODO: add this setting to request_args later
    show_subcategories = True

    categories_result = models.MainCategory.query

    if not categories_result:
        return error('Categories not found.')

    categories = []
    for category in categories_result:

        sub_categories = None
        if category and category.sub_categories and show_subcategories:

            sub_categories = []
            for sub_category in category.sub_categories:
                if sub_category:
                    sub_categories.append(
                        metadata_science.get_category_metadata(sub_category)
                    )

        main_category_metadata = metadata_science.get_category_metadata(category, sub_categories)
        categories.append(main_category_metadata)

    return flask.jsonify(categories), 200


@categories_api_blueprint.route('/categories/add/', methods=['POST'])
# @basic_auth_user
# @api_require_user
# @api_require_superadmin
def add_main_category ():

    """
    Used to add a new category

    :arg category_name: name of new category
    :return: added category, or bunch of errors
    """

    category_name = flask.request.form.get('category_name', default="", type=str)
    if not category_name or len(category_name) == 0:
        return error("Category name is invalid.", 400)

    viewer = flask.g.user
    if not viewer or not viewer.is_superadmin():
        return error('Not allowed.', 403)

    # main_category = models.MainCategory
    # main_category.name = category_name            # TODO: capitalize the name
    #
    # db.session.add(main_category)
    # db.session.flush()
    # db.session.commit()

    # TODO: do it, then.
    return error('Sorry, can\'t do this yet', 403)

@categories_api_blueprint.route('/categories/edit/', methods=['POST'])
# @basic_auth_user
# @api_require_user
# @api_require_superadmin
def edit_main_category ():

    """
    Used to edit main category

    :arg category_id: id of existing category
    :arg category_name: new name of existing category
    :return: modified category, or bunch of errors
    """

    viewer = flask.g.user
    if not viewer or not viewer.is_superadmin():
        return error('Not allowed.', 403)

    # new name
    main_category_name = flask.request.form.get('category_name', default="", type=str)
    if not main_category_name:
        return error('Category name is invalid.', 400)

    # which category
    main_category_id = flask.request.form.get('category_id', default="", type=str)
    main_category = models.MainCategory.by_id(main_category_id)
    if not main_category:
        return error('Category not found.', 400)

    # apply new name
    main_category.name = main_category_name            # TODO: capitalize the name
    db.session.commit()

    return flask.jsonify(metadata_science.get_category_metadata(main_category)), 200


@categories_api_blueprint.route('/categories/subcategories/add/', methods=['POST'])
# @basic_auth_user
# @api_require_user
# @api_require_superadmin
def add_sub_category ():

    """
    Used to add a new subcategory

    :arg parent_category_id: id of parent category
    :arg category_name: name of new category
    :return: added category, or bunch of errors
    """

    parent_category_id = flask.request.form.get('parent_category_id', default="", type=str)
    parent_category = models.MainCategory.by_id(parent_category_id)
    if not parent_category:
        return error("Parent Category not found.", 404)

    category_name = flask.request.form.get('category_name', default="", type=str)
    if not category_name or len(category_name) == 0:
        return error("Category name is invalid.", 400)

    viewer = flask.g.user
    if not viewer or not viewer.is_superadmin():
        return error('Not allowed.', 403)

    # sub_category = models.SubCategory
    # sub_category.name = category_name            # TODO: capitalize the name
    # sub_category.main_category_id = parent_category_id
    #
    # db.session.add(sub_category)
    # db.session.flush()
    # db.session.commit()

    # TODO: do it, then.
    return error('Sorry, can\'t do this yet', 403)

@categories_api_blueprint.route('/categories/subcategories/edit/', methods=['POST'])
# @basic_auth_user
# @api_require_user
# @api_require_superadmin
def edit_sub_category ():

    """
    Used to edit sub category

    :arg main_category_id: id of existing main category
    :arg sub_category_id: id of existing sub category
    :arg new_category_name: new name of sub category
    :return: modified category, or bunch of errors
    """

    # viewer = flask.g.user
    # if not viewer or not viewer.is_superadmin():
    #     return error('Not allowed.', 403)

    # new name
    new_category_name = 'Babes' # flask.request.form.get('new_category_name', default="", type=str)
    if not new_category_name:
        return error('Category name is invalid.', 400)

    # which main_category
    main_category_id = '1' # flask.request.form.get('main_category_id', default="", type=str)
    main_category = models.MainCategory.by_id(main_category_id)
    if not main_category:
        return error('Main Category not found.', 404)

    # # which sub_category
    # sub_category_id = flask.request.form.get('sub_category_id', default="", type=str)
    # sub_category = models.SubCategory.query.get(sub_category_id, main_category_id)
    # if not sub_category:
    #     return error('Sub Category not found.', 404)

    # # apply new name
    # sub_category.name = new_category_name       # TODO: capitalize the name
    # db.session.commit()

    # TODO: do it, then.
    return error('Sorry, can\'t do this yet', 403)
