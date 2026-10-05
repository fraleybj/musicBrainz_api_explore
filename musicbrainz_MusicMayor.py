from musicbrainz_functions import *
from pathlib import Path
import math
import re

if __name__ == "__main__":
    sleeps_duration = 3

    # prepare an object for the top 10 of area list
    n = 100
    dummy_row = {"user_count":-1}
    top_n = []
    for i in range(n):
        top_n.insert(0,dummy_row)

    # prepare an object for the top listeners
    top_listeners = {}

    # prepare an object for the checked artists (some artists show up multiple times)
    checked_artists = []    
    #aid = input('Please input the aid: ')
    aid = '10adc6b5-63bf-4b4e-993e-ed83b05c22fc'
    #Cincinnati, OH b2cf490f-a8a7-4875-a1b7-addede3b327f
    #Portland, OR 2b748d6e-bc1c-4434-9f7b-ecd6332bc557
    #Palm Springs, CA 25b3e1fd-e929-45a5-ba70-8f270a5fad42
    #Seattle, WA 10adc6b5-63bf-4b4e-993e-ed83b05c22fc

    output_folder = Path("Seattle_2026_10_05b")
    output_folder.mkdir(exist_ok=True)
    
    listen_range = 'this_year'
    #TO DO: have stuff be actually this year and not the "this year and last year" that ListenBrainz returns, grrrr

    tags = None
    tags=("queer","lgbt","gay")

    mbSession = build_session()
    mbSession.headers.update(header_MB)
    lbSession = build_session()
    lbSession.headers.update(header_LB)
    
    offset_counter = 0
    if offset_counter > 0:
        if os.path.exists('{0}/top_artists_offset_{1}.data'.format(output_folder,offset_counter - 25)):
            with open('{0}/top_artists_offset_{1}.data'.format(output_folder,offset_counter - 25), 'rb') as fp:
                top_n = pickle.load(fp)
            fp.close()
        else:
            raise Exception("File {0}/top_artists_offset_{1}.data not found".format(output_folder,offset_counter - 25))
        if os.path.exists('{0}/top_listeners_offset_{1}.json'.format(output_folder,offset_counter - 25)):
            with open('{0}/top_listeners_offset_{1}.json'.format(output_folder,offset_counter - 25), 'r') as fp:
                data = fp.read()
            fp.close()
            top_listeners = json.loads(data)
        else:
            raise Exception("File {0}/top_listeners_offset_{1}.json not found".format(output_folder,offset_counter - 25))
        if os.path.exists('{0}/checked_artists_offset_{1}.data'.format(output_folder,offset_counter - 25)):
            with open('{0}/checked_artists_offset_{1}.data'.format(output_folder,offset_counter - 25), 'rb') as fp:
                checked_artists = pickle.load(fp)
            fp.close()
        else:
            raise Exception("File {0}/checked_artists_offset_{1}.data not found".format(output_folder,offset_counter - 25))
    while offset_counter < 6000:
        print("Processed {0} artists. Fetching more.".format(offset_counter))
        if tags is None:
            response = get_area_artists(aid = aid,offset=offset_counter,session=mbSession)
        else:
            response = get_area_artists(aid = aid,offset=offset_counter,session=mbSession,inc="tags")
        time.sleep(sleeps_duration)
        with open('{0}/area_artists_offset_{1}.json'.format(output_folder,offset_counter), 'w') as fp:
            json.dump(response, fp, indent = 4)
        fp.close()
        print("Number found: {0}, offset: {1}".format(response["artist-count"],response["artist-offset"]))
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
            #tag match check
            if tags is not None:
                tag_match = False
                if "tags" in artist:
                    for tag in artist["tags"]:
                        if tag["count"] < 1: continue
                        if re.search("queer|gay|lgbt",tag["name"],flags=re.IGNORECASE):
                            tag_match = True
                if not tag_match: continue
            # lookup artist listens
            listen_count = get_artist_listen_count(mbid=artist["id"],listen_range = listen_range,session=lbSession)
            checked_artists.insert(0,artist["id"])
            with open('{0}/checked_artists_offset_{1}.data'.format(output_folder,offset_counter), 'wb') as fp:
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
            time.sleep(sleeps_duration)
            # insert the new artist in the top n if it's higher than an existing entry
            for i in range(len(top_n)):
                if listen_count["total_user_count"] > top_n[i]["user_count"]:
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
                    top_listeners[listener['user_name']]['in_top10_count'] += 1
                    top_listeners[listener['user_name']]['artist_list'].append(artist["id"])
                else:
                    top_listeners[listener['user_name']] = {"in_top10_count":1,"listens_in_period":0,"artist_list":[artist["id"]]}
                    
        with open('{0}/top_artists_offset_{1}.data'.format(output_folder,offset_counter), 'wb') as fp:
            pickle.dump(top_n, fp)
        fp.close()
        with open('{0}/top_artists_offset_{1}.json'.format(output_folder,offset_counter), 'w') as fp:
            json.dump(top_n, fp, indent = 4)
        fp.close()
        # Sort based on Values
        with open('{0}/top_listeners_offset_{1}.json'.format(output_folder,offset_counter), 'w') as fp:
            json.dump(top_listeners, fp, indent = 4)
        fp.close()
        offset_counter = offset_counter + 25
    # Sort based on in_top10_count
    top_listeners = dict(
        sorted(
            top_listeners.items(),
            key=lambda item: item[1]["in_top10_count"],
            reverse=True,
        )
    )

    #establish a score for top listeners giving up to 10 points for having a top_n band
    for username, user_listens in top_listeners.items():
        top_listeners[username]["score"] = top_listeners[username]["in_top10_count"]
        for artist in user_listens["artist_list"]:
            found_index = None
            # Loop with enumerate to track the sequence/index
            for index, d in enumerate(top_n):
                # .get() prevents errors if a dict is missing the key
                if d.get("mbid") == artist:
                    found_index = index
                    break
            # Check the result
            if found_index is None: continue
            top_listeners[username]["score"] = top_listeners[username]["score"] + (n-found_index)/10
    #look up total listens for users, drop score for high listens
    counter = 1
    for username, user_listens in top_listeners.items():
        if counter <= 50:
            user_activity = get_listening_activity(username, listen_range = listen_range, session=lbSession)
            print("Finding listen history for {0}. User {1} of {2}.".format(username,counter,len(top_listeners)))
            #to do: fix this to only get the elements actually in this period (not the previous period that ListenBrainz sends along)
            listens_in_period = sum(d["listen_count"] for d in user_activity["listening_activity"])
            top_listeners[username]["listens_in_period"] = listens_in_period
            top_listeners[username]["score"] = top_listeners[username]["score"] / (max(1,math.log(listens_in_period) - 8) ** 2)
            time.sleep(sleeps_duration)
        else:
            print("Skipping for {0}. User {1} of {2}.".format(username,counter,len(top_listeners)))
            top_listeners[username]["score"] = top_listeners[username]["score"] - 1000
        counter += 1
    # Sort based on score
    top_listeners = dict(
        sorted(
            top_listeners.items(),
            key=lambda item: item[1]["score"],
            reverse=True,
        )
    )
    with open('{0}/top_listeners.json'.format(output_folder), 'w') as fp:
        json.dump(top_listeners, fp, indent = 4)
    fp.close()
    with open('{0}/top_artists.json'.format(output_folder), 'w') as fp:
        json.dump(top_n, fp, indent = 4)
    fp.close()
