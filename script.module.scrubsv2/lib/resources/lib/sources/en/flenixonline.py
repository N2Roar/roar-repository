# -*- coding: UTF-8 -*-
# -Cleaned and Checked on 07-25-2019 by JewBMX in Scrubs.

import re
from resources.lib.modules import client,cleantitle,source_utils


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['en']
        self.domains = ['flenix.online', 'flenix-hd.online']
        self.base_link = 'http://flenix.online'
        self.search_link = '/?s=%s+%s'


    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            title = cleantitle.geturl(title).replace('-', '+')
            url = self.base_link + self.search_link % (title, year)
            searchPage = client.request(url)
            results = re.compile('<a href="(.+?)" title="(.+?)">').findall(searchPage)
            for url, checkit in results:
                zcheck = '%s (%s)' % (title, year)
                zcheck2 = '%s %s' % (title, year)
                if zcheck.lower() in checkit.lower():
                    return url
                elif zcheck2.lower() in checkit.lower():
                    return url
        except:
            return


    def sources(self, url, hostDict, hostprDict):
        try:
            sources = []
            if url == None:
                return sources
            hostDict = hostDict + hostprDict
            sourcesPage = client.request(url)
            results = re.compile('<iframe.+?src="(.+?)"').findall(sourcesPage)
            for url in results:
                quality, info = source_utils.get_release_quality(url, url)
                valid, host = source_utils.is_host_valid(url, hostDict)
                sources.append({'source': host, 'quality': quality, 'language': 'en', 'url': url, 'info': info, 'direct': False, 'debridonly': False})
            return sources
        except:
            return sources


    def resolve(self, url):
        return url


