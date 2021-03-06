# -*- coding: UTF-8 -*-
# -Cleaned and Checked on 10-16-2019 by JewBMX in Scrubs.

import re, urllib, urlparse
from resources.lib.modules import client
from resources.lib.modules import cfscrape
from resources.lib.modules import debrid
from resources.lib.modules import source_utils
import traceback
from resources.lib.modules import log_utils


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['en']  #  Old  0dayddl.com  0dayddl.xyz
        self.domains = ['0daywarez.us']
        self.base_link = 'https://0daywarez.us/'
        self.search_link = '?s=%s'
        self.scraper = cfscrape.create_scraper()


# 0dayddl.biz
# 0dayreleases.com
# 0dayrls.eu
# 0daywarez.us
# downduck.eu
# downturk.eu
# warezcorner.biz


    def movie(self, imdb, title, localtitle, aliases, year):
        try:
            url = {'imdb': imdb, 'title': title, 'year': year}
            url = urllib.urlencode(url)
            return url
        except:
            return


    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            url = {'imdb': imdb, 'tvdb': tvdb, 'tvshowtitle': tvshowtitle, 'year': year}
            url = urllib.urlencode(url)
            return url
        except:
            return


    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if url == None:
                return
            url = urlparse.parse_qs(url)
            url = dict([(i, url[i][0]) if url[i] else (i, '') for i in url])
            url['title'], url['premiered'], url['season'], url['episode'] = title, premiered, season, episode
            url = urllib.urlencode(url)
            return url
        except:
            return


    def sources(self, url, hostDict, hostprDict):
        try:
            sources = []
            if url == None:
                return sources
            if debrid.status() == False:
                raise Exception()
            data = urlparse.parse_qs(url)
            data = dict([(i, data[i][0]) if data[i] else (i, '') for i in data])
            title = data['tvshowtitle'] if 'tvshowtitle' in data else data['title']
            hdlr = 'S%02dE%02d' % (int(data['season']), int(data['episode'])) if 'tvshowtitle' in data else data['year']
            query = '%s S%02dE%02d' % (data['tvshowtitle'], int(data['season']), int(data['episode'])) \
                    if 'tvshowtitle' in data else '%s %s' % (data['title'], data['year'])
            url = self.search_link % urllib.quote_plus(query)
            url = urlparse.urljoin(self.base_link, url).replace('-', '+')
            r = self.scraper.get(url).content
            if r == None and 'tvshowtitle' in data:
                season = re.search('S(.*?)E', hdlr)
                season = season.group(1)
                url = title
                r = self.scraper.get(url).content
            for loopCount in range(0,2):
                if loopCount == 1 or (r == None and 'tvshowtitle' in data):
                    r = self.scraper.get(url).content
                posts = client.parseDOM(r, "h2")
                hostDict = hostprDict + hostDict
                items = []
                for post in posts:
                    try:
                        u = client.parseDOM(post, 'a', ret='href')
                        for i in u:
                            try:
                                name = str(i)
                                items.append(name)
                            except:
                                pass
                    except:
                        pass
                if len(items) > 0:
                    break
            for item in items:
                try:
                    info = []
                    i = str(item)
                    r = self.scraper.get(i).content
                    u = client.parseDOM(r, "div", attrs={"class": "entry-content"})
                    for t in u:
                        r = re.compile('a href="(.+?)">.+?<').findall(t)
                        query = query.replace(' ', '.')
                        for url in r:
                            if not query in url:
                                continue
                            if any(x in url for x in ['.rar', '.zip', '.iso']):
                                raise Exception()
                            quality, info = source_utils.get_release_quality(url)
                            valid, host = source_utils.is_host_valid(url, hostDict)
                            sources.append({'source': host, 'quality': quality, 'language': 'en', 'url': url, 'info': info, 'direct': False, 'debridonly': True})
                except:
                    pass
            check = [i for i in sources if not i['quality'] == 'CAM']
            if check:
                sources = check
            return sources
        except Exception:
            failure = traceback.format_exc()
            log_utils.log('---0dayWarez - Exception: \n' + str(failure))
            return sources


    def resolve(self, url):
        return url


