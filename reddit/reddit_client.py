import aiohttp
import yaml
from datetime import datetime

class RedditClient():
    '''
    Reddit Client for fetching memes.
    '''
    def __init__(self, meme_log, config):
        self.meme_log = meme_log
        self.json = []
        self.default_limit = config['reddit']['query_limit']
        self.limit = self.default_limit
        self.timestamp_old = datetime.now()
        self.limit_inc = self.default_limit
        self.json_timeout = config['reddit']['json_timeout']
        self.sub_attributes = ['id','title','author','url','is_self','selftext']

    async def get_meme(self, ch_id, target_subs):
        '''
        finds unseen meme for the given server
        '''
        if ch_id not in self.meme_log.keys():
            self.meme_log[ch_id] = []

        difference = datetime.now() - self.timestamp_old

        if not self.json or difference.total_seconds()/60 > self.json_timeout:
            await self.refreshJSON(target_subs)
            self.limit = self.default_limit
            self.timestamp_old = datetime.now()

        while True:
            for i,submission in enumerate(self.json):
                if not submission['id'] in self.meme_log[ch_id]:
                    self.meme_log[ch_id].append(submission['id'])
                    return submission

            self.limit += self.limit_inc
            self.timestamp_old = datetime.now()
            await self.refreshJSON(target_subs)

    async def refreshJSON(self, target_subs):
        async with aiohttp.ClientSession() as session:
            async with session.get('https://www.reddit.com/r/{}/hot.json?limit={}'.format('+'.join(target_subs),self.limit)) as result:
                temp = await result.json()
                temp = temp['data']['children']
                self.json = []
                for i,submission in enumerate(temp):
                    filtered_submission = {k:v for k,v in submission['data'].items() if k in self.sub_attributes}
                    self.json.append(filtered_submission)
