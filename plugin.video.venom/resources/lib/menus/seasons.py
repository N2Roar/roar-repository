# -*- coding: utf-8 -*-

'''
    Venom Add-on
'''

import os, sys, re, json, zipfile
import StringIO, urllib, urllib2, urlparse, datetime

from resources.lib.modules import trakt
from resources.lib.modules import cleantitle
from resources.lib.modules import cleangenre
from resources.lib.modules import control
from resources.lib.modules import client
from resources.lib.modules import cache
from resources.lib.modules import playcount
from resources.lib.modules import views

from resources.lib.menus import episodes as episodesx
from resources.lib.menus import tvshows as tvshowsx


params = dict(urlparse.parse_qsl(sys.argv[2].replace('?',''))) if len(sys.argv) > 1 else dict()
action = params.get('action')


class Seasons:
    def __init__(self, type = 'show'):
        self.list = []
        self.type = type
        self.lang = control.apiLanguage()['tvdb']
        self.season_special = False

        self.datetime = (datetime.datetime.utcnow() - datetime.timedelta(hours = 5))
        self.today_date = (self.datetime).strftime('%Y-%m-%d')

        # self.tvdb_key = control.setting('tvdb.user')
        # if self.tvdb_key == '' or self.tvdb_key is None:
        self.tvdb_key = 'MUQ2MkYyRjkwMDMwQzQ0NA=='

        self.tvdb_info_link = 'http://thetvdb.com/api/%s/series/%s/all/%s.zip' % (self.tvdb_key.decode('base64'), '%s', '%s')
        self.tvdb_by_imdb = 'http://thetvdb.com/api/GetSeriesByRemoteID.php?imdbid=%s'
        self.tvdb_by_query = 'http://thetvdb.com/api/GetSeries.php?seriesname=%s'
        self.tvdb_image = 'http://thetvdb.com/banners/'
        self.tvdb_poster = 'http://thetvdb.com/banners/_cache/'

        self.trakt_user = control.setting('trakt.user').strip()
        self.traktCredentials = trakt.getTraktCredentialsInfo()

        self.showunaired = control.setting('showunaired') or 'true'
        self.unairedcolor = control.setting('unaired.identify')
        if self.unairedcolor == '': self.unairedcolor = 'red'
        self.unairedcolor = self.getUnairedColor(self.unairedcolor)


    def getUnairedColor(self, n):
        if n == '0': n = 'blue'
        elif n == '1': n = 'red'
        elif n == '2': n = 'yellow'
        elif n == '3': n = 'deeppink'
        elif n == '4': n = 'cyan'
        elif n == '5': n = 'lawngreen'
        elif n == '6': n = 'gold'
        elif n == '7': n = 'magenta'
        elif n == '8': n = 'yellowgreen'
        elif n == '9': n = 'nocolor'
        else: n == 'blue'
        return n


    @classmethod
    def mark(self, title, imdb, tvdb, season, watched = True):
        if watched: self.markWatch(title = title, imdb = imdb, tvdb = tvdb, season = season)
        else: self.markUnwatch(title = title, imdb = imdb, tvdb = tvdb, season = season)


    @classmethod
    def markWatch(self, title, imdb, tvdb, season):
        interface.Loader.show()
        playcount.seasons(title, imdb, tvdb, season, '7')
        interface.Loader.hide()
        interface.Dialog.notification(title = 35513, message = 35510, icon = interface.Dialog.IconSuccess)


    @classmethod
    def markUnwatch(self, title, imdb, tvdb, season):
        interface.Loader.show()
        playcount.seasons(title, imdb, tvdb, season, '6')
        interface.Loader.hide()
        interface.Dialog.notification(title = 35513, message = 35511, icon = interface.Dialog.IconSuccess)


    def get(self, tvshowtitle, year, imdb, tvdb, idx=True):
        if idx is True:
            self.list = cache.get(self.tvdb_list, 24, tvshowtitle, year, imdb, tvdb, self.lang)
            # self.list = cache.get(self.tvdb_list, 24, tvshowtitle, year, imdb, tmdb, tvdb, self.lang)
            self.seasonDirectory(self.list)
            return self.list
        else:
            self.list = self.tvdb_list(tvshowtitle, year, imdb, tvdb, 'en')
            # self.list = self.tvdb_list(tvshowtitle, year, imdb, tmdb, tvdb, 'en')
            return self.list


    def seasonList(self, url):
        # Dirty implementation, but avoids rewritting everything from episodes.py.
        episodes = episodesx.Episodes(type = self.type)
        self.list = cache.get(episodes.trakt_list, 0, url, self.trakt_user)
        self.list = self.list[::-1]

        tvshows = tvshowsx.tvshows(type = self.type)
        tvshows.list = self.list
        tvshows.worker()
        self.list = tvshows.list

        # Remove duplicate season entries.
        try:
            result = []
            for i in self.list:
                found = False
                for j in result:
                    if i['imdb'] == j['imdb'] and i['season'] == j['season']:
                        found = True
                        break
                if not found:
                    result.append(i)
            self.list = result
        except: pass

        self.seasonDirectory(self.list)


    def userlists(self):
        episodes = episodesx.Episodes(type = self.type)
        userlists = []

        try:
            if self.traktCredentials is False:
                raise Exception()
            activity = trakt.getActivity()
        except:
            pass

        try:
            if self.traktCredentials is False:
                raise Exception()
            self.list = []
            try:
                if activity > cache.timeout(episodes.trakt_user_list, self.traktlists_link, self.trakt_user): raise Exception()
                userlists += cache.get(episodes.trakt_user_list, 3, self.traktlists_link, self.trakt_user)
            except:
                userlists += cache.get(episodes.trakt_user_list, 0, self.traktlists_link, self.trakt_user)
        except:
            pass

        try:
            if self.traktCredentials is False:
                raise Exception()
            self.list = []
            try:
                if activity > cache.timeout(episodes.trakt_user_list, self.traktlikedlists_link, self.trakt_user): raise Exception()
                userlists += cache.get(episodes.trakt_user_list, 3, self.traktlikedlists_link, self.trakt_user)
            except:
                userlists += cache.get(episodes.trakt_user_list, 0, self.traktlikedlists_link, self.trakt_user)
        except:
            pass

        self.list = []

        # Filter the user's own lists that were
        for i in range(len(userlists)):
            contains = False
            adapted = userlists[i]['url'].replace('/me/', '/%s/' % self.trakt_user)
            for j in range(len(self.list)):
                if adapted == self.list[j]['url'].replace('/me/', '/%s/' % self.trakt_user):
                    contains = True
                    break
            if not contains:
                self.list.append(userlists[i])

        for i in range(0, len(self.list)): self.list[i].update({'image': 'traktlists.png', 'action': 'seasonsList'})

        # Watchlist
        if self.traktCredentials is True:
            self.list.insert(0, {'name': control.lang(32033).encode('utf-8'), 'url': self.traktwatchlist_link, 'image': 'traktwatch.png', 'action': 'seasons'})

        episodes.addDirectory(self.list, queue = True)
        return self.list


    def tvdb_list(self, tvshowtitle, year, imdb, tvdb, lang, limit = ''):
        tmdb = '0'
        try:
            # if imdb == '0' or tmdb == '0' or tvdb == '0':
            if imdb == '0' or tvdb == '0':
                trakt_ids = trakt.SearchTVShow(urllib.quote_plus(tvshowtitle), year, full=False)[0]
                trakt_ids = trakt_ids.get('show', '0')

                imdb = str(trakt_ids.get('ids', {}).get('imdb', '0'))
                if imdb == '' or imdb is None:
                    imdb = '0'

                tmdb = trakt_ids.get('ids', {}).get('tmdb')
                if tmdb == '' or tmdb is None:
                    tmdb = '0'

                tvdb = trakt_ids.get('ids', {}).get('tvdb')
                if tvdb == '' or tvdb is None:
                    tvdb = '0'

            if tvdb == '0' and imdb != '0':
                url = self.tvdb_by_imdb % imdb
                result = client.request(url, timeout='10')

                try:
                    tvdb = client.parseDOM(result, 'seriesid')[0]
                except:
                    tvdb = '0'

                try:
                    name = client.parseDOM(result, 'SeriesName')[0]
                except:
                    name = '0'

                dupe = re.compile('[***]Duplicate (\d*)[***]').findall(name)
                if len(dupe) > 0:
                    tvdb = str(dupe[0])

                if tvdb == '':
                    tvdb = '0'

            if tvdb == '0':
                url = self.tvdb_by_query % (urllib.quote_plus(tvshowtitle))

                years = [str(year), str(int(year)+1), str(int(year)-1)]

                tvdb = client.request(url, timeout='10')
                tvdb = re.sub(r'[^\x00-\x7F]+', '', tvdb)
                tvdb = client.replaceHTMLCodes(tvdb)
                tvdb = client.parseDOM(tvdb, 'Series')
                tvdb = [(x, client.parseDOM(x, 'SeriesName'), client.parseDOM(x, 'FirstAired')) for x in tvdb]
                tvdb = [(x, x[1][0], x[2][0]) for x in tvdb if len(x[1]) > 0 and len(x[2]) > 0]
                tvdb = [x for x in tvdb if cleantitle.get(tvshowtitle) == cleantitle.get(x[1])]
                tvdb = [x[0][0] for x in tvdb if any(y in x[2] for y in years)][0]
                tvdb = client.parseDOM(tvdb, 'seriesid')[0]

                if tvdb == '':
                    tvdb = '0'
        except:
            return

        try:
            if tvdb == '0':
                return

            url = self.tvdb_info_link % (tvdb, 'en')
            data = urllib2.urlopen(url, timeout=30).read()

            zip = zipfile.ZipFile(StringIO.StringIO(data))
            result = zip.read('%s.xml' % 'en')
            artwork = zip.read('banners.xml')
            zip.close()

            dupe = client.parseDOM(result, 'SeriesName')[0]
            dupe = re.compile('[***]Duplicate (\d*)[***]').findall(dupe)

            if len(dupe) > 0:
                tvdb = str(dupe[0]).encode('utf-8')

                url = self.tvdb_info_link % (tvdb, 'en')
                data = urllib2.urlopen(url, timeout=30).read()

                zip = zipfile.ZipFile(StringIO.StringIO(data))
                result = zip.read('%s.xml' % 'en')
                artwork = zip.read('banners.xml')
                zip.close()

            if lang != 'en':
                url = self.tvdb_info_link % (tvdb, lang)
                data = urllib2.urlopen(url, timeout=30).read()

                zip = zipfile.ZipFile(StringIO.StringIO(data))
                result2 = zip.read('%s.xml' % lang)
                zip.close()
            else:
                result2 = result

            artwork = artwork.split('<Banner>')
            artwork = [i for i in artwork if '<Language>en</Language>' in i and '<BannerType>season</BannerType>' in i]
            artwork = [i for i in artwork if not 'seasonswide' in re.findall('<BannerPath>(.+?)</BannerPath>', i)[0]]

            result = result.split('<Episode>')
            result2 = result2.split('<Episode>')

            item = result[0]
            item2 = result2[0]

            episodes = [i for i in result if '<EpisodeNumber>' in i]

            if control.setting('tv.specials') == 'true':
                episodes = [i for i in episodes]
            else:
                episodes = [i for i in episodes if not '<SeasonNumber>0</SeasonNumber>' in i]
                episodes = [i for i in episodes if not '<EpisodeNumber>0</EpisodeNumber>' in i]

            seasons = [i for i in episodes if '<EpisodeNumber>1</EpisodeNumber>' in i]
            counts = self.seasonCountParse(seasons = seasons, episodes = episodes)
            locals = [i for i in result2 if '<EpisodeNumber>' in i]

            result = ''
            result2 = ''

            if limit == '':
                episodes = []
            elif limit == '-1':
                seasons = []
            else:
                episodes = [i for i in episodes if '<SeasonNumber>%01d</SeasonNumber>' % int(limit) in i]
                seasons = []
            try:
                poster = client.parseDOM(item, 'poster')[0]
            except:
                poster = ''
            if poster != '':
                poster = self.tvdb_image + poster
            else:
                poster = '0'
            poster = client.replaceHTMLCodes(poster)
            poster = poster.encode('utf-8')

            try:
                banner = client.parseDOM(item, 'banner')[0]
            except:
                banner = ''
            if banner != '':
                banner = self.tvdb_image + banner
            else:
                banner = '0'
            banner = client.replaceHTMLCodes(banner)
            banner = banner.encode('utf-8')

            try:
                fanart = client.parseDOM(item, 'fanart')[0]
            except:
                fanart = ''
            if fanart != '':
                fanart = self.tvdb_image + fanart
            else:
                fanart = '0'
            fanart = client.replaceHTMLCodes(fanart)
            fanart = fanart.encode('utf-8')

            if poster != '0':
                pass
            elif fanart != '0':
                poster = fanart
            elif banner != '0':
                poster = banner

            if banner != '0':
                pass
            elif fanart != '0':
                banner = fanart
            elif poster != '0':
                banner = poster

            try:
                status = client.parseDOM(item, 'Status')[0]
            except:
                status = ''
            if status == '':
                status = 'Ended'
            status = client.replaceHTMLCodes(status)
            status = status.encode('utf-8')

            try:
                studio = client.parseDOM(item, 'Network')[0]
            except:
                studio = ''
            if studio == '':
                studio = '0'
            studio = client.replaceHTMLCodes(studio)
            studio = studio.encode('utf-8')

            try:
                genre = client.parseDOM(item, 'Genre')[0]
            except:
                genre = ''
            genre = [x for x in genre.split('|') if x != '']
            genre = ' / '.join(genre)
            if genre == '':
                genre = '0'
            genre = client.replaceHTMLCodes(genre)
            genre = genre.encode('utf-8')

            try:
                duration = client.parseDOM(item, 'Runtime')[0]
            except:
                duration = ''
            if duration == '':
                duration = '0'
            duration = client.replaceHTMLCodes(duration)
            duration = duration.encode('utf-8')

            try:
                rating = client.parseDOM(item, 'Rating')[0]
                rating = client.replaceHTMLCodes(rating)
                rating = rating.encode('utf-8')
            except:
                rating = '0'

            try:
                votes = client.parseDOM(item, 'RatingCount')[0]
                votes = client.replaceHTMLCodes(votes)
                votes = votes.encode('utf-8')
            except:
                votes = '0'

            try:
                mpaa = client.parseDOM(item, 'ContentRating')[0]
                mpaa = client.replaceHTMLCodes(mpaa)
                mpaa = mpaa.encode('utf-8')
            except:
                mpaa = '0'

            try:
                cast = client.parseDOM(item, 'Actors')[0]
                cast = [x for x in cast.split('|') if x != '']
                cast = [(x.encode('utf-8'), '') for x in cast]
            except:
                cast = []

            try:
                label = client.parseDOM(item2, 'SeriesName')[0]
            except:
                label = '0'
            label = client.replaceHTMLCodes(label)
            label = label.encode('utf-8')

            try:
                plot = client.parseDOM(item2, 'Overview')[0]
            except:
                plot = ''
            if plot == '':
                plot = '0'
            plot = client.replaceHTMLCodes(plot)
            plot = plot.encode('utf-8')

            unaired = ''

        except:
            pass

        for item in seasons:
            try:
                premiered = client.parseDOM(item, 'FirstAired')[0]
                if premiered == '' or '-00' in premiered: premiered = '0'
                premiered = client.replaceHTMLCodes(premiered)
                premiered = premiered.encode('utf-8')

                # Show Unaired items.
                if status == 'Ended':
                    pass
                elif premiered == '0':
                    raise Exception()
                elif int(re.sub('[^0-9]', '', str(premiered))) > int(re.sub('[^0-9]', '', str(self.today_date))):
                    unaired = 'true'
                    if self.showunaired != 'true':
                        raise Exception()

                season = client.parseDOM(item, 'SeasonNumber')[0]
                season = '%01d' % int(season)
                season = season.encode('utf-8')

                thumb = [i for i in artwork if client.parseDOM(i, 'Season')[0] == season]
                try:
                    thumb = client.parseDOM(thumb[0], 'BannerPath')[0]
                except:
                    thumb = ''
                if thumb != '':
                    thumb = self.tvdb_image + thumb
                else:
                    thumb = '0'
                thumb = client.replaceHTMLCodes(thumb)
                thumb = thumb.encode('utf-8')

                if thumb == '0': thumb = poster

                try:
                    seasoncount = counts[season]
                except:
                    seasoncount = None

                self.list.append({'season': season, 'seasoncount': seasoncount, 'tvshowtitle': tvshowtitle, 'label': label, 'year': year, 'premiered': premiered, 'status': status,
                                            'studio': studio, 'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes, 'mpaa': mpaa, 'cast': cast, 'plot': plot, 'imdb': imdb,
                                            'tmdb': tmdb, 'tvdb': tvdb, 'tvshowid': imdb, 'poster': poster, 'banner': banner, 'fanart': fanart, 'thumb': thumb, 'unaired': unaired})

            except:
                pass

        for item in episodes:
            try:
                premiered = client.parseDOM(item, 'FirstAired')[0]
                if premiered == '' or '-00' in premiered:
                    premiered = '0'
                premiered = client.replaceHTMLCodes(premiered)
                premiered = premiered.encode('utf-8')

               # Show future items
                if status == 'Ended':
                    pass
                elif premiered == '0':
                    raise Exception()
                elif int(re.sub('[^0-9]', '', str(premiered))) > int(re.sub('[^0-9]', '', str(self.today_date))):
                    unaired = 'true'
                    if self.showunaired != 'true':
                        raise Exception()

                season = client.parseDOM(item, 'SeasonNumber')[0]
                season = '%01d' % int(season)
                season = season.encode('utf-8')

                episode = client.parseDOM(item, 'EpisodeNumber')[0]
                episode = re.sub('[^0-9]', '', '%01d' % int(episode))
                episode = episode.encode('utf-8')

# ### episode IDS
                episodeIDS = {}
                if control.setting('enable.upnext') == 'true':
                    episodeIDS = trakt.getEpisodeSummary(imdb, season, episode, full=False)
                    episodeIDS = episodeIDS.get('ids', {})
##------------------

                title = client.parseDOM(item, 'EpisodeName')[0]
                if title == '':
                    title = '0'
                title = client.replaceHTMLCodes(title)
                title = title.encode('utf-8')

                try:
                    thumb = client.parseDOM(item, 'filename')[0]
                except:
                    thumb = ''
                if thumb != '':
                    thumb = self.tvdb_image + thumb
                else:
                    thumb = '0'
                thumb = client.replaceHTMLCodes(thumb)
                thumb = thumb.encode('utf-8')

                if thumb != '0':
                    pass
                elif fanart != '0':
                    thumb = fanart.replace(self.tvdb_image, self.tvdb_poster)
                elif poster != '0':
                    thumb = poster

                try:
                    rating = client.parseDOM(item, 'Rating')[0]
                except:
                    rating = ''
                if rating == '':
                    rating = '0'
                rating = client.replaceHTMLCodes(rating)
                rating = rating.encode('utf-8')

                try:
                    director = client.parseDOM(item, 'Director')[0]
                except:
                    director = ''
                director = [x for x in director.split('|') if x != '']
                director = ' / '.join(director)
                if director == '':
                    director = '0'
                director = client.replaceHTMLCodes(director)
                director = director.encode('utf-8')

                try:
                    writer = client.parseDOM(item, 'Writer')[0]
                except:
                    writer = ''
                writer = [x for x in writer.split('|') if x != '']
                writer = ' / '.join(writer)
                if writer == '':
                    writer = '0'
                writer = client.replaceHTMLCodes(writer)
                writer = writer.encode('utf-8')

                try:
                    local = client.parseDOM(item, 'id')[0]
                    local = [x for x in locals if '<id>%s</id>' % str(local) in x][0]
                except:
                    local = item

                label = client.parseDOM(local, 'EpisodeName')[0]
                if label == '':
                    label = '0'
                label = client.replaceHTMLCodes(label)
                label = label.encode('utf-8')

                try:
                    episodeplot = client.parseDOM(local, 'Overview')[0]
                except:
                    episodeplot = ''
                if episodeplot == '':
                    episodeplot = '0'
                if episodeplot == '0':
                    episodeplot = plot
                episodeplot = client.replaceHTMLCodes(episodeplot)
                try:
                    episodeplot = episodeplot.encode('utf-8')
                except:
                    pass

                try:
                    seasoncount = counts[season]
                except:
                    seasoncount = None

                self.list.append({'title': title, 'label': label, 'seasoncount': seasoncount, 'season': season, 'episode': episode, 'tvshowtitle': tvshowtitle, 'year': year,
                                'premiered': premiered, 'status': status, 'studio': studio, 'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes, 'mpaa': mpaa,
                                'director': director, 'writer': writer, 'cast': cast, 'plot': episodeplot, 'imdb': imdb, 'tmdb': tmdb, 'tvdb': tvdb, 'poster': poster, 'banner': banner,
                                'fanart': fanart, 'thumb': thumb, 'unaired': unaired, 'episodeIDS': episodeIDS})
            except:
                pass
        return self.list


    @classmethod
    def seasonCountParse(self, season = None, items = None, seasons = None, episodes = None):
        # Determine the number of episodes per season to estimate season pack episode sizes.
        index = season
        counts = {} # Do not use a list, since not all seasons are labeled by number. Eg: MythBusters
        if episodes is None:
            episodes = [i for i in items if '<EpisodeNumber>' in i]
            if control.setting('tv.specials') == 'true':
                episodes = [i for i in episodes]
            else:
                episodes = [i for i in episodes if not '<SeasonNumber>0</SeasonNumber>' in i]
                episodes = [i for i in episodes if not '<EpisodeNumber>0</EpisodeNumber>' in i]

            seasons = [i for i in episodes if '<EpisodeNumber>1</EpisodeNumber>' in i]

        for s in seasons:
            season = client.parseDOM(s, 'SeasonNumber')[0]
            season = '%01d' % int(season)
            season = season.encode('utf-8')
            counts[season] = 0

        for e in episodes:
            try:
                season = client.parseDOM(e, 'SeasonNumber')[0]
                season = '%01d' % int(season)
                season = season.encode('utf-8')
                counts[season] += 1
            except:
                pass
        try:
            if index is None:
                return counts
            else:
                return counts[index]
        except:
            return None


    def seasonCount(self, tvshowtitle, year, imdb, tvdb, season):
        try:
            return cache.get(self._seasonCount, 168, tvshowtitle, year, imdb, tvdb)[season]
        except:
            return None


    def _seasonCount(self, tvshowtitle, year, imdb, tvdb):
        try:
            if imdb == '0':
                try:
                    imdb = trakt.SearchTVShow(urllib.quote_plus(tvshowtitle), year, full=False)[0]
                    imdb = imdb.get('show', '0')
                    imdb = imdb.get('ids', {}).get('imdb', '0')
                    imdb = 'tt' + re.sub('[^0-9]', '', str(imdb))
                    if not imdb:
                        imdb = '0'
                except:
                    imdb = '0'

            if tvdb == '0' and imdb != '0':
                url = self.tvdb_by_imdb % imdb
                result = client.request(url, timeout='10')

                try:
                    tvdb = client.parseDOM(result, 'seriesid')[0]
                except:
                    tvdb = '0'

                try:
                    name = client.parseDOM(result, 'SeriesName')[0]
                except:
                    name = '0'

                dupe = re.compile('[***]Duplicate (\d*)[***]').findall(name)
                if len(dupe) > 0:
                    tvdb = str(dupe[0])
                if tvdb == '':
                    tvdb = '0'

            if tvdb == '0':
                url = self.tvdb_by_query % (urllib.quote_plus(tvshowtitle))
                years = [str(year), str(int(year)+1), str(int(year)-1)]
                tvdb = client.request(url, timeout='10')
                tvdb = re.sub(r'[^\x00-\x7F]+', '', tvdb)
                tvdb = client.replaceHTMLCodes(tvdb)
                tvdb = client.parseDOM(tvdb, 'Series')
                tvdb = [(x, client.parseDOM(x, 'SeriesName'), client.parseDOM(x, 'FirstAired')) for x in tvdb]
                tvdb = [(x, x[1][0], x[2][0]) for x in tvdb if len(x[1]) > 0 and len(x[2]) > 0]
                tvdb = [x for x in tvdb if cleantitle.get(tvshowtitle) == cleantitle.get(x[1])]
                tvdb = [x[0][0] for x in tvdb if any(y in x[2] for y in years)][0]
                tvdb = client.parseDOM(tvdb, 'seriesid')[0]
                if tvdb == '': tvdb = '0'
        except:
            return None

        try:
            if tvdb == '0': return None

            url = self.tvdb_info_link % (tvdb, 'en')
            data = urllib2.urlopen(url, timeout=30).read()
            zip = zipfile.ZipFile(StringIO.StringIO(data))
            result = zip.read('%s.xml' % 'en')
            zip.close()

            dupe = client.parseDOM(result, 'SeriesName')[0]
            dupe = re.compile('[***]Duplicate (\d*)[***]').findall(dupe)

            if len(dupe) > 0:
                tvdb = str(dupe[0]).encode('utf-8')
                url = self.tvdb_info_link % (tvdb, 'en')
                data = urllib2.urlopen(url, timeout=30).read()
                zip = zipfile.ZipFile(StringIO.StringIO(data))
                result = zip.read('%s.xml' % 'en')
                zip.close()

            result = result.split('<Episode>')
            return self.seasonCountParse(items = result)
        except:
            return None


    def seasonDirectory(self, items):
        if items is None or len(items) == 0:
            control.idle()
            control.notification(title = 32054, message = 33049, icon = 'INFO')
            sys.exit()

        sysaddon = sys.argv[0]
        syshandle = int(sys.argv[1])

        addonPoster, addonBanner = control.addonPoster(), control.addonBanner()
        addonFanart, settingFanart = control.addonFanart(), control.setting('fanart')

        if trakt.getTraktIndicatorsInfo() is True:
            watchedMenu = control.lang(32068).encode('utf-8')
            unwatchedMenu = control.lang(32069).encode('utf-8')
        else:
            watchedMenu = control.lang(32066).encode('utf-8')
            unwatchedMenu = control.lang(32067).encode('utf-8')

        traktManagerMenu = control.lang(32070).encode('utf-8')
        playlistManagerMenu = control.lang(35522).encode('utf-8')
        queueMenu = control.lang(32065).encode('utf-8')
        showPlaylistMenu = control.lang(35517).encode('utf-8')
        clearPlaylistMenu = control.lang(35516).encode('utf-8')
        labelMenu = control.lang(32055).encode('utf-8')
        playRandom = control.lang(32535).encode('utf-8')
        addToLibrary = control.lang(32551).encode('utf-8')

        try:
            multi = [i['tvshowtitle'] for i in items]
        except:
            multi = []
        multi = len([x for y,x in enumerate(multi) if x not in multi[:y]])
        multi = True if multi > 1 else False

        for i in items:
            try:
                imdb, tmdb, tvdb, year, season = i['imdb'], i['tmdb'], i['tvdb'], i['year'], i['season']
                title = i['tvshowtitle']

                label = '%s %s' % (labelMenu, i['season'])

                if self.season_special is False and control.setting('tv.specials') == 'true':
                    self.season_special = True if int(season) == 0 else False

                try:
                    if i['unaired'] == 'true':
                        label = '[COLOR %s][I]%s[/I][/COLOR]' % (self.unairedcolor, label)
                except:
                    pass

                systitle = sysname = urllib.quote_plus(title)

                meta = dict((k,v) for k, v in i.iteritems() if v != '0')
                meta.update({'code': imdb, 'imdbnumber': imdb, 'imdb_id': imdb})
                meta.update({'tmdb_id': tmdb})
                meta.update({'tvdb_id': tvdb})
                meta.update({'mediatype': 'tvshow'})
                meta.update({'trailer': '%s?action=trailer&name=%s' % (sysaddon, sysname)})

                try:
                    plot = meta['plot']
                    index = plot.rfind('See full summary')
                    if index >= 0: plot = plot[:index]
                    plot = plot.strip()
                    if re.match('[a-zA-Z\d]$', plot): plot += ' ...'
                    meta['plot'] = plot
                except: pass

                try:
                    meta.update({'duration': str(int(meta['duration']) * 60)})
                except:
                    pass
                try:
                    meta.update({'genre': cleangenre.lang(meta['genre'], self.lang)})
                except:
                    pass
                try:
                    meta.update({'tvshowtitle': i['label']})
                except:
                    pass

                try:
                    # Year is the shows year, not the seasons year. Extract the correct year frpm the premier date.
                    yearNew = i['premiered']
                    yearNew = re.findall('(\d{4})', yearNew)[0]
                    yearNew = yearNew.encode('utf-8')
                    meta.update({'year': yearNew})
                except:
                    pass

                # First check thumbs, since they typically contains the seasons poster. The normal poster contains the show poster.
                poster = '0'
                if poster == '0' and 'thumb3' in i: poster = i['thumb3']
                if poster == '0' and 'thumb2' in i: poster = i['thumb2']
                if poster == '0' and 'thumb' in i: poster = i['thumb']
                if poster == '0' and 'poster3' in i: poster = i['poster3']
                if poster == '0' and 'poster2' in i: poster = i['poster2']
                if poster == '0' and 'poster' in i: poster = i['poster']

                icon = '0'
                if icon == '0' and 'icon3' in i: icon = i['icon3']
                if icon == '0' and 'icon2' in i: icon = i['icon2']
                if icon == '0' and 'icon' in i: icon = i['icon']

                thumb = '0'
                if thumb == '0' and 'thumb3' in i: thumb = i['thumb3']
                if thumb == '0' and 'thumb2' in i: thumb = i['thumb2']
                if thumb == '0' and 'thumb' in i: thumb = i['thumb']

                banner = '0'
                if banner == '0' and 'banner3' in i: banner = i['banner3']
                if banner == '0' and 'banner2' in i: banner = i['banner2']
                if banner == '0' and 'banner' in i: banner = i['banner']

                fanart = '0'
                if settingFanart:
                    if fanart == '0' and 'fanart3' in i: fanart = i['fanart3']
                    if fanart == '0' and 'fanart2' in i: fanart = i['fanart2']
                    if fanart == '0' and 'fanart' in i: fanart = i['fanart']

                clearlogo = '0'
                if clearlogo == '0' and 'clearlogo' in i: clearlogo = i['clearlogo']

                clearart = '0'
                if clearart == '0' and 'clearart' in i: clearart = i['clearart']

                if poster == '0': poster = addonPoster
                if icon == '0': icon = poster
                if thumb == '0': thumb = poster
                if banner == '0': banner = addonBanner
                if fanart == '0': fanart = addonFanart

                art = {}
                if poster != '0' and poster is not None:
                    art.update({'poster': poster, 'tvshow.poster': poster, 'season.poster': poster})
                if fanart != '0' and fanart is not None:
                    art.update({'fanart': fanart})
                if icon != '0' and icon is not None:
                    art.update({'icon': icon})
                if thumb != '0' and thumb is not None:
                    art.update({'thumb': thumb})
                if banner != '0' and banner is not None:
                    art.update({'banner': banner})
                if clearlogo != '0' and clearlogo is not None:
                    art.update({'clearlogo': clearlogo})
                if clearart != '0' and clearart is not None:
                    art.update({'clearart': clearart})

####-Context Menu and Overlays-####
                cm = []
                if self.traktCredentials is True:
                    cm.append((traktManagerMenu, 'RunPlugin(%s?action=traktManager&name=%s&imdb=%s&tvdb=%s&season=%s)' % (sysaddon, sysname, imdb, tvdb, season)))

                try:
                    indicators = playcount.getSeasonIndicators(imdb)
                    overlay = int(playcount.getSeasonOverlay(indicators, imdb, tvdb, season))
                    watched = overlay == 7
                    if watched:
                        meta.update({'playcount': 1, 'overlay': 7})
                        cm.append((unwatchedMenu, 'RunPlugin(%s?action=tvPlaycount&name=%s&imdb=%s&tvdb=%s&season=%s&query=6)' % (sysaddon, systitle, imdb, tvdb, season)))
                    else: 
                        meta.update({'playcount': 0, 'overlay': 6})
                        cm.append((watchedMenu, 'RunPlugin(%s?action=tvPlaycount&name=%s&imdb=%s&tvdb=%s&season=%s&query=7)' % (sysaddon, systitle, imdb, tvdb, season)))
                except:
                    pass

                sysmeta = urllib.quote_plus(json.dumps(meta))
                sysart = urllib.quote_plus(json.dumps(art))
                url = '%s?action=episodes&tvshowtitle=%s&year=%s&imdb=%s&tvdb=%s&season=%s' % (sysaddon, systitle, year, imdb, tvdb, season)
                sysurl = urllib.quote_plus(url)

                cm.append((playRandom, 'RunPlugin(%s?action=random&rtype=episode&tvshowtitle=%s&year=%s&imdb=%s&tvdb=%s&season=%s)' % (
                                    sysaddon, urllib.quote_plus(systitle), urllib.quote_plus(year), urllib.quote_plus(imdb), urllib.quote_plus(tvdb), urllib.quote_plus(season))))
                # cm.append((playlistManagerMenu, 'RunPlugin(%s?action=playlistManager&name=%s&url=%s&meta=%s&art=%s)' % (sysaddon, systitle, sysurl, sysmeta, sysart)))
                cm.append((queueMenu, 'RunPlugin(%s?action=queueItem&name=%s)' % (sysaddon, systitle)))
                cm.append((showPlaylistMenu, 'RunPlugin(%s?action=showPlaylist)' % sysaddon))
                cm.append((clearPlaylistMenu, 'RunPlugin(%s?action=clearPlaylist)' % sysaddon))

                cm.append((addToLibrary, 'RunPlugin(%s?action=tvshowToLibrary&tvshowtitle=%s&year=%s&imdb=%s&tvdb=%s)' % (sysaddon, systitle, year, imdb, tvdb)))
                cm.append(('[COLOR red]Venom Settings[/COLOR]', 'RunPlugin(%s?action=openSettings&query=0.0)' % sysaddon))
####################################

                item = control.item(label = label)

                unwatchedEnabled = control.setting('tvshows.unwatched.enabled')
                unwatchedLimit = False
                seasoncountEnabled = control.setting('tvshows.seasoncount.enabled')

                if unwatchedEnabled == 'true':
                    count = playcount.getSeasonCount(imdb, season, self.season_special, unwatchedLimit)
                    if count:
                        item.setProperty('TotalEpisodes', str(count['total']))
                        item.setProperty('WatchedEpisodes', str(count['watched']))
                        item.setProperty('UnWatchedEpisodes', str(count['unwatched']))

                if seasoncountEnabled == 'true' and self.traktCredentials is True:
                    total_seasons = trakt.getSeasons(imdb, full=False)
                    if total_seasons is not None:
                        total_seasons = [i['number'] for i in total_seasons]
                        total_seasons = len(total_seasons)
                        # if control.setting('tv.specials') == 'false' or self.season_special is False:
                            # total_seasons = total_seasons - 1
                        item.setProperty('TotalSeasons', str(total_seasons))

                if 'episodeIDS' in i:
                    item.setUniqueIDs(i['episodeIDS'])
                if 'cast' in i:
                    item.setCast(i['cast'])

                # if fanart != '0' and fanart is not None:
                    # item.setProperty('Fanart_Image', fanart)

                item.setArt(art)
                item.setInfo(type='video', infoLabels=control.metadataClean(meta))
                item.addContextMenuItems(cm)
                video_streaminfo = {'codec': 'h264'}
                item.addStreamInfo('video', video_streaminfo)
                control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)
            except:
                pass

        try:
            control.property(syshandle, 'showplot', items[0]['plot'])
        except:
            pass

        control.content(syshandle, 'seasons')
        control.directory(syshandle, cacheToDisc=True)
        views.setView('seasons', {'skin.estuary': 55, 'skin.confluence': 500})