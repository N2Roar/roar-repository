# -*- coding: UTF-8 -*-
# -Cleaned and Checked on 07-25-2019 by JewBMX in Scrubs.

import re
from resources.lib.modules import client
from resources.lib.modules import cfscrape
from resources.lib.modules import cleantitle
from resources.lib.modules import source_utils


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['en']
        self.domains = ['putlockerfree.sc']
        self.base_link = 'https://www4.putlockerfree.sc'
        self.search_link = '/search-query/%s+%s'
        self.scraper = cfscrape.create_scraper()


    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            mtitle = cleantitle.geturl(title).replace('-', '+')
            u = self.base_link + self.search_link % (mtitle, year)
            u = self.scraper.get(u).content
            i = client.parseDOM(u, "div", attrs={"class": "movies-list movies-list-full"})
            for r in i:
                r = re.compile('<a href="(.+?)"').findall(r)
                for url in r:
                    ctitle = cleantitle.geturl(title).replace("+", "-")
                    if not ctitle in url:
                        continue
                    return url
        except:
            return


    def sources(self, url, hostDict, hostprDict):
        try:
            sources = []
            url = url + "watching.html/"
            r = self.scraper.get(url).content
            t = re.compile('data-.+?="(.+?)".+?href="javascript:void').findall(r)
            for url in t:
                valid, host = source_utils.is_host_valid(url, hostDict)
                if valid:
                    quality, info = source_utils.get_release_quality(url, url)
                    sources.append({'source': host, 'quality': quality, 'language': 'en', 'info': info, 'url': url, 'direct': False, 'debridonly': False})
            return sources
        except:
            return sources


    def resolve(self, url):
        return url


