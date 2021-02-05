import googlesearch

class GoogleSearchClient:
    def google_search(self, query, site):
        '''
        searches for a specific query
        '''
        return googlesearch.search(('{} {}'.format('site:'+site if site else '', query).strip()), 'co.in', 'en', stop=1, pause=1)
