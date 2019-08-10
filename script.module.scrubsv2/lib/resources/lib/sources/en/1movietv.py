# -*- coding: UTF-8 -*-
# -Cleaned and Checked on 07-30-2019 by JewBMX in Scrubs.

import re,requests
from resources.lib.modules import control
from resources.lib.modules import cleantitle
from resources.lib.modules import source_utils
import traceback
from resources.lib.modules import log_utils


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['en']
        self.domains = ['1movietv.com']
        self.base_link = 'https://1movietv.com'
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:67.0) Gecko/20100101 Firefox/67.0', 'Referer': self.base_link}
        self.session = requests.Session()
        self.tm_user = control.setting('tm.user')


# 1movietv.com/playstream/{IMDB ID}
# https://1movietv.com/playstream/tt0800369

    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            url = self.base_link + '/playstream/' + imdb
            return url
        except Exception:
            failure = traceback.format_exc()
            log_utils.log('---1movietv Testing - Exception: \n' + str(failure))
            return


    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            tvShowTitle = cleantitle.geturl(tvshowtitle)
            tmdburl = 'https://api.themoviedb.org/3/find/%s?external_source=tvdb_id&language=en-US&api_key=%s' % (tvdb, self.tm_user)
            tmdbresult = self.session.get(tmdburl, headers=self.headers).content
            tmdb_id = re.compile('"id":(.+?),',re.DOTALL).findall(tmdbresult)[0]
            url = '/playstream/' + tmdb_id
            return url
        except Exception:
            failure = traceback.format_exc()
            log_utils.log('---1movietv Testing - Exception: \n' + str(failure))
            return

# 1movietv.com/playstream/{TMDB ID}-{Season}-{Episode}
# https://1movietv.com/playstream/71340-2-1

    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if not url:
                return
            episodeTitle = cleantitle.geturl(title)
            url = self.base_link + url + '-' + season + '-' + episode
            return url
        except Exception:
            failure = traceback.format_exc()
            log_utils.log('---1movietv Testing - Exception: \n' + str(failure))
            return


    def sources(self, url, hostDict, hostprDict):
        try:
            sources = []
            if url == None:
                return sources
            r = self.session.get(url, headers=self.headers).content
            match = re.compile('<iframe.+?src="(.+?)"',re.DOTALL).findall(r)
            for url in match:
                url =  "https:" + url if not url.startswith('http') else url
                valid, host = source_utils.is_host_valid(url, hostDict)
                quality, info = source_utils.get_release_quality(url, url)
                sources.append({'source': host, 'quality': quality, 'language': 'en', 'info': info, 'url': url, 'direct': False, 'debridonly': False})
            return sources
        except Exception:
            failure = traceback.format_exc()
            log_utils.log('---1movietv Testing - Exception: \n' + str(failure))
            return sources


    def resolve(self, url):
        return url



