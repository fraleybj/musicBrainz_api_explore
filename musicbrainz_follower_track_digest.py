from musicbrainz_functions import *
from datetime import datetime
import pandas as pd
import random

if __name__ == "__main__":

    ratingsDF = pd.read_csv("C:/Users/frale/Downloads/Listenbrainz follow ratings - Data.csv")
    max_ts = None #1758416820 2025-09-20 18:07:00
    #max_ts = int(datetime.strptime("2025-09-28 16:02:24", "%Y-%m-%d %H:%M:%S").timestamp())
    length_target = 12
    digestDF = pd.DataFrame({"timestamp": [], "user": [], "track": [], "artist": []})
    
    while len(digestDF) < length_target:
        feed_listens = get_feed_listens_following(max_ts = max_ts)
        for event in feed_listens["events"]:
            ratingsDF_tmp = ratingsDF[(ratingsDF["User"] == event["metadata"]["user_name"]) & (ratingsDF["Status"] == "Latest")]
            if len(ratingsDF_tmp) == 0:
                include_chance = 1
            else:
                include_chance = ratingsDF_tmp["Ave rating"] / 6 * 1 / (ratingsDF_tmp["Plays by user"]+1)
                include_chance = include_chance.iloc[0]            
            if event["metadata"]["user_name"] in digestDF["user"].values:
                include_chance = include_chance * 0.1 ** (digestDF["user"] == event["metadata"]["user_name"]).sum()
            print("Final play chance: {0}".format(include_chance))
            rand_num = random.random()
            #if rand_num > target, try saving throw. if pass, check tags. if no match, ditch (by setting high rand_num)
            if rand_num >= include_chance:
                rand_num = random.random()
                if rand_num < include_chance:
                    print("Saving throw! Checking artist tags")
                    tags=("queer","lgbt","gay")
                    tag_match = False
                    if event["metadata"]["track_metadata"]["mbid_mapping"] is not None:
                        for artist in event["metadata"]["track_metadata"]["mbid_mapping"]["artist_mbids"]:
                            artist_info = get_artist_info(arid = artist)
                            for tag in artist_info["tags"]:
                                #print("Checking tag {0}".format(tag["name"]))
                                if tag["count"] > 0 and any(search_tag in tag["name"].lower() for search_tag in tags):
                                    print("Artist matched tags! Track saved!")
                                    tag_match = True
                                    break
                            if tag_match:
                                break
                    if not tag_match:
                        rand_num = 100
                        print("No artist matched tags! Saving throw failed!")
            if rand_num < include_chance:
                new_row = pd.DataFrame(
                    {"timestamp": [datetime.fromtimestamp(event["created"])],
                     "user": [event["metadata"]["user_name"]],
                     "track": [event["metadata"]["track_metadata"]["track_name"]],
                     "artist": [event["metadata"]["track_metadata"]["artist_name"]]})
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
        time.sleep(2)
    print("Writing digest to csv.")
    digestDF.to_csv("C:/Users/Brian/Code Stuff/musicbrainz/follower_track_digest.csv",index=False)
    
