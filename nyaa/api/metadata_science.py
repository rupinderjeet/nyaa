def get_comment_metadata(comment, comment_author) :

    if not comment:
        return {}

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