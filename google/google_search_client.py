from googlesearch import search

class GoogleSearchClient:
    def google_search(self, query, site):
        '''
        searches for a specific query
        '''
        return search('{} {}'.format('site:'+site if site else '', query).strip(), 'co.in', 'en', stop=1, pause=1)
