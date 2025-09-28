from musicbrainz_functions import *

if __name__ == "__main__":
    listen_range = "this_year"
    
    ##my_artists = get_artists(username = 'PupSniff', offset=None, listen_range = listen_range)
    offset_counter = 0
    while offset_counter < 100:
        my_artists = get_artists(username = 'PupSniff', offset=offset_counter, listen_range = listen_range)
        for artist in my_artists:
            if artist["artist_mbid"] == None:
                print("Artist: {0} doesn't have an mbid! Skipping.".format(artist["artist_name"]))
                continue
            # lookup artist tags
            artist_info = get_artist_info(arid=artist["artist_mbid"],inc=["tags"])
            if len(artist_info["tags"]) == 0:
                print("You have listened to {0} {1} times {2} and they have no tags.".format(artist["artist_name"],artist["listen_count"],listen_range))
            else:
                print("Artist {0} has tags! Moving on.".format(artist["artist_name"]))
            time.sleep(2)
        offset_counter = offset_counter + 25
