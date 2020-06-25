from apiclient.discovery import build

class GoogleClient():
    def __init__(self, config, credentials):
        self.config = config
        self.credentials = credentials
        self.youtube = build('youtube', 'v3', developerKey=credentials[0])

    def get_video_from_channel(self, channel_id, query):
        request = self.youtube.search().list(q=query, channelId=channel_id, part='snippet', type='video', maxResults=1)
        return request.execute()
