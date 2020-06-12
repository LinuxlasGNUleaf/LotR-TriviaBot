import praw

class RedditClient():
    def __init__(self, config, info):
        self.config = config
        client_id, client_secret, username, password = info
        self.reddit = praw.Reddit(client_id=client_id,
                                  client_secret=client_secret,
                                  password=password,
                                  user_agent="reddit post yoinker by /u/_LegolasGreenleaf",
                                  username=username)
