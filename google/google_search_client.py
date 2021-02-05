from googlesearch import search

class GoogleSearchClient:
    def google_search(self, query, site):
        '''
        searches for a specific query
        '''
        return search('{} {}'.format('site:'+site if site else '', query).strip(),
                      tld='co.in', lang='en',
                      num=10, stop=1, pause=1)
