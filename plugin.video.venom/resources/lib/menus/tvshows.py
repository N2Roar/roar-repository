# -*- coding: utf-8 -*-

'''
	Venom Add-on
'''

import os, sys, re, json
import urllib, urlparse
import datetime

from resources.lib.modules import trakt
from resources.lib.modules import cleangenre
from resources.lib.modules import control
from resources.lib.modules import client
from resources.lib.modules import cache
from resources.lib.modules import metacache
from resources.lib.modules import playcount
from resources.lib.modules import workers
from resources.lib.modules import views
from resources.lib.menus import navigator

params = dict(urlparse.parse_qsl(sys.argv[2].replace('?',''))) if len(sys.argv) > 1 else dict()
action = params.get('action')


class TVshows:
	def __init__(self, type = 'show', notifications = True):
		self.count = int(control.setting('page.item.limit'))
		# if type(self.count) is not int:
			# self.count = 40
		self.list = []
		self.meta = []
		self.threads = []
		self.type = type
		self.lang = control.apiLanguage()['tvdb']
		self.season_special = False
		self.notifications = notifications

		self.datetime = (datetime.datetime.utcnow() - datetime.timedelta(hours = 5))

		# self.tvdb_key = control.setting('tvdb.user')
		# if self.tvdb_key == '' or self.tvdb_key is None:
			# self.tvdb_key = '1D62F2F90030C444'
		self.tvdb_key = 'MUQ2MkYyRjkwMDMwQzQ0NA=='

		self.imdb_user = control.setting('imdb.user').replace('ur', '')

		self.user = str(self.imdb_user) + str(self.tvdb_key)

		self.disable_fanarttv = control.setting('disable.fanarttv')

		self.tvdb_info_link = 'http://thetvdb.com/api/%s/series/%s/%s.xml' % (self.tvdb_key.decode('base64'), '%s', '%s')
		self.tvdb_by_imdb = 'http://thetvdb.com/api/GetSeriesByRemoteID.php?imdbid=%s'
		self.tvdb_by_query = 'http://thetvdb.com/api/GetSeries.php?seriesname=%s'
		self.tvdb_image = 'http://thetvdb.com/banners/'

		self.imdb_link = 'http://www.imdb.com'
		self.persons_link = 'http://www.imdb.com/search/name?count=100&name='
		self.personlist_link = 'http://www.imdb.com/search/name?count=100&gender=male,female'
		self.popular_link = 'http://www.imdb.com/search/title?title_type=tv_series,mini_series&num_votes=100,&release_date=,date[0]&sort=moviemeter,asc&count=%d&start=1' % self.count
		self.airing_link = 'http://www.imdb.com/search/title?title_type=tv_episode&release_date=date[1],date[0]&sort=moviemeter,asc&count=%d&start=1' % self.count
		self.active_link = 'http://www.imdb.com/search/title?title_type=tv_series,mini_series&num_votes=10,&production_status=active&sort=moviemeter,asc&count=%d&start=1' % self.count
		self.premiere_link = 'http://www.imdb.com/search/title?title_type=tv_series,mini_series&languages=en&num_votes=10,&release_date=date[60],date[0]&sort=release_date,desc&count=%d&start=1' % self.count
		self.rating_link = 'http://www.imdb.com/search/title?title_type=tv_series,mini_series&num_votes=5000,&release_date=,date[0]&sort=user_rating,desc&count=%d&start=1' % self.count
		self.views_link = 'http://www.imdb.com/search/title?title_type=tv_series,mini_series&num_votes=100,&release_date=,date[0]&sort=num_votes,desc&count=%d&start=1' % self.count
		self.person_link = 'http://www.imdb.com/search/title?title_type=tv_series,mini_series&release_date=,date[0]&role=%s&sort=year,desc&count=%d&start=1' % ('%s', self.count)
		self.genre_link = 'http://www.imdb.com/search/title?title_type=tv_series,mini_series&release_date=,date[0]&genres=%s&sort=moviemeter,asc&count=%d&start=1' % ('%s', self.count)
		self.keyword_link = 'http://www.imdb.com/search/title?title_type=tv_series,mini_series&release_date=,date[0]&keywords=%s&sort=moviemeter,asc&count=%d&start=1' % ('%s', self.count)
		self.language_link = 'http://www.imdb.com/search/title?title_type=tv_series,mini_series&num_votes=100,&production_status=released&primary_language=%s&sort=moviemeter,asc&count=%d&start=1' % ('%s', self.count)
		self.certification_link = 'http://www.imdb.com/search/title?title_type=tv_series,mini_series&release_date=,date[0]&certificates=%s&sort=moviemeter,asc&count=%d&start=1' % ('%s', self.count)

		self.imdblists_link = 'http://www.imdb.com/user/ur%s/lists?tab=all&sort=mdfd&order=desc&filter=titles' % self.imdb_user
		self.imdblist_link = 'http://www.imdb.com/list/%s/?view=detail&sort=alpha,asc&title_type=tvSeries,tvMiniSeries&start=1'
		self.imdblist2_link = 'http://www.imdb.com/list/%s/?view=detail&sort=date_added,desc&title_type=tvSeries,tvMiniSeries&start=1'
		self.imdbwatchlist_link = 'http://www.imdb.com/user/ur%s/watchlist?sort=alpha,asc' % self.imdb_user
		self.imdbwatchlist2_link = 'http://www.imdb.com/user/ur%s/watchlist?sort=date_added,desc' % self.imdb_user

		self.anime_link = 'https://www.imdb.com/search/keyword?keywords=anime&title_type=tvSeries,miniSeries&sort=moviemeter,asc&count=%d&start=1' % self.count

		self.trakt_user = control.setting('trakt.user').strip()
		self.traktCredentials = trakt.getTraktCredentialsInfo()
		self.trakt_link = 'http://api.trakt.tv'
		self.search_link = 'http://api.trakt.tv/search/show?limit=%d&page=1&query=' % self.count

		self.traktlists_link = 'http://api.trakt.tv/users/me/lists'
		self.traktlikedlists_link = 'http://api.trakt.tv/users/likes/lists?limit=1000000'
		self.traktlist_link = 'http://api.trakt.tv/users/%s/lists/%s/items/shows?page=1&limit=%d' % ('%s', '%s', self.count)
		self.traktwatchlist_link = 'http://api.trakt.tv/users/me/watchlist/shows?page=1&limit=%d' % self.count
		self.traktcollection_link = 'http://api.trakt.tv/users/me/collection/shows'
		self.trakttrending_link = 'http://api.trakt.tv/shows/trending?page=1&limit=%d' % self.count
		self.traktpopular_link = 'http://api.trakt.tv/shows/popular?page=1&limit=%d' % self.count
		self.traktrecommendations_link = 'http://api.trakt.tv/recommendations/shows?page=1&limit=%d' % self.count

		self.tvmaze_link = 'http://www.tvmaze.com'

		self.tmdb_key = control.setting('tm.user')
		if self.tmdb_key == '' or self.tmdb_key is None:
			self.tmdb_key = '3320855e65a9758297fec4f7c9717698'

		self.tmdb_link = 'http://api.themoviedb.org'
		self.tmdb_lang = 'en-US'
		self.tmdb_popular_link = 'http://api.themoviedb.org/3/tv/popular?api_key=%s&language=en-US&region=US&page=1'
		self.tmdb_toprated_link = 'http://api.themoviedb.org/3/tv/top_rated?api_key=%s&language=en-US&region=US&page=1'
		self.tmdb_ontheair_link = 'http://api.themoviedb.org/3/tv/on_the_air?api_key=%s&language=en-US&region=US&page=1'
		self.tmdb_airingtoday_link = 'http://api.themoviedb.org/3/tv/airing_today?api_key=%s&language=en-US&region=US&page=1'


	def get(self, url, idx=True):
		try:
			try:
				url = getattr(self, url + '_link')
			except:
				pass

			try:
				u = urlparse.urlparse(url).netloc.lower()
			except:
				pass

			if u in self.trakt_link and '/users/' in url:
				# urls = []
				# # Must only check if no type is specified at the end of the link, since this function can be called for specific show, season, and episode lists.
				# if url.endswith('/watchlist/'):
					# urls.append(url + 'shows')
					# urls.append(url + 'seasons')
					# urls.append(url + 'episodes')
				# else:
					# urls.append(url)

				# lists = []
				# for u in urls:
					# self.list = []
					# result = cache.get(self.trakt_list, 0.3, u, self.trakt_user)
					# if result: lists += result
				# self.list = lists

				# lists = []
				# for u in urls:
					# self.list = []
					# try:
						# if '/users/me/' not in url:
							# raise Exception()
						# if trakt.getActivity() > cache.timeout(self.trakt_list, u, self.trakt_user):
							# raise Exception()
						# result = cache.get(self.trakt_list, 720, u, self.trakt_user)
						# if result: lists += result
					# except:
						# result = cache.get(self.trakt_list, 0, u, self.trakt_user)
						# if result: lists += result
				# self.list = lists
				try:
					if not '/users/me/' in url: raise Exception()
					if trakt.getActivity() > cache.timeout(self.trakt_list, url, self.trakt_user): raise Exception()
					self.list = cache.get(self.trakt_list, 720, url, self.trakt_user)
				except:
					self.list = cache.get(self.trakt_list, 0, url, self.trakt_user)

				self.sort()
				if idx is True:
					self.worker()

			elif u in self.trakt_link and self.search_link in url:
				self.list = cache.get(self.trakt_list, 1, url, self.trakt_user)
				if idx is True:
					self.worker(level = 0)

			elif u in self.trakt_link:
				self.list = cache.get(self.trakt_list, 24, url, self.trakt_user)
				if idx is True:
					self.worker()

			elif u in self.imdb_link and ('/user/' in url or '/list/' in url):
				self.list = cache.get(self.imdb_list, 1, url)
				self.sort()
				if idx is True:
					self.worker()

			elif u in self.imdb_link:
				self.list = cache.get(self.imdb_list, 168, url)
				if idx is True:
					self.worker()

			if self.list is None:
				self.list = []

			if len(self.list) == 0 and self.search_link in url:
				control.hide()
				if self.notifications:
					control.notification(title=32010, message=33049, icon='INFO')

			if idx is True:
				self.tvshowDirectory(self.list)
			return self.list
		except:
			try:
				invalid = (self.list is None or len(self.list) == 0)
			except:
				invalid = True
			if invalid:
				control.hide()
				if self.notifications:
					control.notification(title=32002, message=33049, icon='INFO')


	def getTMDb(self, url, idx=True):
		try:
			try:
				url = getattr(self, url + '_link')
			except:
				pass

			try:
				u = urlparse.urlparse(url).netloc.lower()
			except:
				pass

			if u in self.tmdb_link and ('/user/' in url or '/list/' in url):
				from resources.lib.indexers import tmdb
				self.list = cache.get(tmdb.TVshows().tmdb_collections_list, 24, url)

			elif u in self.tmdb_link and not ('/user/' in url or '/list/' in url):
				from resources.lib.indexers import tmdb
				self.list = cache.get(tmdb.TVshows().tmdb_list, 168, url)

			if self.list is None:
				self.list = []
				raise Exception()
			if idx is True:
				self.tvshowDirectory(self.list)
			return self.list
		except:
			try:
				invalid = (self.list is None or len(self.list) == 0)
			except:
				invalid = True
			if invalid:
				control.idle()
				if self.notifications:
					control.notification(title = 32002, message = 33049, icon = 'INFO')


	def getTVmaze(self, url, idx=True):
		from resources.lib.indexers import tvmaze
		try:
			try:
				url = getattr(self, url + '_link')
			except:
				pass

			self.list = cache.get(tvmaze.tvshows().tvmaze_list, 168, url)

			if self.list is None:
				self.list = []
				raise Exception()
			if idx is True:
				self.tvshowDirectory(self.list)
			return self.list
		except:
			try:
				invalid = (self.list is None or len(self.list) == 0)
			except:
				invalid = True
			if invalid:
				control.idle()
				if self.notifications:
					control.notification(title = 32002, message = 33049, icon = 'INFO')


	def sort(self):
		try:
			if self.list is None or self.list == []:
				return
			attribute = int(control.setting('sort.shows.type'))
			reverse = int(control.setting('sort.shows.order')) == 1
			if attribute == 0:
				reverse = False
			if attribute > 0:
				if attribute == 1:
					try:
						# self.list = sorted(self.list, key = lambda k: k['tvshowtitle'].lower(), reverse = reverse)
						self.list = sorted(self.list, key=lambda k: re.sub('(^the |^a |^an )', '', k['tvshowtitle'].lower()), reverse=reverse)
					except:
						self.list = sorted(self.list, key = lambda k: k['title'].lower(), reverse = reverse)
				elif attribute == 2:
					self.list = sorted(self.list, key = lambda k: float(k['rating']), reverse = reverse)
				elif attribute == 3:
					self.list = sorted(self.list, key = lambda k: int(k['votes'].replace(',', '')), reverse = reverse)
				elif attribute == 4:
					for i in range(len(self.list)):
						if 'premiered' not in self.list[i]:
							self.list[i]['premiered'] = ''
					self.list = sorted(self.list, key = lambda k: k['premiered'], reverse = reverse)
				elif attribute == 5:
					for i in range(len(self.list)):
						if 'added' not in self.list[i]:
							self.list[i]['added'] = ''
					self.list = sorted(self.list, key = lambda k: k['added'], reverse = reverse)
				elif attribute == 6:
					for i in range(len(self.list)):
						if 'lastplayed' not in self.list[i]:
							self.list[i]['lastplayed'] = ''
					self.list = sorted(self.list, key = lambda k: k['lastplayed'], reverse = reverse)
			elif reverse:
				self.list = reversed(self.list)
		except:
			import traceback
			traceback.print_exc()
			pass


	def search(self):
		navigator.Navigator().addDirectoryItem(32603, 'tvSearchnew', 'search.png', 'DefaultAddonsSearch.png')

		try:
			from sqlite3 import dbapi2 as database
		except:
			from pysqlite2 import dbapi2 as database

		dbcon = database.connect(control.searchFile)
		dbcur = dbcon.cursor()

		try:
			dbcur.executescript("CREATE TABLE IF NOT EXISTS tvshow (ID Integer PRIMARY KEY AUTOINCREMENT, term);")
			dbcur.connection.commit()
		except:
			import traceback
			traceback.print_exc()
			pass

		dbcur.execute("SELECT * FROM tvshow ORDER BY ID DESC")
		lst = []
		delete_option = False

		for (id, term) in dbcur.fetchall():
			if term not in str(lst):
				delete_option = True
				navigator.Navigator().addDirectoryItem(term, 'tvSearchterm&name=%s' % term, 'search.png', 'DefaultAddonsSearch.png')
				lst += [(term)]

		dbcon.close()

		if delete_option:
			navigator.Navigator().addDirectoryItem(32605, 'clearCacheSearch', 'tools.png', 'DefaultAddonService.png', isFolder=False)
		navigator.Navigator().endDirectory()


	def search_new(self):
		t = control.lang(32010).encode('utf-8')
		k = control.keyboard('', t)
		k.doModal()
		q = k.getText() if k.isConfirmed() else None

		if (q is None or q == ''):
			return
			# return sys.exit()

		try:
			from sqlite3 import dbapi2 as database
		except:
			from pysqlite2 import dbapi2 as database

		dbcon = database.connect(control.searchFile)
		dbcur = dbcon.cursor()
		dbcur.execute("INSERT INTO tvshow VALUES (?,?)", (None, q))
		dbcur.connection.commit()
		dbcon.close()
		url = self.search_link + urllib.quote_plus(q)
		self.get(url)


	def search_term(self, name):
		url = self.search_link + urllib.quote_plus(name)
		self.get(url)


	def person(self):
		t = control.lang(32010).encode('utf-8')
		k = control.keyboard('', t)
		k.doModal()
		q = k.getText().strip() if k.isConfirmed() else None
		if not q:
			return
		url = self.persons_link + urllib.quote_plus(q)
		self.persons(url)


	def genres(self):
		genres = [
			('Action', 'action', True), ('Adventure', 'adventure', True), ('Animation', 'animation', True),
			('Anime', 'anime', False), ('Biography', 'biography', True), ('Comedy', 'comedy', True),
			('Crime', 'crime', True), ('Drama', 'drama', True), ('Family', 'family', True),
			('Fantasy', 'fantasy', True), ('Game-Show', 'game_show', True),
			('History', 'history', True), ('Horror', 'horror', True), ('Music ', 'music', True),
			('Musical', 'musical', True), ('Mystery', 'mystery', True), ('News', 'news', True),
			('Reality-TV', 'reality_tv', True), ('Romance', 'romance', True), ('Science Fiction', 'sci_fi', True),
			('Sport', 'sport', True), ('Talk-Show', 'talk_show', True), ('Thriller', 'thriller', True),
			('War', 'war', True), ('Western', 'western', True)
		]
		for i in genres:
			self.list.append({'name': cleangenre.lang(i[0], self.lang), 'url': self.genre_link % i[1] if i[2] else self.keyword_link % i[1], 'image': 'genres.png', 'icon': 'DefaultGenre.png', 'action': 'tvshows'})
		self.addDirectory(self.list)
		return self.list


	def networks(self):
		if control.setting('tvshows.networks.view') == '0':
			from resources.lib.indexers.tvmaze import networks_this_season as networks

		if control.setting('tvshows.networks.view') == '1':
			from resources.lib.indexers.tvmaze import networks_view_all as networks

		networks = sorted(networks, key=lambda x: x[0])

		for i in networks:
			self.list.append({'name': i[0], 'url': self.tvmaze_link + i[1], 'image': i[2], 'icon': 'DefaultNetwork.png', 'action': 'tvmazeTvshows'})
		self.addDirectory(self.list)
		return self.list


	def originals(self):
		if control.setting('tvshows.networks.view') == '0':
			from resources.lib.indexers.tvmaze import originals_this_season as originals

		if control.setting('tvshows.networks.view') == '1':
			from resources.lib.indexers.tvmaze import originals_view_all as originals

		originals = sorted(originals, key=lambda x: x[0])

		for i in originals:
			self.list.append({'name': i[0], 'url': self.tvmaze_link + i[1], 'image': i[2], 'icon': 'DefaultNetwork.png', 'action': 'tvmazeTvshows'})
		self.addDirectory(self.list)
		return self.list


	def languages(self):
		languages = [('Arabic', 'ar'), ('Bosnian', 'bs'), ('Bulgarian', 'bg'), ('Chinese', 'zh'), ('Croatian', 'hr'), ('Dutch', 'nl'),
			('English', 'en'), ('Finnish', 'fi'), ('French', 'fr'), ('German', 'de'), ('Greek', 'el'), ('Hebrew', 'he'), ('Hindi ', 'hi'),
			('Hungarian', 'hu'), ('Icelandic', 'is'), ('Italian', 'it'), ('Japanese', 'ja'), ('Korean', 'ko'), ('Norwegian', 'no'),
			('Persian', 'fa'), ('Polish', 'pl'), ('Portuguese', 'pt'), ('Punjabi', 'pa'), ('Romanian', 'ro'), ('Russian', 'ru'),
			('Serbian', 'sr'), ('Spanish', 'es'), ('Swedish', 'sv'), ('Turkish', 'tr'), ('Ukrainian', 'uk')]
		for i in languages:
			self.list.append({'name': str(i[0]), 'url': self.language_link % i[1], 'image': 'languages.png', 'icon': 'DefaultAddonLanguage.png', 'action': 'tvshows'})
		self.addDirectory(self.list)
		return self.list


	def certifications(self):
		certificates = [
			('Child Audience (Y)', 'TV-Y'),
			('Young Audience (Y7)', 'TV-Y7'),
			('Parental Guidance (PG)', 'TV-PG'),
			('Youth Audience (14)', 'TV-13', 'TV-14'),
			('Mature Audience (MA)', 'TV-MA')
		]
		for i in certificates:
			self.list.append({'name': str(i[0]), 'url': self.certification_link % self.certificatesFormat(i[1]), 'image': 'certificates.png', 'icon': 'DefaultTVShows.png', 'action': 'tvshows'})
		self.addDirectory(self.list)
		return self.list


	def certificatesFormat(self, certificates):
		base = 'US%3A'
		if not isinstance(certificates, (tuple, list)):
			certificates = [certificates]
		return ','.join([base + i.upper() for i in certificates])


	def persons(self, url):
		if url is None:
			self.list = cache.get(self.imdb_person_list, 24, self.personlist_link)
		else:
			self.list = cache.get(self.imdb_person_list, 1, url)

		if len(self.list) == 0:
			control.hide()
			control.notification(title = 32010, message = 33049, icon = 'INFO')

		for i in range(0, len(self.list)):
			self.list[i].update({'icon': 'DefaultActor.png', 'action': 'tvshows'})
		self.addDirectory(self.list)
		return self.list


	def userlists(self):
		userlists = []
		try:
			if self.traktCredentials is False:
				raise Exception()
			activity = trakt.getActivity()

			self.list = []
			lists = []

			try:
				if activity > cache.timeout(self.trakt_user_list, self.traktlists_link, self.trakt_user):
					raise Exception()
				lists += cache.get(self.trakt_user_list, 3, self.traktlists_link, self.trakt_user)
			except:
				lists += cache.get(self.trakt_user_list, 0, self.traktlists_link, self.trakt_user)

			for i in range(len(lists)):
				lists[i].update({'image': 'trakt.png', 'icon': 'DefaultVideoPlaylists.png'})
			userlists += lists
		except:
			pass

		try:
			if self.imdb_user == '':
				raise Exception()
			self.list = []
			lists = cache.get(self.imdb_user_list, 0, self.imdblists_link)
			for i in range(len(lists)):
				lists[i].update({'image': 'imdb.png', 'icon': 'DefaultVideoPlaylists.png'})
			userlists += lists
		except:
			pass

		try:
			if self.traktCredentials is False:
				raise Exception()
			self.list = []
			lists = []

			try:
				if activity > cache.timeout(self.trakt_user_list, self.traktlikedlists_link, self.trakt_user):
					raise Exception()
				lists += cache.get(self.trakt_user_list, 3, self.traktlikedlists_link, self.trakt_user)
			except:
				lists += cache.get(self.trakt_user_list, 0, self.traktlikedlists_link, self.trakt_user)

			for i in range(len(lists)):
				lists[i].update({'image': 'trakt.png', 'icon': 'DefaultVideoPlaylists.png'})
			userlists += lists
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

		for i in range(len(self.list)):
			self.list[i].update({'action': 'tvshows'})

		# imdb Watchlist
		if self.imdb_user != '':
			imdb_watchlist = self.imdbwatchlist2_link
			self.list.insert(0, {'name': control.lang(32033).encode('utf-8'), 'url': imdb_watchlist, 'image': 'imdb.png', 'icon': 'DefaultVideoPlaylists.png', 'action': 'tvshows'})

		# Trakt Watchlist
		if self.traktCredentials is True:
			# trakt_watchlist = self.traktwatchlist_link + 'shows'
			trakt_watchlist = self.traktwatchlist_link
			self.list.insert(0, {'name': control.lang(32033).encode('utf-8'), 'url': trakt_watchlist, 'image': 'trakt.png', 'icon': 'DefaultVideoPlaylists.png', 'action': 'tvshows'})

		self.addDirectory(self.list)
		return self.list


	def trakt_list(self, url, user):
		list = []
		try:
			dupes = []

			q = dict(urlparse.parse_qsl(urlparse.urlsplit(url).query))
			q.update({'extended': 'full'})
			q = (urllib.urlencode(q)).replace('%2C', ',')
			u = url.replace('?' + urlparse.urlparse(url).query, '') + '?' + q

			result = trakt.getTraktAsJson(u)

			items = []
			for i in result:
				try:
					items.append(i['show'])
				except:
					pass
			if len(items) == 0:
				items = result
		except:
			return

		try:
			q = dict(urlparse.parse_qsl(urlparse.urlsplit(url).query))
			if int(q['limit']) != len(items):
				raise Exception()
			q.update({'page': str(int(q['page']) + 1)})
			q = (urllib.urlencode(q)).replace('%2C', ',')
			next = url.replace('?' + urlparse.urlparse(url).query, '') + '?' + q
		except:
			next = ''

		for item in items:
			try:
				try:
					title = item['title'].encode('utf-8')
				except:
					title = item['title']

				year = str(item.get('year'))

				imdb = item.get('ids', {}).get('imdb', '0')
				if imdb == '' or imdb is None or imdb == 'None':
					imdb = '0'

				tmdb = str(item.get('ids', {}).get('tmdb', 0))
				if tmdb == '' or tmdb is None or tmdb == 'None':
					tmdb = '0'

				tvdb = str(item.get('ids', {}).get('tvdb', 0))
				if tvdb == '' or tvdb is None or tvdb == 'None':
					tvdb = '0'

				if tvdb is None or tvdb == '' or tvdb in dupes:
					raise Exception()
				dupes.append(tvdb)

				premiered = item.get('first_aired', '0')

				studio = item.get('network', '0')

				try: genre = item['genres']
				except: genre = '0'
				genre = [i.title() for i in genre]
				if genre == []: genre = '0'
				genre = ' / '.join(genre)

				duration = str(item.get('runtime'))

				rating = str(item.get('rating', '0'))
				votes = str(format(int(item.get('votes', '0')),',d'))

				mpaa = item.get('certification', '0')

				plot = item.get('overview')

				list.append({'title': title, 'originaltitle': title, 'year': year, 'premiered': premiered, 'studio': studio, 'genre': genre, 'duration': duration, 'rating': rating,
											'votes': votes, 'mpaa': mpaa, 'plot': plot, 'imdb': imdb, 'tmdb': tmdb, 'tvdb': tvdb, 'poster': '0', 'fanart': '0', 'next': next})
			except:
				import traceback
				traceback.print_exc()
				pass

		return list


	def trakt_user_list(self, url, user):
		list = []
		try:
			result = trakt.getTrakt(url)
			items = json.loads(result)
		except:
			pass

		for item in items:
			try:
				try:
					name = item['list']['name']
				except:
					name = item['name']
				name = client.replaceHTMLCodes(name)
				name = name.encode('utf-8')

				try:
					url = (trakt.slug(item['list']['user']['username']), item['list']['ids']['slug'])
				except:
					url = ('me', item['ids']['slug'])

				url = self.traktlist_link % url
				url = url.encode('utf-8')

				list.append({'name': name, 'url': url, 'context': url})
			except:
				pass

		list = sorted(list, key=lambda k: re.sub('(^the |^a |^an )', '', k['name'].lower()))
		return list


	def imdb_list(self, url):
		list = []
		items = []
		dupes = []

		try:
			for i in re.findall('date\[(\d+)\]', url):
				url = url.replace('date[%s]' % i, (self.datetime - datetime.timedelta(days = int(i))).strftime('%Y-%m-%d'))

			def imdb_watchlist_id(url):
				return client.parseDOM(client.request(url).decode('iso-8859-1').encode('utf-8'), 'meta', ret='content', attrs = {'property': 'pageId'})[0]

			if url == self.imdbwatchlist_link:
				url = cache.get(imdb_watchlist_id, 8640, url)
				url = self.imdblist_link % url
			elif url == self.imdbwatchlist2_link:
				url = cache.get(imdb_watchlist_id, 8640, url)
				url = self.imdblist2_link % url

			result = client.request(url)
			result = result.replace('\n', ' ')
			result = result.decode('iso-8859-1').encode('utf-8')

			items = client.parseDOM(result, 'div', attrs = {'class': '.+? lister-item'}) + client.parseDOM(result, 'div', attrs = {'class': 'lister-item .+?'})
			items += client.parseDOM(result, 'div', attrs = {'class': 'list_item.+?'})
		except:
			return

		try:
			# HTML syntax error, " directly followed by attribute name. Insert space in between. parseDOM can otherwise not handle it.
			result = result.replace('"class="lister-page-next', '" class="lister-page-next')

			next = client.parseDOM(result, 'a', ret='href', attrs = {'class': 'lister-page-next.+?'})

			if len(next) == 0:
				next = client.parseDOM(result, 'div', attrs = {'class': 'pagination'})[0]
				next = zip(client.parseDOM(next, 'a', ret='href'), client.parseDOM(next, 'a'))
				next = [i[0] for i in next if 'Next' in i[1]]

			next = url.replace(urlparse.urlparse(url).query, urlparse.urlparse(next[0]).query)
			next = client.replaceHTMLCodes(next)
			next = next.encode('utf-8')
		except:
			next = ''

		for item in items:
			try:
				title = client.parseDOM(item, 'a')[1]
				title = client.replaceHTMLCodes(title)
				title = title.encode('utf-8')

				year = client.parseDOM(item, 'span', attrs = {'class': 'lister-item-year.+?'})
				year += client.parseDOM(item, 'span', attrs = {'class': 'year_type'})
				year = re.findall('(\d{4})', year[0])[0]
				year = year.encode('utf-8')

				# if int(year) > int((self.datetime).strftime('%Y')): raise Exception()

				imdb = client.parseDOM(item, 'a', ret='href')[0]
				imdb = re.findall('(tt\d*)', imdb)[0]
				imdb = imdb.encode('utf-8')

				if imdb in dupes: raise Exception()
				dupes.append(imdb)

				# parseDOM cannot handle elements without a closing tag.
				# try: poster = client.parseDOM(item, 'img', ret='loadlate')[0]
				# except: poster = '0'
				try:
					from bs4 import BeautifulSoup
					html = BeautifulSoup(item, "html.parser")
					poster = html.find_all('img')[0]['loadlate']
				except:
					poster = '0'

				if '/nopicture/' in poster: poster = '0'
				poster = re.sub('(?:_SX|_SY|_UX|_UY|_CR|_AL)(?:\d+|_).+?\.', '_SX500.', poster)
				poster = client.replaceHTMLCodes(poster)
				poster = poster.encode('utf-8')

				try: genre = client.parseDOM(item, 'span', attrs = {'class': 'genre'})[0]
				except: genre = '0'
				genre = ' / '.join([i.strip() for i in genre.split(',')])
				if genre == '': genre = '0'
				genre = client.replaceHTMLCodes(genre)
				genre = genre.encode('utf-8')

				try: duration = re.findall('(\d+?) min(?:s|)', item)[-1]
				except: duration = '0'
				duration = duration.encode('utf-8')

				rating = '0'
				try: rating = client.parseDOM(item, 'span', attrs = {'class': 'rating-rating'})[0]
				except:
					try: rating = client.parseDOM(rating, 'span', attrs = {'class': 'value'})[0]
					except:
						try: rating = client.parseDOM(item, 'div', ret='data-value', attrs = {'class': '.*?imdb-rating'})[0]
						except: pass
				if rating == '' or rating == '-': rating = '0'
				rating = client.replaceHTMLCodes(rating)
				rating = rating.encode('utf-8')

				votes = '0'
				try:
					votes = client.parseDOM(item, 'span', attrs = {'name': 'nv'})[0]
				except:
					try:
						votes = client.parseDOM(item, 'div', ret='title', attrs = {'class': '.*?rating-list'})[0]
					except:
						try:
							votes = re.findall('\((.+?) vote(?:s|)\)', votes)[0]
						except:
							pass
				if votes == '':
					votes = '0'
				votes = client.replaceHTMLCodes(votes)
				votes = votes.encode('utf-8')

				try:
					mpaa = client.parseDOM(item, 'span', attrs = {'class': 'certificate'})[0]
				except:
					mpaa = '0'
				if mpaa == '' or mpaa == 'NOT_RATED':
					mpaa = '0'
				mpaa = mpaa.replace('_', '-')
				mpaa = client.replaceHTMLCodes(mpaa)
				mpaa = mpaa.encode('utf-8')

				try:
					director = re.findall('Director(?:s|):(.+?)(?:\||</div>)', item)[0]
				except:
					director = '0'
				director = client.parseDOM(director, 'a')
				director = ' / '.join(director)
				if director == '':
					director = '0'
				director = client.replaceHTMLCodes(director)
				director = director.encode('utf-8')

				# try:
					# cast = re.findall('Stars(?:s|):(.+?)(?:\||</div>)', item)[0]
				# except:
					# cast = '0'
				# cast = client.replaceHTMLCodes(cast)
				# cast = cast.encode('utf-8')
				# cast = client.parseDOM(cast, 'a')
				# if cast == []:
					# cast = '0'

				plot = '0'
				try:
					plot = client.parseDOM(item, 'p', attrs = {'class': 'text-muted'})[0]
				except:
					try:
						plot = client.parseDOM(item, 'div', attrs = {'class': 'item_description'})[0]
					except:
						pass
				plot = plot.rsplit('<span>', 1)[0].strip()
				plot = re.sub('<.+?>|</.+?>', '', plot)
				if plot == '':
					plot = '0'
				plot = client.replaceHTMLCodes(plot)
				plot = plot.encode('utf-8')

				list.append({'title': title, 'originaltitle': title, 'year': year, 'genre': genre, 'duration': duration,
							'rating': rating, 'votes': votes, 'mpaa': mpaa, 'director': director, 'writer': '0',
							'plot': plot, 'imdb': imdb, 'tmdb': '0', 'tvdb': '0', 'poster': poster, 'next': next})
			except:
				pass
		return list


	def imdb_person_list(self, url):
		list = []
		try:
			result = client.request(url)
			result = result.decode('iso-8859-1').encode('utf-8')
			items = client.parseDOM(result, 'div', attrs = {'class': '.+? lister-item'}) + client.parseDOM(result, 'div', attrs = {'class': 'lister-item .+?'})
		except:
			import traceback
			traceback.print_exc()

		for item in items:
			try:
				name = client.parseDOM(item, 'a')[1]
				name = client.replaceHTMLCodes(name)
				name = name.encode('utf-8')

				url = client.parseDOM(item, 'a', ret='href')[1]
				url = re.findall('(nm\d*)', url, re.I)[0]
				url = self.person_link % url
				url = client.replaceHTMLCodes(url)
				url = url.encode('utf-8')

				image = client.parseDOM(item, 'img', ret='src')[0]
				image = re.sub('(?:_SX|_SY|_UX|_UY|_CR|_AL)(?:\d+|_).+?\.', '_SX500.', image)
				image = client.replaceHTMLCodes(image)
				image = image.encode('utf-8')

				list.append({'name': name, 'url': url, 'image': image})
			except:
				import traceback
				traceback.print_exc()

		return list


	def imdb_user_list(self, url):
		list = []
		try:
			result = client.request(url)
			result = result.decode('iso-8859-1').encode('utf-8')
			items = client.parseDOM(result, 'li', attrs={'class': 'ipl-zebra-list__item user-list'})
			# Gaia uses this but seems to break the IMDb user list
			# items = client.parseDOM(result, 'div', attrs = {'class': 'list_name'})
		except:
			pass

		for item in items:
			try:
				name = client.parseDOM(item, 'a')[0]
				name = client.replaceHTMLCodes(name)
				name = name.encode('utf-8')

				url = client.parseDOM(item, 'a', ret='href')[0]
				url = url = url.split('/list/', 1)[-1].strip('/')
				# url = url.split('/list/', 1)[-1].replace('/', '')
				url = self.imdblist_link % url
				url = client.replaceHTMLCodes(url)
				url = url.encode('utf-8')

				list.append({'name': name, 'url': url, 'context': url})
			except:
				pass

		list = sorted(list, key=lambda k: re.sub('(^the |^a |^an )', '', k['name'].lower()))
		return list


	def worker(self, level = 1):
		try:
			if self.list is None or self.list == []:
				return
			self.meta = []
			total = len(self.list)

			for i in range(0, total): 
				self.list[i].update({'metacache': False})

			self.list = metacache.fetch(self.list, self.lang, self.user)

			for r in range(0, total, 40):
				threads = []
				for i in range(r, r + 40):
					if i <= total:
						threads.append(workers.Thread(self.super_info, i, total))
				[i.start() for i in threads]
				[i.join() for i in threads]

			if self.meta:
				metacache.insert(self.meta)

			self.list = [i for i in self.list if i['tvdb'] != '0']
		except:
			import traceback
			traceback.print_exc()


	def metadataRetrieve(self, title, year, imdb, tmdb, tvdb):
		self.list = [{'metacache': False, 'title': title, 'year': year, 'imdb': imdb, 'tmdb': tmdb, 'tvdb': tvdb}]
		self.worker()
		return self.list[0]


	def super_info(self, i, total):
		try:
			if self.list[i]['metacache'] == True:
				raise Exception()

			imdb = self.list[i]['imdb'] if 'imdb' in self.list[i] else '0'
			tmdb = self.list[i]['tmdb'] if 'tmdb' in self.list[i] else '0'
			tvdb = self.list[i]['tvdb'] if 'tvdb' in self.list[i] else '0'

			if imdb == '0' or tmdb == '0' or tvdb == '0':
				try:
					trakt_ids = trakt.SearchTVShow(urllib.quote_plus(self.list[i]['title']), self.list[i]['year'], full=False)[0]
					trakt_ids = trakt_ids.get('show', '0')
					# log_utils.log('trakt_ids = %s for title = %s' % (str(trakt_ids), str(self.list[i]['title'])), __name__, log_utils.LOGDEBUG)

					if imdb == '0':
						imdb = trakt_ids.get('ids', {}).get('imdb', '0')
						if imdb == '' or imdb is None or imdb == 'None':
							imdb = '0'

					if tmdb == '0':
						tmdb = str(trakt_ids.get('ids', {}).get('tmdb', 0))
						if tmdb == '' or tmdb is None or tmdb == 'None':
							tmdb = '0'

					if tvdb == '0':
						tvdb = str(trakt_ids.get('ids', {}).get('tvdb', 0))
						if tvdb == '' or tvdb is None or tvdb == 'None':
							tvdb = '0'
				except:
					pass

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

				dupe = re.findall('[***]Duplicate (\d*)[***]', name)
				if dupe:
					tvdb = str(dupe[0])
				if tvdb == '':
					tvdb = '0'

###--Check TVDb for missing info
			if tvdb == '0' or imdb == '0':
				url = self.tvdb_by_query % (urllib.quote_plus(self.list[i]['title']))

				item2 = client.request(url, timeout='10')
				item2 = re.sub(r'[^\x00-\x7F]+', '', item2)
				item2 = client.replaceHTMLCodes(item2)
				item2 = client.parseDOM(item2, 'Series')

				if tvdb == '0':
					try:
						tvdb = client.parseDOM(item2, 'seriesid')[0]
					except:
						tvdb = '0'

				if imdb == '0':
					try:
						imdb = client.parseDOM(item2, 'IMDB_ID')[0]
					except:
						imdb = '0'

			if tvdb == '0' or tvdb is None:
				raise Exception()

			url = self.tvdb_info_link % (tvdb, self.lang)
			item = client.request(url, timeout='10', error = True)

			if item is None:
				raise Exception()

			if imdb == '0':
				try:
					imdb = client.parseDOM(item, 'IMDB_ID')[0]
				except:
					pass
				if imdb == '':
					imdb = '0'
				imdb = imdb.encode('utf-8')

			try:
				title = client.parseDOM(item, 'SeriesName')[0]
			except:
				title = ''
			if title == '':
				title = '0'
			title = client.replaceHTMLCodes(title)
			title = title.encode('utf-8')

			try:
				year = client.parseDOM(item, 'FirstAired')[0]
			except:
				year = ''
			try:
				year = re.compile('(\d{4})').findall(year)[0]
			except:
				year = ''
			if year == '':
				year = '0'
			year = year.encode('utf-8')

			try:
				premiered = client.parseDOM(item, 'FirstAired')[0]
			except:
				premiered = '0'
			if premiered == '':
				premiered = '0'
			premiered = client.replaceHTMLCodes(premiered)
			premiered = premiered.encode('utf-8')

			if 'studio' not in self.list[i] or self.list[i]['studio'] == '0':
				studio = client.parseDOM(item, 'Network')[0]
				studio = client.replaceHTMLCodes(studio)
				studio = studio.encode('utf-8')
				if studio is None or studio == '': studio = '0'
			else:
				studio = self.list[i]['studio']

			if 'genre' not in self.list[i] or self.list[i]['genre'] == '0':
				genre = client.parseDOM(item, 'Genre')[0]
				genre = [x for x in genre.split('|') if x != '']
				genre = ' / '.join(genre)
				genre = client.replaceHTMLCodes(genre)
				genre = genre.encode('utf-8')
				if genre is None or genre == '': genre = '0'
			else:
				genre = self.list[i]['genre']

			if 'duration' not in self.list[i] or self.list[i]['duration'] == '0':
				duration = client.parseDOM(item, 'Runtime')[0]
				duration = client.replaceHTMLCodes(duration)
				duration = duration.encode('utf-8')
				if duration is None or duration == '': duration = '0'
			else:
				duration = self.list[i]['duration']

			if 'rating' not in self.list[i] or self.list[i]['rating'] == '0':
				rating = client.parseDOM(item, 'Rating')[0]
				rating = client.replaceHTMLCodes(rating)
				rating = rating.encode('utf-8')
				if rating is None or rating == '': rating = '0'
			else:
				rating = self.list[i]['rating']

			if 'votes' not in self.list[i] or self.list[i]['votes'] == '0':
				votes = client.parseDOM(item, 'RatingCount')[0]
				votes = client.replaceHTMLCodes(votes)
				votes = votes.encode('utf-8')
				if votes is None or votes == '': votes = '0'
			else:
				votes = self.list[i]['votes']

			if 'mpaa' not in self.list[i] or self.list[i]['mpaa'] == '0':
				mpaa = client.parseDOM(item, 'ContentRating')[0]
				mpaa = client.replaceHTMLCodes(mpaa)
				mpaa = mpaa.encode('utf-8')
				if mpaa is None or mpaa == '': mpaa = '0'
			else:
				mpaa = self.list[i]['mpaa']

			if 'castandart' not in self.list[i] or self.list[i]['castandart'] == '0':
				url2 = self.tvdb_info_link % (tvdb, 'actors')
				actors = client.request(url2, timeout='10', error=True)
				castandart = []
				if actors is not None:
					import xml.etree.ElementTree as ET
					tree = ET.ElementTree(ET.fromstring(actors))
					root = tree.getroot()
					for actor in root.iter('Actor'):
						person = [name.text for name in actor]
						image = person[1]
						name = person[2]
						role = person[3]
						try:
							castandart.append({'name': name.encode('utf-8'), 'role': role.encode('utf-8'), 'thumbnail': ((self.tvdb_image + image) if image is not None else '0')})
						except:
							castandart.append({'name': name, 'role': role, 'thumbnail': ((self.tvdb_image + image) if image is not None else '0')})

			try:
				plot = client.parseDOM(item, 'Overview')[0]
			except:
				plot = ''
			if plot == '':
				plot = '0'
			plot = client.replaceHTMLCodes(plot)
			plot = plot.encode('utf-8')

			try:
				status = client.parseDOM(item, 'Status')[0]
			except:
				status = ''
			if status == '':
				status = 'Ended'
			status = client.replaceHTMLCodes(status)
			status = status.encode('utf-8')

			if 'poster' not in self.list[i] or self.list[i]['poster'] == '0':
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
			else:
				poster = self.list[i]['poster']

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

			if 'fanart' not in self.list[i] or self.list[i]['fanart'] == '0':
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
			else:
				fanart = self.list[i]['fanart']

			item = {'extended': True, 'title': title, 'year': year, 'imdb': imdb, 'tmdb': tmdb, 'tvdb': tvdb,
					'premiered': premiered, 'studio': studio, 'genre': genre, 'duration': duration,
					'rating': rating, 'votes': votes, 'mpaa': mpaa, 'castandart': castandart, 'plot': plot,
					'status': status, 'poster': poster, 'poster2': '0', 'poster3': '0', 'banner': banner,
					'banner2': '0', 'fanart': fanart, 'fanart2': '0', 'fanart3': '0', 'clearlogo': '0',
					'clearart': '0', 'landscape': fanart, 'metacache': False}

			meta = {'imdb': imdb, 'tmdb': tmdb, 'tvdb': tvdb, 'lang': self.lang, 'user': self.user, 'item': item}

			# fanart_thread = threading.Thread
			if (poster == '0' or fanart == '0' and total > 40) or (self.disable_fanarttv != 'true'):
				if tvdb is not None or tvdb != '0':
					from resources.lib.indexers import fanarttv
					extended_art = fanarttv.get_tvshow_art(tvdb)
					if extended_art is not None:
						item.update(extended_art)
						meta.update(item)

			if (self.disable_fanarttv == 'true' and (poster == '0' or fanart == '0')) or (
				self.disable_fanarttv != 'true' and ((poster == '0' and item.get('poster2') == '0') or (
				fanart == '0' and item.get('fanart2') == '0'))):
				# if total <= 40:
				from resources.lib.indexers.tmdb import TVshows
				tmdb_art = TVshows().tmdb_art(tmdb)
				item.update(tmdb_art)
				if item.get('landscape', '0') == '0':
					landscape = item.get('fanart3', '0')
					item.update({'landscape': landscape})
				meta.update(item)

			item = dict((k,v) for k, v in item.iteritems() if v != '0')
			self.list[i].update(item)

			self.meta.append(meta)
		except:
			pass


	def tvshowDirectory(self, items, next=True):
		if items is None or len(items) == 0:
			control.idle()
			control.notification(title = 32002, message = 33049, icon = 'INFO')
			sys.exit()

		sysaddon = sys.argv[0]
		syshandle = int(sys.argv[1])

		addonPoster, addonBanner = control.addonPoster(), control.addonBanner()
		addonFanart, settingFanart = control.addonFanart(), control.setting('fanart')

		flatten = True if control.setting('flatten.tvshows') == 'true' else False

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
		nextMenu = control.lang(32053).encode('utf-8')
		playRandom = control.lang(32535).encode('utf-8')
		addToLibrary = control.lang(32551).encode('utf-8')

		for i in items:
			try:
				imdb, tmdb, tvdb, year = i['imdb'], i['tmdb'], i['tvdb'], i['year']

				label = i['title']

				systitle = sysname = urllib.quote_plus(i['originaltitle'])
				sysimage = urllib.quote_plus(i['poster'])

				meta = dict((k,v) for k, v in i.iteritems() if v != '0')
				meta.update({'code': imdb, 'imdbnumber': imdb, 'imdb_id': imdb})
				# meta.update({'tmdb_id': tmdb})
				meta.update({'tvdb_id': tvdb})
				meta.update({'mediatype': 'tvshow'})
				# meta.update({'tvshowtitle': systitle})
				meta.update({'tvshowtitle': label})
				meta.update({'trailer': '%s?action=trailer&name=%s' % (sysaddon, urllib.quote_plus(label))})

				try:
					plot = meta['plot']
					index = plot.rfind('See full summary')
					if index >= 0: plot = plot[:index]
					plot = plot.strip()
					if re.match('[a-zA-Z\d]$', plot): plot += ' ...'
					meta['plot'] = plot
				except:
					pass

				try:
					meta.update({'duration': str(int(meta['duration']) * 60)})
				except:
					pass
				try:
					meta.update({'genre': cleangenre.lang(meta['genre'], self.lang)})
				except:
					pass

				poster = '0'
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

				fanart = '0'
				if settingFanart:
					if fanart == '0' and 'fanart3' in i: fanart = i['fanart3']
					if fanart == '0' and 'fanart2' in i: fanart = i['fanart2']
					if fanart == '0' and 'fanart' in i: fanart = i['fanart']

				banner = '0'
				if banner == '0' and 'banner3' in i: banner = i['banner3']
				if banner == '0' and 'banner2' in i: banner = i['banner2']
				if banner == '0' and 'banner' in i: banner = i['banner']
				if banner == '0': banner = fanart

				clearlogo = '0'
				if clearlogo == '0' and 'clearlogo' in i: clearlogo = i['clearlogo']

				clearart = '0'
				if clearart == '0' and 'clearart' in i: clearart = i['clearart']

				landscape = '0'
				if landscape == '0' and 'landscape' in i: landscape = i['landscape']

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
				if landscape != '0' and landscape is not None:
					art.update({'landscape': landscape})

				if flatten is True:
					url = '%s?action=episodes&tvshowtitle=%s&year=%s&imdb=%s&tvdb=%s' % (sysaddon, systitle, year, imdb, tvdb)
				else:
					url = '%s?action=seasons&tvshowtitle=%s&year=%s&imdb=%s&tvdb=%s' % (sysaddon, systitle, year, imdb, tvdb)

####-Context Menu and Overlays-####
				cm = []
				if self.traktCredentials is True:
					cm.append((traktManagerMenu, 'RunPlugin(%s?action=traktManager&name=%s&imdb=%s&tvdb=%s)' % (sysaddon, sysname, imdb, tvdb)))
				try:
					indicators = playcount.getTVShowIndicators()
					overlay = int(playcount.getTVShowOverlay(indicators, imdb, tvdb))
					watched = overlay == 7
					if watched:
						meta.update({'playcount': 1, 'overlay': 7})
						cm.append((unwatchedMenu, 'RunPlugin(%s?action=tvPlaycount&name=%s&imdb=%s&tvdb=%s&query=6)' % (sysaddon, systitle, imdb, tvdb)))
					else:
						meta.update({'playcount': 0, 'overlay': 6})
						cm.append((watchedMenu, 'RunPlugin(%s?action=tvPlaycount&name=%s&imdb=%s&tvdb=%s&query=7)' % (sysaddon, systitle, imdb, tvdb)))
				except:
					pass

				sysmeta = urllib.quote_plus(json.dumps(meta))
				# sysart = urllib.quote_plus(json.dumps(art))

				cm.append(('Find similar', 'ActivateWindow(10025,%s?action=tvshows&url=http://api.trakt.tv/shows/%s/related,return)' % (sysaddon, imdb)))
				cm.append((playRandom, 'RunPlugin(%s?action=random&rtype=season&tvshowtitle=%s&year=%s&imdb=%s&tvdb=%s)' % (
									sysaddon, systitle, year, imdb, tvdb)))

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
					count = playcount.getShowCount(indicators, imdb, tvdb, unwatchedLimit)
					if count:
						item.setProperty('TotalEpisodes', str(count['total']))
						item.setProperty('WatchedEpisodes', str(count['watched']))
						item.setProperty('UnWatchedEpisodes', str(count['unwatched']))

				if seasoncountEnabled == 'true' and self.traktCredentials is True:
					total_seasons = trakt.getSeasons(imdb, full=False)
					if total_seasons is not None:
						total_seasons = [i['number'] for i in total_seasons]
						total_seasons = len(total_seasons)
						# if control.setting('tv.specials') == 'true' and self.season_special is True:
							# total_seasons = total_seasons - 1
						item.setProperty('TotalSeasons', str(total_seasons))

				if 'castandart' in i:
					item.setCast(i['castandart'])

				# if fanart != '0' and fanart is not None:
					# item.setProperty('Fanart_Image', fanart)
				item.setArt(art)
				item.setInfo(type='video', infoLabels=control.metadataClean(meta))
				video_streaminfo = {'codec': 'h264'}
				item.addStreamInfo('video', video_streaminfo)
				item.addContextMenuItems(cm)
				control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)
			except:
				import traceback
				traceback.print_exc()
				pass

		if next:
			try:
				url = items[0]['next']
				if url == '': raise Exception()

				if self.imdb_link in url or self.trakt_link in url:
					url = '%s?action=tvshowPage&url=%s' % (sysaddon, urllib.quote_plus(url))

				elif self.tmdb_link in url:
					url = '%s?action=tmdbTvshowPage&url=%s' % (sysaddon, urllib.quote_plus(url))

				elif self.tvmaze_link in url:
					url = '%s?action=tvmazeTvshowPage&url=%s' % (sysaddon, urllib.quote_plus(url))

				item = control.item(label=nextMenu)
				icon = control.addonNext()
				item.setArt({'icon': icon, 'thumb': icon, 'poster': icon, 'banner': icon})
				# if addonFanart is not None:
					# item.setProperty('Fanart_Image', addonFanart)
				control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)
			except:
				pass

		control.content(syshandle, 'tvshows')
		control.directory(syshandle, cacheToDisc=True)
		views.setView('tvshows', {'skin.estuary': 55, 'skin.confluence': 500})


	def addDirectory(self, items, queue=False):
		if items is None or len(items) == 0: 
			control.idle()
			control.notification(title = 32002, message = 33049, icon = 'INFO')
			sys.exit()

		sysaddon = sys.argv[0]
		syshandle = int(sys.argv[1])

		addonFanart, addonThumb, artPath = control.addonFanart(), control.addonThumb(), control.artPath()
		queueMenu = control.lang(32065).encode('utf-8')
		playRandom = control.lang(32535).encode('utf-8')
		addToLibrary = control.lang(32551).encode('utf-8')

		for i in items:
			try:
				name = i['name']

				if i['image'].startswith('http'):
					thumb = i['image']
				elif artPath is not None:
					thumb = os.path.join(artPath, i['image'])
				else:
					thumb = addonThumb

				icon = i.get('icon', 0)
				if icon is None:
					icon = 'DefaultFolder.png'

				url = '%s?action=%s' % (sysaddon, i['action'])
				try:
					url += '&url=%s' % urllib.quote_plus(i['url'])
				except:
					pass

				cm = []
				cm.append((playRandom, 'RunPlugin(%s?action=random&rtype=show&url=%s)' % (sysaddon, urllib.quote_plus(i['url']))))

				if queue is True:
					cm.append((queueMenu, 'RunPlugin(%s?action=queueItem)' % sysaddon))

				try:
					cm.append((addToLibrary, 'RunPlugin(%s?action=tvshowsToLibrary&url=%s)' % (sysaddon, urllib.quote_plus(i['context']))))
				except:
					pass

				cm.append(('[COLOR red]Venom Settings[/COLOR]', 'RunPlugin(%s?action=openSettings&query=0.0)' % sysaddon))

				item = control.item(label = name)
				item.setArt({'icon': icon, 'poster': thumb, 'thumb': thumb, 'banner': thumb})

				if addonFanart is not None:
					item.setProperty('Fanart_Image', addonFanart)

				item.addContextMenuItems(cm)
				control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)
			except:
				pass

		control.content(syshandle, 'addons')
		control.directory(syshandle, cacheToDisc=True)
