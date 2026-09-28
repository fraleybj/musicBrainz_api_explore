from musicbrainz_functions import *
from datetime import datetime
import pandas as pd

if __name__ == "__main__":

    ratingsURL = "https://docs.google.com/spreadsheets/d/1kOjkZy6jsM_qQl8ZTbBuWX3cmJV5c-GqbfJFsqjj6yA/export?format=csv&gid=0"
    ratingsDF = pd.read_csv(ratingsURL)
    ratingsDF_latest = ratingsDF[ratingsDF["Status"] == "Latest"]
    ratingsDF_latest = ratingsDF_latest.sort_values(by = "Ave rating",ascending=False).reset_index(drop=True)

    print(ratingsDF_latest.iloc[0])
    print(ratingsDF_latest.iloc[1])

    length_target = 12
    sleeps_duration = 3
    
    mbSession = build_session()
    mbSession.headers.update(header_MB)
    lbSession = build_session()
    lbSession.headers.update(header_LB)
    
    #username = 'TRDuchess'
    #username = 'PupSniff'
    listen_range = 'month'
    offset = 0
    session = lbSession
    
    s = session or requests.Session()

    digestDF = pd.DataFrame({"timestamp": [], "user": [], "track": [], "artist": [], "recording_mbid": []})
    
    """
    response = s.get(
        url="{0}/1/stats/user/{1}/recordings".format(ROOT_LB, username),
        params={
            "range": listen_range,
            "offset": offset,
        },
        headers=header_LB,
    )
    
    result = response.json()['payload']['recordings']
    print(result[0])
    """

    #for username in ratingsDF_latest["User"]:
    #    print("Fetching top tracks from {0}".format(username))
    
    #username = ratingsDF_latest.iloc[0]["User"]
    while len(digestDF) < length_target:
        for username in ratingsDF_latest["User"]:
            print("Fetching top tracks from {0}".format(username))
                  
            result = get_user_stats(username = username, offset = offset,
                                    listen_range=listen_range, endpoint = 'recordings',
                                    session = s)
            time.sleep(sleeps_duration)
            if len(result) == 0:
                print("No listens in period for {0}, moving on.".format(username))
                continue
            top_result = result[0]
            rec_mbid = ""
            if top_result["recording_mbid"] is not None:
                rec_mbid = top_result["recording_mbid"]
                if any(rec_mbid == digestDF["recording_mbid"]):
                    print("Recording is already in this digest, skipping.")
                    continue
                print("Checking if already rated")
                user_rating = get_recording_info(mbid = rec_mbid,inc=["user-ratings"],session=mbSession)
                time.sleep(sleeps_duration)
                try:
                    if user_rating["user-rating"]["value"] is not None:
                        print("Recording is already rated, skipping.")
                        continue
                except:
                    print("Something went wrong, skipping.")
                    continue
            new_row = pd.DataFrame(
                {"timestamp": [datetime.now()],
                 "user": [username],
                 "track": [top_result["track_name"]],
                 "artist": [top_result["artist_name"]],
                 "recording_mbid": [rec_mbid]})
            if len(digestDF) == 0:
                digestDF = new_row
            else:
                digestDF = pd.concat([digestDF, new_row],ignore_index=True)
            print("Added row to digest. {0} listened to {1} by {2} {3} time(s).".format(
                username,
                top_result["track_name"],
                top_result["artist_name"],
                top_result["listen_count"]
            ))
            print("Digest length at {0} of {1}".format(len(digestDF),length_target))
            if len(digestDF) >= length_target:
                print("Digest complete") 
                break
    print("Writing digest to csv.")
    title = "Follower_Top_Tracks_" + datetime.now().strftime("%Y-%m-%d_%H%M%S")
    outpath = "C:/Users/Brian/Code Stuff/musicbrainz/"
    digestDF.to_csv(outpath + title + ".csv",index=False)
    print("Creating LB playlist.")
    playlist_result = create_playlist(title = title,recording_mbid_list = digestDF["recording_mbid"][digestDF["recording_mbid"] != ''])
