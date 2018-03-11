"""
    This file keeps response structure in here
    so that, we can change it here and reflect it everywhere else \
        where same model is used
"""

def get_category_metadata(category, sub_categories=None) :

    if not category:
        return None

    category_metadata = {
        # 'id': category.id,
        'name': category.name,
        'id_as_string': category.id_as_string,
    }

    if sub_categories:
        category_metadata['sub_categories']= sub_categories

    return category_metadata

def get_torrent_metadata(torrent, submitter=None, category_as_model=False) :

    if not torrent:
        return None

    torrent_metadata = {
        'id': torrent.id,
        'name': torrent.display_name,

        'created_at': torrent.created_time,
        'hash_b32': torrent.info_hash_as_b32,  # as used in magnet uri
        'hash_hex': torrent.info_hash_as_hex,  # .hex(), #as shown in torrent client

        'url': '',  # TODO download url, later
        'magnet': torrent.magnet_uri,

        'information': torrent.information,
        'description': torrent.description,
        'filesize': torrent.filesize,

        'is_trusted': torrent.trusted,
        'is_complete': torrent.complete,
        'is_remake': torrent.remake
    }

    if submitter:
        torrent_metadata['submitter'] = {
            'id': submitter.id,
            'name': submitter.name
        }

    if category_as_model:
        torrent_metadata['main_category'] = get_category_metadata(
            torrent.main_category, [get_category_metadata(torrent.sub_category)]
        )
    else:
        torrent_metadata['main_category'] = torrent.main_category.name
        torrent_metadata['main_category_id'] = torrent.main_category.id
        torrent_metadata['sub_category'] = torrent.sub_category.name
        torrent_metadata['sub_category_id'] = torrent.sub_category.id

    if torrent.stats:
        torrent_metadata['stats'] = {
            'seeders': torrent.stats.seed_count,
            'leechers': torrent.stats.leech_count,
            'downloads': torrent.stats.download_count
        }

    return torrent_metadata

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