from musicbrainz_functions import *

if __name__ == "__main__":
    listen_range = "this_year"
    
    my_artists = get_artists(username = 'PupSniff', offset=None, listen_range = listen_range)
    bands_im_top = []
    with open('my_top_bands.json', 'w') as fp:
        json.dump(my_artists, fp, indent = 4)
    fp.close()
    offset_counter = 0
    while offset_counter < 100:
        my_artists = get_artists(username = 'PupSniff', offset=offset_counter, listen_range = listen_range)
        for artist in my_artists:
            if artist["artist_mbid"] == None:
                print("Artist: {0} doesn't have an mbid! Skipping.".format(artist["artist_name"]))
                continue
            # lookup artist listens
            listen_count = get_artist_listen_count(mbid=artist["artist_mbid"],listen_range = listen_range)
            #checked_artists.insert(0,artist["id"])
            #with open('checked_artists_offset_{0}.data'.format(offset_counter), 'wb') as fp:
            #    pickle.dump(checked_artists, fp)
            #fp.close()
            if listen_count == 204:
                print("For artist: {0}, No listen history".format(artist["artist_name"]))
                continue
                #an artist with no listens: 1eeb0d5a-fcb6-42b2-a93d-02396e206c70
            else:
                print("For artist: {0}, Total listens: {1}, Total listeners: {2}".format(listen_count["artist_name"],
                                                                                     listen_count["total_listen_count"],
                                                                                     listen_count["total_user_count"]))
                i = 1
                sniff_found_flag = False
                for listener in listen_count["listeners"]:
                    if listener['user_name'] == 'PupSniff':
                        sniff_found_flag = True
                        bands_im_top_row = {"artist":artist["artist_name"],
                                            "my_rank":i,"my_listen_count":listener["listen_count"]}
                        bands_im_top.append(bands_im_top_row)
                        print("Sniff is Rank {0} for {1} with {2} listens!".format(i,
                                                                                   artist["artist_name"],
                                                                                   listener["listen_count"]))
                    i = i+1
                if not sniff_found_flag:
                    print("Sniff is not ranked. User {0} has {1} listens compared to Sniff's {2}.".format(listener['user_name'],
                                                                                   listener["listen_count"],
                                                                                   artist["listen_count"]))
            time.sleep(3)
        offset_counter = offset_counter + 25
    with open('bands_im_top.json', 'w') as fp:
        json.dump(bands_im_top, fp, indent = 4)
    fp.close()
            
