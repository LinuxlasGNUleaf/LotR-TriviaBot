import googlesearch

class GoogleSearchClient:
    def google_search(self, query, site):
        '''
        searches for a specific query
        '''
        query = '{} {}'.format('site:'+site if site else '', query).strip()
        return googlesearch.search(query, lang='en', num_results=1)
