from musicbrainz_functions import *

#### TO DO: detect release group seen previously


if __name__ == "__main__":
    # prepare an object for the top n release groups
    n = 100
    dummy_row = {"user_count":-1}
    top_n = []
    for i in range(n):
        top_n.insert(0,dummy_row)

    # prepare an object for the top listeners
    #top_listeners = {}

    # prepare objects for the checked artists and checked releases (some entities show up multiple times)
    checked_artists = []
    checked_releases = []
    listen_range = 'this_year'
    fresh_threshold = '2025-06-01'
    offset_counter = 0
    if offset_counter > 0:
        if os.path.exists('top_hot_and_new_offset_{0}.data'.format(offset_counter - 25)):
            with open('top_hot_and_new_offset_{0}.data'.format(offset_counter - 25), 'rb') as fp:
                top_n = pickle.load(fp)
            fp.close()
        else:
            raise Exception("File hot_and_new_offset_{0}.data not found".format(offset_counter - 25))
    while offset_counter < 1000:
        print("Processed {0} artists. Fetching more.".format(offset_counter))
        response = get_artists_by_tag(tags=("queer","lgbt","gay"),offset=offset_counter)
        with open('hot_and_new_offset_{0}.json'.format(offset_counter), 'w') as fp:
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
            # lookup artist releases
            checked_artists.insert(0,artist["id"])
            with open('checked_hot_and_new_offset_{0}.data'.format(offset_counter), 'wb') as fp:
                pickle.dump(checked_artists, fp)
            fp.close()
            release_group_offset_counter = 0
            while release_group_offset_counter < 1000:
                release_groups = get_release_groups_by_artist(arid = artist["id"],offset=release_group_offset_counter)
                time.sleep(2)
                if release_groups == 204:
                    print("For artist: {0}, No releases found".format(artist["name"]))
                    release_group_offset_counter = 9999
                    continue
                elif len(release_groups['release-groups']) == 0:
                    print("For artist: {0}, No more releases found".format(artist["name"]))
                    release_group_offset_counter = 9999
                    continue
                else:
                    print("For artist: {0}, {1} more releases found ({2} total)".format(artist["name"],
                                                                        len(release_groups['release-groups']),
                                                                        release_group_offset_counter + len(release_groups['release-groups'])))
                    if len(release_groups['release-groups']) == 25:
                        release_group_offset_counter = release_group_offset_counter + 25
                    else:
                        release_group_offset_counter = 9999
                for release_group in release_groups['release-groups']:
                    #check for release dups
                    if release_group["id"] in checked_releases:
                        print("Release: {0} encountered previously, skipping.".format(release_group["title"]))
                        continue
                    checked_releases.insert(0,release_group["id"])
                    with open('checked_releases_hot_and_new_offset_{0}.data'.format(offset_counter), 'wb') as fp:
                        pickle.dump(checked_releases, fp)
                    fp.close()
                    if 'first-release-date' not in release_group:
                        first_release_date = '1900-01-01'
                    else:
                        first_release_date = release_group["first-release-date"]
                    if first_release_date < fresh_threshold:
                        #print("Release: {0} by {1} is older than threshold {2}, skipping".format(release_group["title"],
                        #                                                                         artist["name"],
                        #                                                                         fresh_threshold))
                        continue
                    # lookup release group listens
                    listen_count = get_release_group_listen_count(mbid=release_group["id"],listen_range = listen_range)
                    time.sleep(2)
                    if listen_count == 204:
                        print("For release: {0} by {1}, No listen history".format(release_group["title"],artist["name"]))
                        continue
                    else:
                        print("For release: {0} by {1}, Total listens: {2}, Total listeners: {3}".format(release_group["title"],
                                                                                                         artist["name"],
                                                                                                         listen_count["total_listen_count"],
                                                                                                         listen_count["total_user_count"]))
                    # insert the new release group in the top n if it's higher than an existing entry
                    for i in range(len(top_n)):
                        if listen_count["total_user_count"] > top_n[i]["user_count"]:
                            listen_count_detail = {"arid": artist["id"],
                                                   "artist_name": artist["name"],
                                                   "disambiguation": disambiguation,
                                                   "release": release_group["title"],
                                                   "listen_count": listen_count["total_listen_count"],
                                                   "user_count": listen_count["total_user_count"]}
                            top_n.insert(i,listen_count_detail)
                            break
                    #pop the last if list went over n
                    if len(top_n) > n:
                        top_n.pop()
                # end release_group segment for loop
            # end release_group full for loop
        # end artist for loop
        with open('top_hot_and_new_offset_{0}.data'.format(offset_counter), 'wb') as fp:
            pickle.dump(top_n, fp)
        fp.close()
        with open('top_hot_and_new_offset_{0}.json'.format(offset_counter), 'w') as fp:
            json.dump(top_n, fp, indent = 4)
        fp.close()
        offset_counter = offset_counter + 25


    
    
    
