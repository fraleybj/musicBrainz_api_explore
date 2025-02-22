import requests
import time
import pprint
import json
import pickle
import os

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
AUTH_HEADER = {
    "Authorization": "Token {0}".format(TOKEN)
}


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
        headers=AUTH_HEADER,
    )
    
    response.raise_for_status()

    return response.json()['payload']['listens']

def get_artists(username, offset=None):
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
            "offset": offset,
        },
        # Note that an authorization header isn't compulsary for requests to get artists
        # BUT requests with authorization headers are given relaxed rate limits by ListenBrainz
        headers=AUTH_HEADER,
    )

    response.raise_for_status()

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
        )

        area_response.raise_for_status()

        area = area_response.json()["areas"][0]["name"]
        
    response = requests.get(
        url="{0}/ws/2/artist".format(ROOT_MB),
        params={
            "fmt": "json",
            "offset": offset,
            "query": 'area:"{0}" OR beginarea:"{0}" OR endarea:"{0}"'.format(area)
        },
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
        headers=AUTH_HEADER,
    )

    response.raise_for_status()

    if response.status_code == 204:
        return response.status_code
    
    return response.json()['payload']

if __name__ == "__main__":
    # prepare an object for the top 10 of area list
    n = 100
    dummy_row = {"listen_count":-1}
    top_n = []
    for i in range(n):
        top_n.insert(0,dummy_row)

    # prepare an object for the top listeners
    top_listeners = {}

    # prepare an object for the checked artists (some artists show up multiple times)
    checked_artists = []    
    #aid = input('Please input the aid: ')
    #Cincinnati, OH b2cf490f-a8a7-4875-a1b7-addede3b327f
    #Portland, OR 2b748d6e-bc1c-4434-9f7b-ecd6332bc557
    #Palm Springs, CA 25b3e1fd-e929-45a5-ba70-8f270a5fad42
    listen_range = 'year'
    
    offset_counter = 0
    if offset_counter > 0:
        if os.path.exists('top_artists_offset_{0}.data'.format(offset_counter - 25)):
            with open('top_artists_offset_{0}.data'.format(offset_counter - 25), 'rb') as fp:
                top_n = pickle.load(fp)
            fp.close()
        else:
            raise Exception("File top_artists_offset_{0}.data not found".format(offset_counter - 25))
        if os.path.exists('top_listeners_offset_{0}.json'.format(offset_counter - 25)):
            with open('top_listeners_offset_{0}.json'.format(offset_counter - 25), 'r') as fp:
                data = fp.read()
            fp.close()
            top_listeners = json.loads(data)
        else:
            raise Exception("File top_listeners_offset_{0}.json not found".format(offset_counter - 25))
        if os.path.exists('checked_artists_offset_{0}.data'.format(offset_counter - 25)):
            with open('checked_artists_offset_{0}.data'.format(offset_counter - 25), 'rb') as fp:
                checked_artists = pickle.load(fp)
            fp.close()
        else:
            raise Exception("File checked_artists_offset_{0}.data not found".format(offset_counter - 25))
    while offset_counter < 3250:
        print("Processed {0} artists. Fetching more.".format(offset_counter))
        response = get_area_artists(aid = '25b3e1fd-e929-45a5-ba70-8f270a5fad42',offset=offset_counter)
        with open('area_artists_offset_{0}.json'.format(offset_counter), 'w') as fp:
            json.dump(response, fp, indent = 4)
        fp.close()
        print("Number found: {0}, offset: {1}".format(response["count"],response["offset"]))
        if len(response["artists"]) == 0:
            print("No more artists. Writing final results.")
            break
        print("Processing {0} artists.".format(len(response["artists"])))
        # while there are unprocessed artists check if an artist should join the list
        for artist in response["artists"]:
            if 'disambiguation' not in artist:
                disambiguation = "None"
            else:
                disambiguation = artist["disambiguation"]
            if artist["id"] in checked_artists:
                print("Artist: {0} encountered previously, skipping.".format(artist["name"]))
                continue
            # lookup artist listens
            listen_count = get_artist_listen_count(mbid=artist["id"],listen_range = listen_range)
            checked_artists.insert(0,artist["id"])
            with open('checked_artists_offset_{0}.data'.format(offset_counter), 'wb') as fp:
                pickle.dump(checked_artists, fp)
            fp.close()
            if listen_count == 204:
                print("For artist: {0}, No listen history".format(artist["name"]))
                continue
                #an artist with no listens: 1eeb0d5a-fcb6-42b2-a93d-02396e206c70
            else:
                print("For artist: {0}, Total listens: {1}, Total listeners: {2}".format(listen_count["artist_name"],
                                                                                     listen_count["total_listen_count"],
                                                                                     listen_count["total_user_count"]))
            time.sleep(3)
            # isert the new artist in the top n if it's higher than an existing entry
            for i in range(len(top_n)):
                if listen_count["total_listen_count"] > top_n[i]["listen_count"]:
                    listen_count_detail = {"mbid": listen_count["artist_mbid"],
                                           "name": listen_count["artist_name"],
                                           "disambiguation": disambiguation,
                                           "listen_count": listen_count["total_listen_count"],
                                           "user_count": listen_count["total_user_count"]}
                    top_n.insert(i,listen_count_detail)
                    break
            #pop the last if list went over n
            if len(top_n) > n:
                top_n.pop()

            #update top listeners
            for listener in listen_count["listeners"]:
                if listener['user_name'] in top_listeners:
                    top_listeners[listener['user_name']] = top_listeners[listener['user_name']] + 1
                else:
                    top_listeners[listener['user_name']] = 1
                    
        with open('top_artists_offset_{0}.data'.format(offset_counter), 'wb') as fp:
            pickle.dump(top_n, fp)
        fp.close()
        with open('top_artists_offset_{0}.json'.format(offset_counter), 'w') as fp:
            json.dump(top_n, fp, indent = 4)
        fp.close()
        # Sort based on Values
        top_listeners = {k: v for k, v in sorted(top_listeners.items(), key=lambda item: item[1],reverse=True)}
        with open('top_listeners_offset_{0}.json'.format(offset_counter), 'w') as fp:
            json.dump(top_listeners, fp, indent = 4)
        fp.close()
        offset_counter = offset_counter + 25
    # Sort based on Values
    top_listeners = {k: v for k, v in sorted(top_listeners.items(), key=lambda item: item[1],reverse=True)}
    with open('top_listeners.json', 'w') as fp:
        json.dump(top_listeners, fp, indent = 4)
    fp.close()
    with open('top_artists.json', 'w') as fp:
        json.dump(top_n, fp, indent = 4)
    fp.close()

    
    
    
