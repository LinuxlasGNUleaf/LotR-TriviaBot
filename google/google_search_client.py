import googlesearch

class GoogleSearchClient:
    def google_search(self, query, site):
        '''
        searches for a specific query
        '''
        query = '{} {}'.format('site:'+site if site else '', query).strip()
        print(query)
        return googlesearch.search(query, tld='co.in', lang='en', stop=1, pause=1)
