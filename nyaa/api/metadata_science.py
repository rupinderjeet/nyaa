from datetime import timezone

"""
    This file keeps response structure in here
    so that, we can change it here and reflect it everywhere else \
        where same model is used
        
    TODO: Maybe now I can split this in respective individual classes.
    For e.g. metadata code for comments should be in comments_api
"""

###############################################################
########  LIST OF API-ENDPOINTS                         #######
###############################################################

def get_api_metadata () :

    api_metadata = {
        "status" : "active",
        "base" : "/api/v3/",
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

###############################################################
########  LIST OF CATEGORIES                            #######
###############################################################

def get_category_metadata(category, sub_categories=None) :

    if not category:
        return None

    category_metadata = {
        'id': category.id,
        'name': category.name,
        'id_as_string': category.id_as_string,
    }

    if sub_categories:
        category_metadata['sub_categories']= sub_categories

    return category_metadata

###############################################################
########  GET COMMENT                                   #######
###############################################################

def get_comment_metadata(comment) :

    if not comment:
        return None

    comment_metadata = {
        'id': comment.id,
        'text': comment.text,
        'created_time': without_dot_zero(comment.created_utc_timestamp)
    }

    if comment.edited_time:
        comment_metadata['edited_time'] = without_dot_zero(comment.edited_utc_timestamp)

    comment_author = comment.user
    if comment_author:
        comment_metadata['author_id'] = comment_author.id
        comment_metadata['author_name'] = comment_author.username

    return comment_metadata

###############################################################
########  BROWSE TORRENTS: Used for                     #######
########     1. Single Torrent                          #######
########     2. Torrent List with Search Term (DB)      #######
########     3. Torrent List without Search Term (ES)   #######
###############################################################

def get_torrent_metadata (torrent, submitter=None, from_es=False) :

    """
        For consistency between es and db results

        And, the presence of each key in returned dict is based on its availability.

        `created_time` is a pain for me:
            db time format is: Fri, 02 Feb 2018 19:38:09 GMT
            es time format is: 2018-02-02T19:37:43

        TODO: must convert them to epoch(posix) like timestamp
        TODO: add download url
    """

    if not torrent:
        return None

    torrent_metadata = {}

    if from_es:

        # User searched for a term, and our es got triggered

        # this means `torrent` is already a dict
        # I pushed extra_information from ES to new position 'es_extra', but haven't included it
        # for consistency with non-es results.

        # es has abnormal timestamp, as does db(2018-02-02T19:37:43) convert to seconds since epoch
        # I think this might break at some time, TODO: heal this!
        # nice_datetime = datetime.strptime(torrent['created_time'], "%Y-%m-%dT%H:%M:%S")
        # supposed_timestamp = (nice_datetime - datetime(1970, 1, 1)).total_seconds()
        # torrent_metadata['created_time'] = 'hello' # str(supposed_timestamp).rstrip('.0')

        stats = {}

        if 'seed_count' in torrent:
            stats['seed_count'] = torrent.pop('seed_count')

        if 'leech_count' in torrent:
            stats['leech_count'] = torrent.pop('leech_count')

        if 'download_count' in torrent:
            stats['download_count'] = torrent.pop('download_count')

        torrent['stats'] = stats

        es_extra = {}

        if 'anonymous' in torrent:
            es_extra['anonymous'] = torrent.pop('anonymous')

        if 'hidden' in torrent:
            es_extra['hidden'] = torrent.pop('hidden')

        if 'deleted' in torrent:
            es_extra['deleted'] = torrent.pop('deleted')

        if 'comment_count' in torrent:
            es_extra['comment_count'] = torrent.pop('comment_count')

        if 'has_torrent' in torrent:
            es_extra['has_torrent'] = torrent.pop('has_torrent')

        if 'hello' in torrent:
            es_extra['hello'] = torrent.pop('hello')

        # torrent['es_extra'] = es_extra

        return torrent


    # User is not using a search term, most likely viewing some category or latest torrents
    # torrent is a model
    # this means: we will have `magnet_uti`, `information` and `description` keys additionally

    if hasattr(torrent, 'id'):
        torrent_metadata['id'] = torrent.id

    if hasattr(torrent, 'display_name'):
        torrent_metadata['display_name'] = torrent.display_name

    if hasattr(torrent, 'created_time'):

        # I think this might break at some time, TODO: heal this!
        timestamp = torrent.created_time.replace(tzinfo=timezone.utc).timestamp()
        torrent_metadata['created_time'] = str(timestamp).rstrip('.0')

    if hasattr(torrent, 'information'):
        torrent_metadata['information'] = torrent.information

    if hasattr(torrent, 'description'):
        torrent_metadata['description'] = torrent.description

    if hasattr(torrent, 'info_hash'):
        torrent_metadata['info_hash'] = torrent.info_hash_as_hex

    if hasattr(torrent, 'filesize'):
        torrent_metadata['filesize'] = torrent.filesize

    if hasattr(torrent, 'magnet_uri'):
        torrent_metadata['magnet_uri'] = torrent.magnet_uri

    if hasattr(torrent, 'trusted'):
        torrent_metadata['trusted'] = torrent.trusted

    if hasattr(torrent, 'complete'):
        torrent_metadata['complete'] = torrent.complete

    if hasattr(torrent, 'remake'):
        torrent_metadata['remake'] = torrent.remake

    # torrent stats
    stats = {}
    if hasattr(torrent, 'stats') and torrent.stats:

        if hasattr(torrent.stats, 'seed_count'):
            stats['seed_count'] = torrent.stats.seed_count

        if hasattr(torrent.stats, 'leech_count'):
            stats['leech_count'] = torrent.stats.leech_count

        if hasattr(torrent.stats, 'download_count'):
            stats['download_count'] = torrent.stats.download_count

        torrent_metadata['stats'] = stats

    # torrent : submitter
    if submitter:

        if hasattr(submitter, 'id'):
            torrent_metadata['uploader_id'] = submitter.id

        if hasattr(submitter, 'name'):
            torrent_metadata['uploader_name'] = submitter.name

    # torrent : main category
    if hasattr(torrent, 'main_category') and torrent.main_category:

        if hasattr(torrent.main_category, 'id'):
            torrent_metadata['main_category_id'] = torrent.main_category.id

        ''' available, but not required. Category list should be fetched only once. '''
        # if hasattr(torrent.main_category, 'name'):
        #     torrent_metadata['main_category_name'] = torrent.main_category.name

    # torrent : sub category
    if hasattr(torrent, 'sub_category') and torrent.sub_category:

        if hasattr(torrent.sub_category, 'id'):
            torrent_metadata['sub_category_id'] = torrent.sub_category.id

        ''' available, but not required. Category list should be fetched only once. '''
        # if hasattr(torrent.sub_category, 'name'):
        #     torrent_metadata['sub_category_name'] = torrent.sub_category.name

    return torrent_metadata

def get_es_torrent_list_metadata(es_json, args) :

    """
        FROM ELASTIC SEARCH
    """

    torrents = []

    if es_json and es_json['hits'] and es_json['hits']['hits']:

        for hit in es_json['hits']['hits']:

            hit_source = hit['_source']

            if hit_source:
                torrents.append(get_torrent_metadata(hit_source, None, True))

    return get_torrent_list_metadata(torrents, args)

def get_torrent_list_metadata(torrents, args) :

    """ return torrents and its args """

    return {
        'torrents': torrents,
        'args': args
    }

# remove trailing .0
def without_dot_zero(target):
    return str(target).rstrip('.0')

