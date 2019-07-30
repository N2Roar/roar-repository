# -*- coding: UTF-8 -*-
# -Cleaned and Checked on 07-02-2019 by JewBMX in Scrubs.

import re,requests,urlparse
from resources.lib.modules import client,cleantitle,tvmaze
from resources.lib.modules import source_utils,source_tools


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['en']
        self.genre_filter = ['animation', 'anime']
        self.domains = ['cartoontab.com']
        self.base_link = 'http://cartoontab.com'
        self.search_link = '/toon/search?key=%s'


    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            title = cleantitle.geturl(title)
            url = '%s-%s' % (title, year)
            url = self.base_link + '/' + url
            return url
        except:
            return


    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            tv_maze = tvmaze.tvMaze()
            tvshowtitle = tv_maze.showLookup('thetvdb', tvdb)
            tvshowtitle = tvshowtitle['name']
            t = cleantitle.get(tvshowtitle)
            q = self.base_link + self.search_link %(tvshowtitle)
            r = client.request(q)
            r = client.parseDOM(r, 'div', attrs={'class': 'featured-image'})
            for i in r:
                match = re.compile('<a href="(.+?)"',re.DOTALL).findall(i)
                for url in match:
                    if t in cleantitle.get(url):
                        return source_utils.strip_domain(url)
        except:
            return


    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if not url:
                return
            if season == '1': 
                url = self.base_link + url + '-episode-' + episode
            else:
                url = self.base_link + url + '-season-' + season + '-episode-' + episode
            return url
        except:
            return


    def sources(self, url, hostDict, hostprDict):
        try:
            hostDict = hostDict + hostprDict
            sources = []
            if url == None:
                return sources
            r = client.request(url)
            match = re.compile('<iframe.+?src="(.+?)"',re.DOTALL).findall(r)
            for url in match:
                quality = source_tools.get_quality(url)
                info = source_tools.get_info(url)
                valid, host = source_utils.is_host_valid(url, hostDict)
                if valid or 'gogoanime' in url:
                    sources.append({'source': host, 'quality': quality, 'language': 'en', 'url': url, 'info': info, 'direct': False, 'debridonly': False})
            return sources
        except:
            return sources


    def resolve(self, url):
        try:
            open = requests.get(url, timeout=3).content
            if 'gogoanime' in url:
                url = re.compile('"link":"(.+?)"',re.DOTALL).findall(open)[0]
                url = url.replace('\\','')
        except:
            pass
        return url


