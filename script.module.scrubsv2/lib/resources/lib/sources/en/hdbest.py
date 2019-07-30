# -*- coding: UTF-8 -*-
# -Cleaned and Checked on 07-18-2019 by JewBMX in Scrubs.

import re,requests
from resources.lib.modules import cleantitle,directstream
from resources.lib.modules import getSum,source_utils


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['en']
        self.domains = ['hdbest.net']
        self.base_link = 'https://hdbest.net'
        self.movie_link = '/watch/%s-%s.html'
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0', 'Referer': self.base_link}
        self.session = requests.Session()


    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            mtitle = cleantitle.geturl(title)
            url = self.base_link + self.movie_link % (mtitle, year)
            return url
        except:
            return


    def sources(self, url, hostDict, hostprDict):
        try:
            sources = []
            if url == None:
                return sources
            hostDict = hostprDict + hostDict
            r = self.session.get(url, headers=self.headers).content
            match = getSum.findSum(r)
            for url in match:
                if "api.hdv.fun" in url:
                    r2 = self.session.get(url, headers=self.headers).content
                    match2 = getSum.findEm(r2, '<source src= "(.+?)" type="(.+?)" .+? label="(.+?)"')
                    if match2:
                        for url2, inf, qua in match2:
                            quainf = '%s - %s' % (inf, qua)
                            quality, info = source_utils.get_release_quality(quainf, quainf)
                            valid, host = source_utils.is_host_valid(url2, hostDict)
                            sources.append({'source': host, 'quality': quality, 'language': 'en', 'url': url2, 'info': info, 'direct': False, 'debridonly': False})
            return sources
        except:
            return sources


    def resolve(self, url):
        if 'google' in url and not 'googleapis' in url:
            return directstream.googlepass(url)
        else:
            return url


