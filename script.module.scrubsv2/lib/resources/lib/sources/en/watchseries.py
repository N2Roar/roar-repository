# -*- coding: UTF-8 -*-
# -Cleaned and Checked on 06-17-2019 by JewBMX in Scrubs.

import re,urllib,urlparse
from resources.lib.modules import cleantitle,client,dom_parser,source_utils


class source:
    def __init__(self):
        self.priority = 1
        self.language = ['en']
        self.domains = ['watch-series.live', 'watch-series.co'] # Old  watch-series.ru
        self.base_link = 'https://www2.watch-series.live'
        self.search_link = '/search.html?keyword=%s'
# https://ww4.watch-series.co/
# https://www2.watch-series.live/series/the-code-season-1-episode-10


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
            url = self.base_link + '/series/' + url + '-season-' + season + '-episode-' + episode
            return url
        except:
            return


    def sources(self, url, hostDict, hostprDict):
        try:
            sources = []
            if url == None:
                return sources
            hostDict += ['akamaized.net', 'google.com', 'picasa.com', 'blogspot.com']
            result = client.request(url, timeout=10)
            dom = dom_parser.parse_dom(result, 'a', req='data-video')
            urls = [i.attrs['data-video'] if i.attrs['data-video'].startswith('http') else 'https:' + i.attrs['data-video'] for i in dom]
            for url in urls:
                dom = []
                if 'vidnode.net' in url:
                    result = client.request(url, timeout=10)
                    dom = dom_parser.parse_dom(result, 'source', req=['src','label'])
                    dom = [(i.attrs['src'] if i.attrs['src'].startswith('http') else 'https:' + i.attrs['src'], i.attrs['label']) for i in dom if i]
                elif 'ocloud.stream' in url:
                    result = client.request(url, timeout=10)
                    base = re.findall('<base href="([^"]+)">', result)[0]
                    hostDict += [base]
                    dom = dom_parser.parse_dom(result, 'a', req=['href','id'])
                    dom = [(i.attrs['href'].replace('./embed',base+'embed'), i.attrs['id']) for i in dom if i]
                    dom = [(re.findall("var\s*ifleID\s*=\s*'([^']+)", client.request(i[0]))[0], i[1]) for i in dom if i]                        
                if dom:                
                    try:
                        for r in dom:
                            valid, hoster = source_utils.is_host_valid(r[0], hostDict)
                            if not valid:
                                continue
                            quality = source_utils.label_to_quality(r[1])
                            urls, host, direct = source_utils.check_directstreams(r[0], hoster)
                            for x in urls:
                                if direct:
                                    size = source_utils.get_size(x['url'])
                                if size:
                                    sources.append({'source': host, 'quality': quality, 'language': 'en', 'url': x['url'], 'direct': direct, 'debridonly': False, 'info': size})         
                                else:
                                    sources.append({'source': host, 'quality': quality, 'language': 'en', 'url': x['url'], 'direct': direct, 'debridonly': False})         
                    except:
                        pass
                else:
                    valid, hoster = source_utils.is_host_valid(url, hostDict)
                    if not valid:
                        continue
                    try:
                        url.decode('utf-8')
                        sources.append({'source': hoster, 'quality': 'SD', 'language': 'en', 'url': url, 'direct': False, 'debridonly': False})
                    except:
                        pass
            return sources
        except:
            return sources


    def resolve(self, url):
        return url


""" Old Code Saved while search is down.

    def tvshow(self, imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year):
        try:
            url = urlparse.urljoin(self.base_link, self.search_link % urllib.quote_plus(cleantitle.query(tvshowtitle)))
            self.tvshowtitle = tvshowtitle
            return url
        except:
            return


    def episode(self, url, imdb, tvdb, title, premiered, season, episode):
        try:
            if url == None:
                return
            result = client.request(url)
            express = '''<a\s*href="([^"]+)"\s*class="videoHname\s*title"\s*title="%s - Season %s''' % (self.tvshowtitle, season)
            get_season = re.findall(express, result, flags=re.I)[0]
            url = urlparse.urljoin(self.base_link, get_season + '/season')
            result = client.request(url)
            express = '''<div class="vid_info"><span><a href="([^"]+)" title="([^"]+)" class="videoHname">'''
            get_ep = re.findall(express, result, flags=re.I)
            epi = [i[0] for i in get_ep if title.lower() in i[1].lower()]
            get_ep = urlparse.urljoin(self.base_link, epi[0])
            url = get_ep.encode('utf-8')
            return url
        except:
            return

"""