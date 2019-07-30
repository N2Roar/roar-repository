# -*- coding: utf-8 -*-

'''
Venom
'''

import sys ,re , datetime
import urllib, urlparse, json

from resources.lib.modules import trakt
from resources.lib.modules import client
from resources.lib.modules import cache
from resources.lib.modules import metacache
from resources.lib.modules import playcount
from resources.lib.modules import workers

# from resources.lib.modules import utils

# import requests


        self.trakt_link = 'http://api.trakt.tv'
        self.trakt_user = control.setting('trakt.user').strip()
        self.lang = control.apiLanguage()['trakt']

        self.traktlist_link = 'http://api.trakt.tv/users/%s/lists/%s/items'
        self.traktlists_link = 'http://api.trakt.tv/users/me/lists'
        self.traktlikedlists_link = 'http://api.trakt.tv/users/likes/lists?limit=1000000'
        self.traktcollection_link = 'http://api.trakt.tv/users/me/collection/movies'
        self.traktwatchlist_link = 'http://api.trakt.tv/users/me/watchlist/movies'
        self.trakthistory_link = 'http://api.trakt.tv/users/me/history/movies?limit=%d&page=1' % self.count
        self.traktunfinished_link = 'http://api.trakt.tv/sync/playback/movies'

        self.traktanticipated_link = 'http://api.trakt.tv/movies/anticipated?limit=%d&page=1' % self.count
        self.traktrecommendations_link = 'http://api.trakt.tv/recommendations/movies?limit=%d' % self.count
        self.trakttrending_link = 'http://api.trakt.tv/movies/trending?limit=40&page=1'
        self.traktboxoffice_link = 'http://api.trakt.tv/movies/boxoffice?limit=40&page=1'
        self.traktpopular_link = 'http://api.trakt.tv/movies/popular?limit=40&page=1'

# https://api.trakt.tv/users/id/collection/type


    def trakt_list(self, url, user):
        try:
            q = dict(urlparse.parse_qsl(urlparse.urlsplit(url).query))
            q.update({'extended': 'full'})
            q = (urllib.urlencode(q)).replace('%2C', ',')
            u = url.replace('?' + urlparse.urlparse(url).query, '') + '?' + q
            result = trakt.getTraktAsJson(u)
            items = []
            for i in result:
                try:
                    movie = i['movie']
                    try: movie['progress'] = max(0, min(1, i['progress'] / 100.0))
                    except: pass
                    items.append(movie)
                except: pass
            if len(items) == 0:
                items = result
        except:
            return
        try:
            q = dict(urlparse.parse_qsl(urlparse.urlsplit(url).query))
            if not int(q['limit']) == len(items): raise Exception()
            q.update({'page': str(int(q['page']) + 1)})
            q = (urllib.urlencode(q)).replace('%2C', ',')
            next = url.replace('?' + urlparse.urlparse(url).query, '') + '?' + q
            next = next.encode('utf-8')
        except:
            next = ''

        for item in items:
            try:
                title = item['title']
                title = client.replaceHTMLCodes(title)
                # title = title.encode('utf-8')

                year = item['year']
                year = re.sub('[^0-9]', '', str(year))
                year = year.encode('utf-8')

                # try:
                    # if int(year) > int((self.datetime).strftime('%Y')): continue
                # except: pass

                try: progress = item['progress']
                except: progress = None

                try:
                    imdb = item['ids']['imdb']
                    imdb = 'tt' + re.sub('[^0-9]', '', str(imdb))
                    imdb = imdb.encode('utf-8')
                except: imdb = '0'

                tmdb = str(item.get('ids', {}).get('tmdb', 0))

                try:
                    premiered = item['released']
                    premiered = re.compile('(\d{4}-\d{2}-\d{2})').findall(premiered)[0]
                    premiered = premiered.encode('utf-8')
                except: premiered = '0'

                try:
                    genre = item['genres']
                    genre = [i.title() for i in genre]
                    genre = ' / '.join(genre)
                    genre = genre.encode('utf-8')
                except: genre = 'NA'

                try:
                    duration = str(item['runtime'])
                    duration = duration.encode('utf-8')
                except: duration = '0'

                try:
                    rating = str(item['rating'])
                    rating = rating.encode('utf-8')
                except: rating = '0'

                try:
                    votes = str(item['votes'])
                    votes = str(format(int(votes),',d'))
                    votes = votes.encode('utf-8')
                except: votes = '0'

                try:
                    mpaa = item['certification']
                    mpaa = mpaa.encode('utf-8')
                except: mpaa = '0'

                try:
                    plot = item['overview'].encode('utf-8')
                    plot = client.replaceHTMLCodes(plot)
                    plot = plot.encode('utf-8')
                except: plot = '0'

                try:
                    tagline = item['tagline']
                    tagline = client.replaceHTMLCodes(tagline)
                except: tagline = '0'

                self.list.append({'title': title, 'originaltitle': title, 'year': year, 'premiered': premiered, 'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes, 'mpaa': mpaa, 'plot': plot, 'tagline': tagline, 'imdb': imdb, 'tmdb': tmdb, 'tvdb': '0', 'poster': '0', 'fanart': '0', 'next': next, 'progress': progress})
            except:
                pass
        return self.list



    def trakt_user_list(self, url, user):
        try:
            result = trakt.getTrakt(url)
            items = json.loads(result)

        except:
            pass
        for item in items:
            try:
                try: name = item['list']['name']
                except: name = item['name']
                name = client.replaceHTMLCodes(name)
                name = name.encode('utf-8')

                try: url = (trakt.slug(item['list']['user']['username']), item['list']['ids']['slug'])
                except: url = ('me', item['ids']['slug'])
                url = self.traktlist_link % url
                url = url.encode('utf-8')

                self.list.append({'name': name, 'url': url, 'context': url})
            except:
                pass
        self.list = sorted(self.list, key=lambda k: re.sub('(^the |^a |^an )', '', k['name'].lower()))
        return self.list