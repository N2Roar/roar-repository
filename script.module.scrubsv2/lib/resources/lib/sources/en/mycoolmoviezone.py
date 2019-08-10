# -*- coding: UTF-8 -*-
# -Cleaned and Checked on 02-01-2019 by JewBMX in Scrubs.

import re
from resources.lib.modules import cleantitle,client,source_utils


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['en']  #  coolmoviezone.online
        self.domains = ['coolmoviezone.io']
        self.base_link = 'https://coolmoviezone.io'


    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            mtitle = cleantitle.geturl(title)
            url = self.base_link + '/%s-%s' % (mtitle, year)
            return url
        except:
            return


    def sources(self, url, hostDict, hostprDict):
        try:
            sources = []
            hostDict = hostprDict + hostDict
            r = client.request(url)
            match = re.compile('<td align="center"><strong><a href="(.+?)"').findall(r)
            for url in match:
                valid, host = source_utils.is_host_valid(url, hostDict)
                if valid:
                    quality, info = source_utils.get_release_quality(url, url)
                    sources.append({'source': host, 'quality': quality, 'language': 'en', 'url': url, 'info': info, 'direct': False, 'debridonly': False})
            return sources
        except Exception:
            return sources


    def resolve(self, url):
        return url


