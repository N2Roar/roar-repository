# -*- coding: UTF-8 -*-
# -Cleaned and Checked on 07-24-2018 by JewBMX in Scrubs.
# Sites ass and barely has much. Tested with new walking dead episodes.

import re,requests
from resources.lib.modules import cleantitle
from resources.lib.modules import source_utils


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['en']
        self.domains = ['get.mywatchseries.stream', 'go.mywatchseries.stream']
        self.base_link = 'https://get.mywatchseries.stream'
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0', 'Referer': self.base_link}
        self.session = requests.Session()


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
            tvshowTitle = url
            episodeTitle = cleantitle.geturl(title)
            url = self.base_link + '/' + tvshowTitle + '-' + season + 'x' + episode + '-' + episodeTitle
            return url
        except:
            return


    def sources(self, url, hostDict, hostprDict):
        try:
            sources = []
            if url == None:
                return sources
            hostDict = hostprDict + hostDict
            page = self.session.get(url, headers=self.headers).content
            match = re.compile('<a class="w3-btn w3-white w3-border w3-round" title="(.+?)" rel="nofollow" target="_blank" href="(.+?)" class', re.DOTALL).findall(page)
            for hoster, url in match:
                valid, host = source_utils.is_host_valid(hoster, hostDict)
                if source_utils.limit_hosts() is True and hoster in str(sources):
                    continue
                url = self.base_link + url
                sources.append({'source': host, 'quality': 'SD', 'language': 'en', 'url': url, 'direct': False, 'debridonly': False})
            return sources
        except:
            return sources


    def resolve(self, url):
        try:
            page2 = self.session.get(url, headers=self.headers).content
            match2 = re.compile('<a rel="external nofollow" href="(.+?)" class', re.DOTALL).findall(page2)
            for link in match2:
                url = requests.get(link, headers=self.headers).url
                return url
        except:
            return url


