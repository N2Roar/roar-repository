# -*- coding: UTF-8 -*-
# -Cleaned and Checked on 03-21-2019 by JewBMX in Scrubs.

from resources.lib.modules import cleantitle
from resources.lib.modules import getSum
from resources.lib.modules import source_utils


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['en']  # watchserieshd.co got changed to a different source 
        self.domains = ['watchserieshd.cc']  # Old  watchserieshd.io
        self.base_link = 'https://watchserieshd.cc'
        self.search_link = '/series/%s-season-%s-episode-%s'


    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            url = cleantitle.geturl(tvshowtitle)
            return url
        except:
            return


    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if not url:
                return
            tvshowtitle = url
            url = self.base_link + self.search_link % (tvshowtitle, season, episode)
            return url
        except:
            return


    def sources(self, url, hostDict, hostprDict):
        try:
            if url == None:
                return sources
            sources = []
            hostDict = hostprDict + hostDict
            r = getSum.get(url)
            match = getSum.findSum(r)
            for url in match:
                url = url.replace('xstreamcdn.com', 'fembed.com').replace('gcloud.live', 'fembed.com').replace('femoload.xyz', 'fembed.com').replace('there.to', 'fembed.com') if '/v/' in url else url
                quality, info = source_utils.get_release_quality(url, url)
                valid, host = source_utils.is_host_valid(url, hostDict)
                if not 'vidcloud.icu' in url and valid:
                    sources.append({'source': host, 'quality': quality, 'language': 'en', 'info': info, 'url': url, 'direct': False, 'debridonly': False})
            return sources
        except Exception:
            return sources


    def resolve(self, url):
        return url


