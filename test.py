import os
import sys

import lotr_config

sys.path.append(os.path.abspath('./discord'))
sys.path.append(os.path.abspath('./reddit'))
sys.path.append(os.path.abspath('./google'))

import dc_client
import reddit_client
import google_client

# aquire Google credentials from file
try:
    with open(lotr_config.GOOGLE_TOKEN, 'r') as tokenfile:
        google_credentials = tokenfile.readlines()
        for i, item in enumerate(google_credentials):
            google_credentials[i] = item.strip()
except (FileNotFoundError, EOFError):
    print('[ERROR]: google credentials not found! abort.')
    sys.exit(-1)

channel_id = 'UCYXpatz5Z4ek0M_5VR-Qt1A'
client = google_client.GoogleClient(lotr_config, google_credentials)
res = client.get_video_from_channel(channel_id, 'tennis', 1)['items'][0]
video_id = res['id']['videoId']
res2 = client.get_video_info(video_id)
print(res2)