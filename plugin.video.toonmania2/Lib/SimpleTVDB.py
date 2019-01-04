# -*- coding: utf-8 -*-
import requests
from base64 import b64decode
from datetime import datetime

import xbmc

from Lib.SimpleCache import cache


# Simple TVDB metadata fetcher. UNUSED yet.
# Special thanks to phate89's tvdbsimple for the beautiful educational code: https://github.com/phate89/tvdbsimple

class SimpleTVDB():

    API_BASEURL = 'https://api.thetvdb.com'
    TVDB_IMAGES_BASEURL = 'https://www.thetvdb.com/banners/_cache/'
    
    API_REQUEST_DELAY = 100
    
    # Personal TVDB api key for this add-on only.
    # Go make your own, it's free and fast: https://www.thetvdb.com/member/api
    TOONMANIA2_TVDB_KEY = 'VFVUSk9aOERQSVk2QjFCWQ=='

    PROPERTY_TVDB_TOKEN = 'simpletvdb.token'

    CUSTOM_HEADERS = {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
        'Connection': 'close'
    }


    def getSeriesBasicInfo(self, name):
        r = self.tvdbRequest('/search/series?name=' + name)
        if r.ok:
            seriesRecord = r.json()['data'][0]
            basicInfo = {
                'id': str(seriesRecord['id']),
                'plot': seriesRecord.get('overview', ''),
                'imdb': seriesRecord.get('imdbId','')
            }
            # Get a poster (instead of the banner that comes in the seriesRecord dict).
            r2 = self.tvdbRequest('/series/' + str(seriesRecord['id']) + '/images/query?keyType=poster')
            if r2.ok:
                imageEntry = r2.json()['data'][0] # Just use whatever poster is first.
                basicInfo['poster'] = imageEntry['fileName'] if imageEntry['fileName'] else ''
            else:
                basicInfo['poster'] = None
            return basicInfo
        else:
            return None # May fail if the item is not on TVDB after all.
            
    #def getSeriesEpisodes(seriesID)
    #    (...)


    #def getEpisodeQuery(seriesID, seasonNumber = -1, episodeNumber = -1)
    #    (...)


    def tvdbRequest(self, path, retry = False):
        self.ensureToken()
        
        r = requests.get(self.API_BASEURL + path, headers = self.CUSTOM_HEADERS)
        xbmc.sleep(self.API_REQUEST_DELAY)
        if not r.ok and not retry:
            self.ensureToken(refresh = True)
            r = self.tvdbRequest(path, retry = True) # Maybe the token expired, if 24 hours have passed.
        return r


    def ensureToken(self, refresh = False):
        token = cache.getRawProperty(self.PROPERTY_TVDB_TOKEN)
        if not token:
            r = requests.post(
                self.API_BASEURL + '/login',
                data = '{"apikey":"' + b64decode(self.TOONMANIA2_TVDB_KEY) + '"}',
                headers = self.CUSTOM_HEADERS
            )
            if r.ok:
                token = r.json()['token']
                cache.setRawProperty(self.PROPERTY_TVDB_TOKEN, token)
                self.CUSTOM_HEADERS.update({'Authorization':'Bearer '+ token})
            else:
                self.CUSTOM_HEADERS.pop('Authorization', None)
                raise Exception('TVDB token failed.')
        if refresh:
            r = requests.get(self.API_BASEURL + '/refresh_token', headers = self.CUSTOM_HEADERS)
            if r.ok:
                token = r.json()['token']
                cache.setRawProperty(self.PROPERTY_TVDB_TOKEN, token)
                self.CUSTOM_HEADERS.update({'Authorization':'Bearer '+ token})
            else:
                cache.clearRawProperty(self.PROPERTY_TVDB_TOKEN) # Expired. Use the login route.
                self.CUSTOM_HEADERS.pop('Authorization', None)

                
    def delayBegin(self):
        self.delayStartTime = datetime.now()


    def delayEnd(self, delayOverride = 200):
        elapsed = int((datetime.now() - self.delayStartTime).total_seconds() * 1000)
        if elapsed < delayOverride: # Only delay if we haven't waited the full delay time, obviously.
            sleep(max(delayOverride - elapsed, 100))
                
                
tvdb = SimpleTVDB()
