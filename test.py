import os, sys

sys.path.append(os.path.abspath('./google'))

import google_search_client


client = google_search_client.GoogleSearchClient()
result = client.google_search(input(), 'lotr.fandom.com')

for i in result:
    print(i)