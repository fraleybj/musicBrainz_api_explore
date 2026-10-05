from musicbrainz_functions import *
from pathlib import Path

if __name__ == "__main__":
    sleeps_duration = 3
    
    # prepare an object for the top n artists
    n = 100
    dummy_row = {"user_count":-1}
    top_n = []
    for i in range(n):
        top_n.insert(0,dummy_row)

    # prepare an object for the checked artists (some artists show up multiple times)
    checked_artists = []
    aid = None
    aid = '10adc6b5-63bf-4b4e-993e-ed83b05c22fc'
    #aid = input('Please input the aid: ')
    #Cincinnati, OH b2cf490f-a8a7-4875-a1b7-addede3b327f
    #Portland, OR 2b748d6e-bc1c-4434-9f7b-ecd6332bc557
    #Palm Springs, CA 25b3e1fd-e929-45a5-ba70-8f270a5fad42
    listen_range = 'year'

    output_folder = Path("Seattle_2026_10_05")
    output_folder.mkdir(exist_ok=True)

    mbSession = build_session()
    mbSession.headers.update(header_MB)
    lbSession = build_session()
    lbSession.headers.update(header_LB)
    
    offset_counter = 0
    if offset_counter > 0:
        if os.path.exists('{0}/top_artists_by_tag_offset_{1}.data'.format(output_folder,offset_counter - 25)):
            with open('{0}/top_artists_by_tag_offset_{1}.data'.format(output_folder,offset_counter - 25), 'rb') as fp:
                top_n = pickle.load(fp)
            fp.close()
        else:
            raise Exception("File top_artists_by_tag_offset_{0}.data not found".format(offset_counter - 25))
    while offset_counter < 750:
        print("Processed {0} artists. Fetching more.".format(offset_counter))
        response = get_artists_by_tag(tags=("queer","lgbt","gay"),offset=offset_counter,session=mbSession)
        time.sleep(sleeps_duration)
        with open('{0}/artists_by_tag_offset_{1}.json'.format(output_folder,offset_counter), 'w') as fp:
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
            #if aid is set then skip an artist if they aren't in the area
            if aid is not None:
                aid_match = False
                if "begin-area" in artist:
                    if artist["begin-area"]["id"] == aid:
                        aid_match = True
                if "area" in artist:
                    if artist["area"]["id"] == aid:
                        aid_match = True
                if "end-area" in artist:
                    if artist["end-area"]["id"] == aid:
                        aid_match = True
                if not aid_match: continue
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
        with open('{0}/top_artists_by_tag_offset_{1}.data'.format(output_folder,offset_counter), 'wb') as fp:
            pickle.dump(top_n, fp)
        fp.close()
        with open('{0}/top_artists_by_tag_offset_{1}.json'.format(output_folder,offset_counter), 'w') as fp:
            json.dump(top_n, fp, indent = 4)
        fp.close()
        offset_counter = offset_counter + 25
    

    
    
    
