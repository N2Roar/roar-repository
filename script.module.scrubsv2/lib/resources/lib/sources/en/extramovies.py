# -*- coding: UTF-8 -*-
# -Cleaned and Checked on 06-17-2019 by JewBMX in Scrubs.

import re,urllib,urlparse,base64
from resources.lib.modules import cleantitle,source_utils,cfscrape
import traceback
from resources.lib.modules import log_utils


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['en']
        self.domains = ['extramovies.trade', 'extramovies.guru', 'extramovies.wiki'] # http://extramovies.ind.in/
        self.base_link = 'http://extramovies.wiki' # Dead  extramovies.host
        self.search_link = '/?s=%s'
        self.scraper = cfscrape.create_scraper()


    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            aliases.append({'country': 'us', 'title': title})
            url = {'imdb': imdb, 'title': title, 'year': year, 'aliases': aliases}
            url = urllib.urlencode(url)
            return url
        except:
            return


    def sources(self, url, hostDict, hostprDict):
        try:
            sources = []
            self.hostDict = hostDict + hostprDict
            if url == None:
                return sources
            data = urlparse.parse_qs(url)
            data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])
            title = data['title']
            url = urlparse.urljoin(self.base_link, self.search_link % urllib.quote_plus(cleantitle.query(title)))
            html = self.scraper.get(url).content
            match = re.compile('<div class="thumbnail".+?href="(.+?)" title="(.+?)"', re.DOTALL | re.IGNORECASE).findall(html)
            for url, item_name in match:
                if cleantitle.getsearch(title).lower() in cleantitle.getsearch(item_name).lower():
                    quality, info = source_utils.get_release_quality(url, url)
                    result = self.scraper.get(url).content
                    regex = re.compile('href="/download.php.+?link=(.+?)"', re.DOTALL | re.IGNORECASE).findall(result)
                    for link in regex:
                        if 'server=' not in link:
                            try:
                                link = base64.b64decode(link)
                            except:
                                pass
                            valid, host = source_utils.is_host_valid(link, self.hostDict)
                            if valid:
                                sources.append({'source': host, 'quality': quality, 'language': 'en', 'info': info, 'url': link, 'direct': False, 'debridonly': False})
            return sources
        except Exception:
            failure = traceback.format_exc()
            log_utils.log('---ExtraMovies Testing - Exception: \n' + str(failure))
            return sources


    def resolve(self, url):
        return url


