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

def get_torrent_metadata(torrent) :

    if not torrent:
        return None

    torrent_stats = None
    if torrent.stats:
        torrent_stats = {
            'seeders': torrent.stats.seed_count,
            'leechers': torrent.stats.leech_count,
            'downloads': torrent.stats.download_count
        }

    return {
        'id': torrent.id,
        'name': torrent.display_name,

        'created_at': torrent.created_time,
        'hash_b32': torrent.info_hash_as_b32,  # as used in magnet uri
        'hash_hex': torrent.info_hash_as_hex,  # .hex(), #as shown in torrent client

        'url': '', # TODO download url, later
        'magnet': torrent.magnet_uri,

        'main_category': get_parent_category_metadata(
            torrent.main_category, [get_sub_category_metadata(torrent.sub_category)]
        ),

        'information': torrent.information,
        'description': torrent.description,
        'stats': torrent_stats,
        'filesize': torrent.filesize,

        'is_trusted': torrent.trusted,
        'is_complete': torrent.complete,
        'is_remake': torrent.remake
    }

def get_torrent_list_metadata(torrents, args) :

    return {
        'torrents': torrents,
        'args': args
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