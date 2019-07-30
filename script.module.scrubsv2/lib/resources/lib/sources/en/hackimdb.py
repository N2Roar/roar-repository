# -*- coding: UTF-8 -*-
# -Cleaned and Checked on 07-19-2018 by JewBMX in Scrubs.

from resources.lib.modules import getSum
from resources.lib.modules import source_utils


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['en']
        self.domains = ['hackimdb.com', '123movieswww.com']
        self.base_link = 'https://123movieswww.com'
        self.search_link = '/title/%s'


    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            url = self.base_link + self.search_link % imdb
            return url
        except:
            return


    def sources(self, url, hostDict, hostprDict):
        try:
            sources = []
            if url == None:
                return sources
            hostDict = hostprDict + hostDict
            r = getSum.get(url, Type='cfscrape')
            match = getSum.findSum(r)
            for url in match:
                if not 'youtube' in url:
                    url = url.replace('xstreamcdn.com', 'fembed.com').replace('gcloud.live', 'fembed.com').replace('femoload.xyz', 'fembed.com').replace('there.to', 'fembed.com') if '/v/' in url else url
                    quality, info = source_utils.get_release_quality(url, url)
                    valid, host = source_utils.is_host_valid(url, hostDict)
                    if valid:
                        sources.append({'source': host, 'quality': quality, 'language': 'en', 'url': url, 'info': info, 'direct': False, 'debridonly': False})
            return sources
        except:
            return sources


    def resolve(self, url):
        return url


