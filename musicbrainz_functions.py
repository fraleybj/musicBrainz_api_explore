import requests
import time
import pprint
import json
import pickle
import os
import re
from datetime import datetime

# Set DEBUG to True to test local dev server.
# API keys for local dev server and the real server are different.
DEBUG = False
ROOT_LB = 'http://localhost:8100' if DEBUG else 'https://api.listenbrainz.org'
ROOT_MB = 'http://localhost:8100' if DEBUG else 'https://musicbrainz.org'

# The following token must be valid, but it doesn't have to be the token of the user you're
# trying to get the listen history of.
with open('my_token.txt', 'r') as fp:
    TOKEN = fp.read()
fp.close()
with open('my_user_agent_string.txt', 'r') as fp:
    user_agent_string = fp.read()
fp.close()
header_LB = {
    "Authorization": "Token {0}".format(TOKEN)
}
header_MB = {'User-Agent': "{0}".format(user_agent_string)}

def get_listens(username, min_ts=None, max_ts=None, count=None):
    """Gets the listen history of a given user.

    Args:
        username: User to get listen history of.
        min_ts: History before this timestamp will not be returned.
                DO NOT USE WITH max_ts.
        max_ts: History after this timestamp will not be returned.
                DO NOT USE WITH min_ts.
        count: How many listens to return. If not specified,
               uses a default from the server.

    Returns:
        A list of listen info dictionaries if there's an OK status.

    Raises:
        An HTTPError if there's a failure.
        A ValueError if the JSON in the response is invalid.
        An IndexError if the JSON is not structured as expected.
    """
    response = requests.get(
        url="{0}/1/user/{1}/listens".format(ROOT_LB, username),
        params={
            "min_ts": min_ts,
            "max_ts": max_ts,
            "count": count,
        },
        # Note that an authorization header isn't compulsary for requests to get listens
        # BUT requests with authorization headers are given relaxed rate limits by ListenBrainz
        headers=header_LB,
    )
    
    response.raise_for_status()

    return response.json()['payload']['listens']

def get_listening_activity(username, listen_range = "all_time"):
    """Get the listening activity for user username.
    The listening activity shows the number of listens
    the user has submitted over a period of time.

    Args:
        username: User to get listen history of.
        listen_range: time interval for which statistics
        should be returned, possible values are
        ALLOWED_STATISTICS_RANGE, defaults to all_time

    Returns:
        A list of listen info dictionaries if there's an OK status.

    Raises:
        An HTTPError if there's a failure.
        A ValueError if the JSON in the response is invalid.
        An IndexError if the JSON is not structured as expected.
    """
    response = requests.get(
        url="{0}/1/stats/user/{1}/listening-activity".format(ROOT_LB, username),
        params={
            "range": listen_range,
        },
        # Note that an authorization header isn't compulsary for requests to get listens
        # BUT requests with authorization headers are given relaxed rate limits by ListenBrainz
        headers=header_LB,
    )
    
    response.raise_for_status()

    return response.json()['payload']

def get_artists(username, listen_range = 'all_time', offset=None, include_payload = False):
    """Gets the artist stats of a given user.

    Args:
        username: User to get listen history of.
        offest: How many artists to skip.

    Returns:
        A list of artists if there's an OK status.

    Raises:
        An HTTPError if there's a failure.
        A ValueError if the JSON in the response is invalid.
        An IndexError if the JSON is not structured as expected.
    """
    response = requests.get(
        url="{0}/1/stats/user/{1}/artists".format(ROOT_LB, username),
        params={
            "range": listen_range,
            "offset": offset,
        },
        # Note that an authorization header isn't compulsary for requests to get artists
        # BUT requests with authorization headers are given relaxed rate limits by ListenBrainz
        headers=header_LB,
    )

    response.raise_for_status()

    if include_payload:
        return response.json()['payload']
    else:
        return response.json()['payload']['artists']

def get_area_artists(area = None, aid = None, offset=None):
    """Gets the artists from an area (either begin, area, or end).

    Args:
        Area: Area.
        offest: How many artists to skip.

    Returns:
        A list of artists if there's an OK status.

    Raises:
        An HTTPError if there's a failure.
        A ValueError if the JSON in the response is invalid.
        An IndexError if the JSON is not structured as expected.
    """
    if aid is not None:
        area_response = requests.get(
            url="{0}/ws/2/area".format(ROOT_MB),
            params={
                "fmt": "json",
                "query": "aid:{0}".format(aid)
            },
            headers=header_MB,
        )

        area_response.raise_for_status()

        area = area_response.json()["areas"][0]["name"]
        time.sleep(1)
        
    response = requests.get(
        url="{0}/ws/2/artist".format(ROOT_MB),
        params={
            "fmt": "json",
            "offset": offset,
            "query": 'area:"{0}" OR beginarea:"{0}" OR endarea:"{0}"'.format(area)
        },
        headers=header_MB,
    )
    
    response.raise_for_status()
    
    if response.status_code != 200:
        print("No artists found")
    response_filt = response.json()
    if aid is not None:
        #filtered = [x for x in response_filt["artists"] if (x['area']['id'] == aid or x['begin-area']['id'] == aid or x['end-area']['id'] == aid)]
        for x in response_filt["artists"]:
            if x.get('area') is None:
                x.update({'area': {'id': 'None'}})
            if x.get('begin-area') is None:
                x.update({'begin-area': {'id': 'None'}})
            if x.get('end-area') is None:
                x.update({'end-area': {'id': 'None'}})
        filtered = [x for x in response_filt["artists"] if (x['area']['id'] == aid or x['begin-area']['id'] == aid or x['end-area']['id'] == aid)]
        response_filt["artists"] = filtered
    
    return response_filt

def get_artist_listen_count(mbid, listen_range = 'all_time'):
    """Gets the top listeners for an artist and overall listen count.

    Args:
        mbid: artist music brains id.
        listen_range: ['this_week', 'this_month', 'this_year', 'week', 'month', 'quarter', 'year', 'half_yearly', 'all_time']
        
    Returns:
        A list of top listeners for an artist and overall listen count if there's an OK status.

    Raises:
        An HTTPError if there's a failure.
        A ValueError if the JSON in the response is invalid.
        An IndexError if the JSON is not structured as expected.
    """

    response = requests.get(
        url="{0}/1/stats/artist/{1}/listeners".format(ROOT_LB, mbid),
        params={
            "range": listen_range,
        },
        headers=header_LB,
    )

    response.raise_for_status()

    if response.status_code == 204:
        return response.status_code
    
    return response.json()['payload']

def get_artists_by_tag(tags, offset=None):
    """Gets the artists from a list of tags

    Args:
        tags: Area.
        offest: How many artists to skip.

    Returns:
        A list of artists if there's an OK status.

    Raises:
        An HTTPError if there's a failure.
        A ValueError if the JSON in the response is invalid.
        An IndexError if the JSON is not structured as expected.
    """
    
    tag_list = "*+*".join(tags)
    print('tag:(*{0}*)'.format(tag_list))

    # need to do a "prepared request" because requests.get swaps stuff to unicode characters
    # in a way that MusicBrainz doesn't understand
    s = requests.Session()

    req = requests.Request('GET',
        url="{0}/ws/2/artist".format(ROOT_MB),
        params={
            "fmt": "json",
            "offset": offset,
            "query": 'tag:(*{0}*)'.format(tag_list)
        },
        headers=header_MB,
    )
    prepped = req.prepare()

    # swap out the "tag" section for a fixed one. Note, the .* is a bit risky, if tag isn't at the end
    # it would remove another paramater
    prepped.url = re.sub("tag.*",'tag:(*{0}*)'.format(tag_list),prepped.url)
    
    response = s.send(prepped)
    response.raise_for_status()
    print(response.url)
    if response.status_code != 200:
        print("No artists found")
    #Todo: 

    response_filt = response.json()

    artists_new = []
    for artist in response_filt["artists"]:
        #filter out tags with 0 or lower score
        artist["tags"] = [x for x in artist["tags"] if x["count"] > 0]
        #keep the artist if it still has a matching tag
        for tag in artist["tags"]:
            if re.search("|".join(tags),tag["name"]):
                artists_new.append(artist)
                break
    response_filt["artists"] = artists_new
    
    return response_filt

def get_release_group_listen_count(mbid, listen_range = 'all_time'):
    """Gets the top listeners for a release group and overall listen count.

    Args:
        mbid: release group music brains id.
        listen_range: ['this_week', 'this_month', 'this_year', 'week', 'month', 'quarter', 'year', 'half_yearly', 'all_time']
        
    Returns:
        A list of top listeners for a release group and overall listen count if there's an OK status.

    Raises:
        An HTTPError if there's a failure.
        A ValueError if the JSON in the response is invalid.
        An IndexError if the JSON is not structured as expected.
    """

    response = requests.get(
        url="{0}/1/stats/release-group/{1}/listeners".format(ROOT_LB, mbid),
        params={
            "range": listen_range,
        },
        headers=header_LB,
    )

    response.raise_for_status()

    if response.status_code == 204:
        return response.status_code
    
    return response.json()['payload']

def get_fresh_releases(release_date = datetime.today().strftime('%Y-%m-%d')):
    """This endpoint fetches upcoming and recently released (fresh) releases

    Args:
        release_date – Fresh releases will be shown around this pivot date. Must be in YYYY-MM-DD format
        (i didn't implement) days – The number of days of fresh releases to show. Max 90 days.
        (i didn't implement) sort – The sort order of the results. Must be one of “release_date”, “artist_credit_name” or “release_name”. Default “release_date”.
        (i didn't implement) past – Whether to show releases in the past. Default True.
        (i didn't implement) future – Whether to show releases in the future. Default True.
        
    Returns:
        upcoming and recently released (fresh) releases

    Raises:
        An HTTPError if there's a failure.
        A ValueError if the JSON in the response is invalid.
        An IndexError if the JSON is not structured as expected.
    """

    response = requests.get(
        url="{0}/1/explore/fresh-releases".format(ROOT_LB),
        params={
            "release_date": release_date,
        },
        headers=header_LB,
    )

    response.raise_for_status()

    if response.status_code == 204:
        return response.status_code
    
    return response.json()['payload']

def get_release_groups_by_artist(arid, offset=None):
    """Gets the release groups from an artist

    Args:
        arid: artist mbid

    Returns:
        A list of release groups if there's an OK status.

    Raises:
        An HTTPError if there's a failure.
        A ValueError if the JSON in the response is invalid.
        An IndexError if the JSON is not structured as expected.
    """
    
    response = requests.get(
        url="{0}/ws/2/release-group".format(ROOT_MB),
        params={
            "fmt": "json",
            "offset": offset,
            "query": 'arid:{0}'.format(arid)
        },
        headers=header_MB,
    )

    return response.json()

def get_artist_info(arid,inc=["tags","aliases"]):
    """Gets the artist info

    Args:
        arid: artist mbid
        inc: a list of elements to include

    Returns:
        Artist info including tags

    Raises:
        An HTTPError if there's a failure.
        A ValueError if the JSON in the response is invalid.
        An IndexError if the JSON is not structured as expected.
    """
    
    response = requests.get(
        url="{0}/ws/2/artist/{1}".format(ROOT_MB,arid),
        params={
            "fmt": "json",
            "inc": "+".join(inc)
        },
        headers=header_MB,
    )

    return response.json()

def get_feed_listens_following(user_name = "PupSniff",max_ts = None, min_ts  = None, count = None):
    """Get feed’s listen events for followed users.

    """

    response = requests.get(
        url="{0}/1/user/{1}/feed/events/listens/following".format(ROOT_LB,user_name),
        params={
            "max_ts": max_ts,
            "min_ts": min_ts,
            "count": count
        },
        headers=header_LB,
    )

    response.raise_for_status()

    if response.status_code == 204:
        return response.status_code
    
    return response.json()['payload']
