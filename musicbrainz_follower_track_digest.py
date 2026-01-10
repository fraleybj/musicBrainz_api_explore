from musicbrainz_functions import *
from datetime import datetime
import pandas as pd
import random

if __name__ == "__main__":

    ratingsURL = "https://docs.google.com/spreadsheets/d/1kOjkZy6jsM_qQl8ZTbBuWX3cmJV5c-GqbfJFsqjj6yA/export?format=csv&gid=0"
    ratingsDF = pd.read_csv(ratingsURL)
    max_ts = None #1758416820 2025-09-20 18:07:00
    #max_ts = int(datetime.strptime("2025-09-28 16:02:24", "%Y-%m-%d %H:%M:%S").timestamp())
    length_target = 12
    sleeps_duration = 3
    digestDF = pd.DataFrame({"timestamp": [], "user": [], "track": [], "artist": [], "recording_mbid": []})

    aveRating = ratingsDF["Rating"].mean()

    mbSession = build_session()
    mbSession.headers.update(header_MB)
    lbSession = build_session()
    lbSession.headers.update(header_LB)
    while len(digestDF) < length_target:
        print("Fetching more listens")
        feed_listens = get_feed_listens_following(max_ts = max_ts,session=lbSession)
        time.sleep(sleeps_duration)
        for event in feed_listens["events"]:
            ratingsDF_tmp = ratingsDF[(ratingsDF["User"] == event["metadata"]["user_name"]) & (ratingsDF["Status"] == "Latest")]
            if len(ratingsDF_tmp) == 0:
                include_chance = 1
            else:
                include_chance = ratingsDF_tmp["Ave rating"] / 6 * 1 / (ratingsDF_tmp["Plays by user"]/aveRating+1)
                include_chance = include_chance.iloc[0]            
            if event["metadata"]["user_name"] in digestDF["user"].values:
                include_chance = include_chance * 0.05 ** (digestDF["user"] == event["metadata"]["user_name"]).sum()
            print("Final play chance: {0}".format(include_chance))
            rand_num = random.random()
            #if rand_num > target, try saving throw. if pass, check tags. if no match, ditch (by setting high rand_num)
            if rand_num >= include_chance:
                rand_num = random.random()
                if rand_num < include_chance:
                    print("Saving throw! Checking artist tags")
                    tags=("queer","lgbt","gay")
                    fresh_threshold = '2025-10-01'
                    tag_match = False
                    if event["metadata"]["track_metadata"]["mbid_mapping"] is not None:
                        for artist in event["metadata"]["track_metadata"]["mbid_mapping"]["artist_mbids"]:
                            artist_info = get_artist_info(arid = artist,session=mbSession)
                            time.sleep(sleeps_duration)
                            for tag in artist_info["tags"]:
                                #print("Checking tag {0}".format(tag["name"]))
                                if tag["count"] > 0 and any(search_tag in tag["name"].lower() for search_tag in tags):
                                    print("Artist matched tags! Track saved!")
                                    tag_match = True
                                    break
                            if tag_match:
                                break
                        if not tag_match:
                            print("No artist matched tags! Checking first release date")
                            rec_mbid = event["metadata"]["track_metadata"]["mbid_mapping"]["recording_mbid"]
                            rec_info = get_recording_info(mbid=rec_mbid,session=mbSession)
                            time.sleep(sleeps_duration)
                            if rec_info["first-release-date"] >= fresh_threshold:
                                print("Track is fresh! Checking popularity")
                                rec_pop = get_recording_popularity(mbid_list=[rec_mbid],session=lbSession)
                                time.sleep(sleeps_duration)
                                if rec_pop[0]["total_user_count"] is None:
                                    rec_pop[0]["total_user_count"] = 0
                                if rec_pop[0]["total_user_count"] > 25:
                                    print("Track is popular! Track saved!")
                                    tag_match = True
                    if not tag_match:
                        print("Saving throw failed.")
                        rand_num = 100
            if rand_num < include_chance:
                rec_mbid = ""
                if event["metadata"]["track_metadata"]["mbid_mapping"] is not None:
                    if event["metadata"]["track_metadata"]["mbid_mapping"]["recording_mbid"] is not None:
                        rec_mbid = event["metadata"]["track_metadata"]["mbid_mapping"]["recording_mbid"]
                        print("Checking if already rated")
                        user_rating = get_recording_info(mbid = rec_mbid,inc=["user-ratings"],session=mbSession)
                        time.sleep(sleeps_duration)
                        if user_rating["user-rating"]["value"] is not None:
                            print("Recording is already rated, skipping.")
                            break
                new_row = pd.DataFrame(
                    {"timestamp": [datetime.fromtimestamp(event["created"])],
                     "user": [event["metadata"]["user_name"]],
                     "track": [event["metadata"]["track_metadata"]["track_name"]],
                     "artist": [event["metadata"]["track_metadata"]["artist_name"]],
                     "recording_mbid": [rec_mbid]})
                if len(digestDF) == 0:
                    digestDF = new_row
                else:
                    digestDF = pd.concat([digestDF, new_row],ignore_index=True)
                print("Added row to digest. {0} listened to {1} by {2} at {3}".format(
                    event["metadata"]["user_name"],
                    event["metadata"]["track_metadata"]["track_name"],
                    event["metadata"]["track_metadata"]["artist_name"],
                    datetime.fromtimestamp(event["created"])
                ))
                print("Digest length at {0} of {1}".format(len(digestDF),length_target))
            max_ts = event["created"]
            if len(digestDF) >= length_target:
                print("Digest complete") 
                break
    print("Writing digest to csv.")
    title = "Follower_Track_Digest_" + datetime.now().strftime("%Y-%m-%d_%H%M%S")
    outpath = "C:/Users/Brian/Code Stuff/musicbrainz/"
    digestDF.to_csv(outpath + title + ".csv",index=False)
    print("Creating LB playlist.")
    playlist_result = create_playlist(title = title,recording_mbid_list = digestDF["recording_mbid"][digestDF["recording_mbid"] != ''])
    
