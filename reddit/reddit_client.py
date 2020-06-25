import praw

class RedditClient():
    """
    Reddit Client for fetching memes.
    """
    def __init__(self, config, info, meme_log):
        self.config = config
        self.meme_log = meme_log
        client_id, client_secret, username, password = info
        self.reddit = praw.Reddit(client_id=client_id,
                                  client_secret=client_secret,
                                  password=password,
                                  user_agent="reddit post yoinker by /u/_LegolasGreenleaf",
                                  username=username)

    def get_meme(self, server, subreddit):
        """
        finds unseen meme for the given server
        """
        if server in self.meme_log.keys():
            used_ids = self.meme_log[server]
        else:
            used_ids = []

        meme = ""
        for submission in self.reddit.subreddit(subreddit).hot():
            if submission.id in used_ids:
                continue
            else:
                meme = submission
                used_ids.append(submission.id)
                break

        self.meme_log[server.id] = used_ids
        return meme
