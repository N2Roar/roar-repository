# -*- coding: UTF-8 -*-
#######################################################################
 # ----------------------------------------------------------------------------
 # "THE BEER-WARE LICENSE" (Revision 42):
 # @tantrumdev wrote this file.  As long as you retain this notice you
 # can do whatever you want with this stuff. If we meet some day, and you think
 # this stuff is worth it, you can buy me a beer in return. - Muad'Dib
 # ----------------------------------------------------------------------------
#######################################################################

# Addon Name: Yoda
# Addon id: plugin.video.Yoda
# Addon Provider: Supremacy

import re
from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import source_utils


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['en']
        self.domains = ['alluc.xyz']
        self.base_link = 'https://alluc.xyz'
        self.search_link = '/?s=%s+%s'

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            title = cleantitle.geturl(title).replace('-', '+')
            url = self.base_link + self.search_link % (title, year)
            return url
        except:
            return

    def sources(self, url, hostDict, hostprDict):
        try:
            hostDict = hostDict + hostprDict
            sources = []
            r = client.request(url)
            u = client.parseDOM(r, "div", attrs={"class": "item"})
            for i in u:
                t = re.compile('<a href="(.+?)"').findall(i)
                for r in t:
                    t = client.request(r)
                    u = client.parseDOM(t, "ul", attrs={"class": "enlaces"})
                    r = re.compile('<a href="(.+?)"').findall(t)
                    for url in r:
                        if '1080p' in url: quality = '1080p'
                        elif '720p' in url: quality = '720p'
                        elif 'HDRip' in url: quality = '720p'
                        elif 'hdtv' in url: quality = '720p'
                        else: quality = 'SD'
                        valid, host = source_utils.is_host_valid(url, hostDict)
                        if not host in hostDict:
                            continue
                        sources.append({'source': host, 'quality': quality, 'language': 'en', 'url': url, 'direct': False, 'debridonly': False})
                    return sources
        except Exception:
            return

    def resolve(self, url):
        return url