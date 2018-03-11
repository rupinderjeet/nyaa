"""
    This file keeps response structure in here
    so that, we can change it here and reflect it everywhere else \
        where same model is used
"""

def get_parent_category_metadata(category, sub_categories) :

    if not category:
        return None

    return {
        # 'id': category.id,
        'name': category.name,
        'id_as_string': category.id_as_string,
        'sub_categories': sub_categories
    }

def get_sub_category_metadata(sub_category) :

    if not sub_category:
        return None

    return {
        # 'id': category.id,
        'name': sub_category.name,
        'id_as_string': sub_category.id_as_string,
    }

def get_comment_metadata(comment, comment_author) :

    if not comment:
        return None

    comment_author_metadata = None
    if comment_author:
        comment_author_metadata = {
            'id': comment_author.id,
            'name': comment_author.username
        }

    return {
        'id': comment.id,
        'author': comment_author_metadata,
        'text': comment.text,
        'created_at': comment.created_time,
        'edited_at': comment.edited_time
    }