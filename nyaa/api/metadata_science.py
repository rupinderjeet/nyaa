"""
    This file keeps response structure in here
    so that, we can change it here and reflect it everywhere else \
        where same model is used
"""
from nyaa import models

def get_api_metadata () :

    api_metadata = {
        "status" : "active",
        "end_points" : [
            "categories/",
            "browse/",
            "info/<id>",
            "info/<id>/comments",
            "info/<id>/comments/<page>",
            "info/<id>/comments/add",
            "info/<id>/files"
        ]
    }

    return api_metadata

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
        # 'hash_b32': torrent.info_hash_as_b32,  # as used in magnet uri
        # 'hash_hex': torrent.info_hash_as_hex,  # .hex(), #as shown in torrent client

        # 'url': '',  # TODO download url, later
    }

    if hasattr(torrent, 'id'):
        torrent_metadata['id'] = torrent.id

    if hasattr(torrent, 'display_name'):
        torrent_metadata['name'] = torrent.display_name

    if hasattr(torrent, 'created_time'):
        torrent_metadata['created_time'] = torrent.created_time

    if hasattr(torrent, 'information'):
        torrent_metadata['information'] = torrent.information

    if hasattr(torrent, 'description'):
        torrent_metadata['description'] = torrent.description

    if hasattr(torrent, 'filesize'):
        torrent_metadata['filesize'] = torrent.filesize

    # if hasattr(torrent, 'info_hash'):
    #     torrent_metadata['info_hash'] = torrent.info_hash

    if hasattr(torrent, 'magnet_uri'):
        torrent_metadata['magnet'] = torrent.magnet_uri

    if hasattr(torrent, 'trusted'):
        torrent_metadata['is_trusted'] = torrent.trusted

    if hasattr(torrent, 'complete'):
        torrent_metadata['is_complete'] = torrent.complete

    if hasattr(torrent, 'remake'):
        torrent_metadata['is_remake'] = torrent.remake

    if submitter:
        torrent_metadata['submitter'] = {
            'id': submitter.id,
            'name': submitter.name
        }

    # if category_as_model:
    #     torrent_metadata['main_category'] = get_category_metadata(
    #         torrent.main_category, [get_category_metadata(torrent.sub_category)]
    #     )
    # else:
    #     torrent_metadata['main_category'] = torrent.main_category.name
    #     torrent_metadata['main_category_id'] = torrent.main_category.id
    #     torrent_metadata['sub_category'] = torrent.sub_category.name
    #     torrent_metadata['sub_category_id'] = torrent.sub_category.id

    if hasattr(torrent, 'stats') and torrent.stats:
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

def get_es_torrent_list_metadata(es_json, args) :

    torrents = []

    if es_json and es_json['hits'] and es_json['hits']['hits']:

        for hit in es_json['hits']['hits']:

            hit_source = hit['_source']

            if hit_source:

                torrents.append(hit["_source"])

                # no magnet
                # no information
                # no description

                torrent = models.Torrent
                torrent.id = hit_source['id']
                torrent.display_name = hit_source['display_name']
                torrent.created_time = hit_source['created_time']
                torrent.info_hash = hit_source['info_hash']

                torrent.filesize = hit_source['filesize']
                torrent.stats.seed_count = hit_source['seed_count']
                torrent.stats.leech_count = hit_source['leech_count']
                torrent.stats.download_count = hit_source['download_count']
                torrent.stats.downloads = hit_source['download_count']

                torrent.trusted = hit_source['trusted']
                torrent.complete = hit_source['complete']
                torrent.remake = hit_source['remake']

                torrents.append({})
                # torrents.append(get_torrent_metadata(torrent))

    return {
        'torrents': torrents,
        'args': args
    }

def get_comment_metadata(comment, comment_author) :

    if not comment:
        return None

    comment_metadata = {
        'id': comment.id,
        'text': comment.text,
        'created_at': comment.created_time
    }

    if comment.edited_time:
        comment_metadata['edited_at'] = comment.edited_time

    if comment_author:
        comment_metadata['author'] = {
            'id': comment_author.id,
            'name': comment_author.username
        }

    return comment_metadata