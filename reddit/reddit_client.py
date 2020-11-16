import praw

class RedditClient():
    '''
    Reddit Client for fetching memes.
    '''
    def __init__(self, info, meme_log):
        self.meme_log = meme_log
        client_id, client_secret, username, password = info
        self.reddit = praw.Reddit(client_id=client_id,
                                  client_secret=client_secret,
                                  password=password,
                                  user_agent='reddit post yoinker by /u/_LegolasGreenleaf',
                                  username=username)

    def get_meme(self, ch_id, subreddit):
        '''
        finds unseen meme for the given server
        '''
        if ch_id in self.meme_log.keys():
            used_ids = self.meme_log[ch_id]
        else:
            used_ids = []

        meme = ''
        for submission in self.reddit.subreddit(subreddit).hot():
            if not submission.id in used_ids:
                meme = submission
                used_ids.append(submission.id)
                break

        self.meme_log[ch_id] = used_ids
        return meme

    def get_crosspost_parent(self, submission):
        if hasattr(submission, 'crosspost_parent'):
            return praw.models.Submission(self.reddit, submission.crosspost_parent.split('_')[1])
        else:
            return False
