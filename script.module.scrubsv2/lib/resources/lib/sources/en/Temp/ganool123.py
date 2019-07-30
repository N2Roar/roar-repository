# -*- coding: UTF-8 -*-
# -Cleaned and Checked on 06-17-2019 by JewBMX in Scrubs.
# -Update by Tempest (Pulls links for RD users)

import re, urllib, urlparse
from resources.lib.modules import cleantitle
from resources.lib.modules import source_utils
from resources.lib.modules import debrid
from resources.lib.modules import cfscrape

import traceback
from resources.lib.modules import log_utils


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['en'] # Old  ganool.ws
        self.domains = ['ganool.bz', 'ganol.si', 'ganool123.com']
        self.base_link = 'https://ganool.bz'
        self.search_link = '/search/?q=%s'
        self.scraper = cfscrape.create_scraper()


    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            url = {'imdb': imdb, 'title': title, 'year': year}
            url = urllib.urlencode(url)
            return url
        except:
            return


    def sources(self, url, hostDict, hostprDict):
        sources = []
        try:
            if url is None:
                return sources
            if debrid.status() is False:
                raise Exception()
            data = urlparse.parse_qs(url)
            data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])
            q = '%s' % cleantitle.get_gan_url(data['title'])
            url = self.base_link + self.search_link % q
            r = self.scraper.get(url).content
            v = re.compile('<a href="(.+?)" class="ml-mask jt" title="(.+?)">\n<span class=".+?">(.+?)</span>').findall(r)
            for url, check, quality in v:
                t = '%s (%s)' % (data['title'], data['year'])
                if t.lower() not in check.lower():
                    raise Exception()
                key = url.split('-hd')[1]
                r = self.scraper.get('https://ganool.bz/moviedownload.php?q=' + key).content
                r = re.compile('<a rel=".+?" href="(.+?)" target=".+?">').findall(r)
                for url in r:
                    if any(x in url for x in ['.rar']):
                        continue
                    quality = source_utils.check_url(quality)
                    valid, host = source_utils.is_host_valid(url, hostDict)
                    if not valid:
                        continue
                    sources.append({'source': host, 'quality': quality, 'language': 'en', 'url': url, 'direct': False, 'debridonly': True})
            return sources
        except Exception:
            failure = traceback.format_exc()
            log_utils.log('---ganool.bz Testing - Exception: \n' + str(failure))
            return sources


    def resolve(self, url):
        return url


