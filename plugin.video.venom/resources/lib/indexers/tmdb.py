# -*- coding: utf-8 -*-

'''
Venom
'''

import re, datetime
import requests, xbmc
from time import sleep

from resources.lib.modules import control
from resources.lib.modules import client
from resources.lib.modules import metacache
from resources.lib.modules import log_utils


class Movies:
	def __init__(self):
		self.list = []
		self.meta = []

		self.datetime = (datetime.datetime.utcnow() - datetime.timedelta(hours = 5))

		self.lang = control.apiLanguage()['trakt']

		self.tmdb_key = control.setting('tm.user')
		if self.tmdb_key == '' or self.tmdb_key is None:
			self.tmdb_key = '3320855e65a9758297fec4f7c9717698'
		# access_token = 'eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIzMzIwODU1ZTY1YTk3NTgyOTdmZWM0ZjdjOTcxNzY5OCIsInN1YiI6IjVjNDYwODQ2OTI1MTQxMGUyNDRmMDU4ZiIsInNjb3BlcyI6WyJhcGlfcmVhZCJdLCJ2ZXJzaW9uIjoxfQ.3pqIZisgsykso59k521K4plalhK7lnah2zADdHiB_g4'

		self.tmdb_link = 'http://api.themoviedb.org'
		# self.tmdb_poster = 'http://image.tmdb.org/t/p/w500'
		self.tmdb_poster = 'http://image.tmdb.org/t/p/w300'
		# self.tmdb_fanart = 'http://image.tmdb.org/t/p/original'
		self.tmdb_fanart = 'http://image.tmdb.org/t/p/w1280'

		self.tmdb_info_link = 'http://api.themoviedb.org/3/movie/%s?api_key=%s&language=%s&append_to_response=credits,release_dates' % ('%s', self.tmdb_key, self.lang)
###                                                                                  other "append_to_response" options                                           external_ids,alternative_titles,videos,images
		self.tmdb_art_link = 'http://api.themoviedb.org/3/movie/%s/images?api_key=%s&include_image_language=en,%s,null' % ('%s', self.tmdb_key, self.lang)

		self.disable_fanarttv = control.setting('disable.fanarttv')


	def get_request(self, url):
		try:
			try:
				response = requests.get(url)
			except requests.exceptions.SSLError:
				response = requests.get(url, verify=False)
		except requests.exceptions.ConnectionError:
			control.notification(title='default', message=32024, icon='INFO')
			return

		if '200' in str(response):
			return response.json()
		elif 'Retry-After' in response.headers:
			# API REQUESTS ARE BEING THROTTLED, INTRODUCE WAIT TIME
			throttleTime = response.headers['Retry-After']
			control.notification(title='default', message='TMDB Throttling Applied, Sleeping for %s seconds' % throttleTime, icon='INFO')
			# log_utils.log('TMDB Throttling Applied, Sleeping for %s seconds' % throttleTime, __name__, log_utils.LOGDEBUG)
			sleep(int(throttleTime) + 1)
			return self.get_request(url)
		else:
			log_utils.log('Get request failed to TMDB URL: %s' % url, __name__, log_utils.LOGDEBUG)
			log_utils.log('TMDB Response: %s' % response.text, __name__, log_utils.LOGDEBUG)
			return None


	def tmdb_list(self, url):
		next = url
		try:
			result = self.get_request(url % self.tmdb_key)
			items = result['results']
		except:
			return

		try:
			page = int(result['page'])
			total = int(result['total_pages'])
			if page >= total:
				raise Exception()
			if 'page=' not in url:
				raise Exception()
			next = '%s&page=%s' % (next.split('&page=', 1)[0], page+1)
		except:
			next = ''

		for item in items:
			try:
				title = (item.get('title')).encode('utf-8')

				try: 
					originaltitle = (item.get('original_title')).encode('utf-8')
				except:
					originaltitle = title

				year = str(item.get('release_date')[:4])

				tmdb = item.get('id')

				poster = '%s%s' % (self.tmdb_poster, item['poster_path']) if item['poster_path'] else '0'
				fanart = '%s%s' % (self.tmdb_fanart, item['backdrop_path']) if item['backdrop_path'] else '0'

				premiered = item.get('release_date')

				rating = str(item.get('vote_average', '0'))
				votes = str(format(int(item.get('vote_count', '0')),',d'))

				plot = item.get('overview')

				try:
					tagline = item.get('tagline', '0')
					if tagline == '' or tagline == '0' or tagline is None:
						tagline = re.compile('[.!?][\s]{1,2}(?=[A-Z])').split(plot)[0]
				except:
					tagline = '0'

##--TMDb additional info
				url = self.tmdb_info_link % tmdb
				item = self.get_request(url)

				imdb = item.get('imdb_id', '0')
				if imdb == '' or imdb is None:
					imdb = '0'

				# studio = item['production_companies']
				# try: studio = [x['name'] for x in studio][0]
				# except: studio = '0'
				# if studio == '' or studio is None: studio = '0'

				try:
					genre = item['genres']
					genre = [x['name'] for x in genre]
					genre = (' / '.join(genre))
				except:
					genre = 'NA'

				duration = str(item.get('runtime', '0'))

				mpaa = item['release_dates']['results']
				mpaa = [i for i in mpaa if i['iso_3166_1'] == 'US']
				try:
					mpaa = mpaa[0].get('release_dates')[-1].get('certification')
					if not mpaa:
						mpaa = mpaa[0].get('release_dates')[0].get('certification')
						if not mpaa:
							mpaa = mpaa[0].get('release_dates')[1].get('certification')
					mpaa = str(mpaa)
				except: mpaa = '0'

				director = item['credits']['crew']
				try:
					director = [x['name'] for x in director if x['job'] == 'Director']
				except:
					director = '0'
				if director == '' or director is None or director == []:
					director = '0'
				director = (' / '.join(director))

				writer = item['credits']['crew']
				try:
					writer = [x['name'] for x in writer if x['job'] in ['Writer', 'Screenplay']]
				except:
					writer = '0'
				try:
					writer = [x for n,x in enumerate(writer) if x not in writer[:n]]
				except:
					writer = '0'
				if writer == '' or writer is None or writer == []:
					writer = '0'
				writer = (' / '.join(writer))

				cast = item['credits']['cast']
				try:
					cast = [(x['name'], x['character']) for x in cast]
				except:
					cast = []

				item = {}
				item = {'content': 'movie', 'title': title, 'originaltitle': originaltitle, 'year': year, 'premiered': premiered, 'studio': '0', 'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes,
								'mpaa': mpaa, 'director': director, 'writer': writer, 'cast': cast, 'plot': plot, 'tagline': tagline, 'code': tmdb, 'imdb': imdb, 'tmdb': tmdb, 'tvdb': '0', 'poster': poster,
								'poster2': '0', 'poster3': '0', 'banner': '0', 'fanart': fanart, 'fanart2': '0', 'fanart3': '0', 'clearlogo': '0', 'clearart': '0', 'landscape': fanart, 'metacache': False, 'next': next}
				meta = {}
				meta = {'imdb': imdb, 'tmdb': tmdb, 'tvdb': '0', 'lang': self.lang, 'user': self.tmdb_key, 'item': item}

				# fanart_thread = threading.Thread
				if self.disable_fanarttv != 'true':
					from resources.lib.indexers import fanarttv
					extended_art = fanarttv.get_movie_art(imdb, tmdb)

					if extended_art is not None:
						item.update(extended_art)
						meta.update(item)

				self.list.append(item)
				self.meta.append(meta)
				metacache.insert(self.meta)

			except:
				pass
		return self.list


	def tmdb_collections_list(self, url):
		next = url
		try:
			result = self.get_request(url)
			if '/3/' in url:
				items = result['items']
			else:
				items = result['results']
		except:
			return

		try:
			page = int(result['page'])
			total = int(result['total_pages'])
			if page >= total:
				raise Exception()
			if 'page=' not in url:
				raise Exception()
			next = '%s&page=%s' % (next.split('&page=', 1)[0], page+1)
		except:
			next = ''

		for item in items:
			try:
				media_type = item['media_type']

				title = (item.get('title')).encode('utf-8')
				if media_type != 'movie':
					title = (item.get('name')).encode('utf-8')

				try: 
					originaltitle = (item.get('original_title')).encode('utf-8')
				except:
					originaltitle = title

				year = str(item.get('release_date')[:4])

				tmdb = item.get('id')

				poster = '%s%s' % (self.tmdb_poster, item['poster_path']) if item['poster_path'] else '0'
				fanart = '%s%s' % (self.tmdb_fanart, item['backdrop_path']) if item['backdrop_path'] else '0'

				premiered = item.get('release_date')

				rating = str(item.get('vote_average', '0'))
				votes = str(format(int(item.get('vote_count', '0')),',d'))

				plot = (item.get('overview'))

				try:
					tagline = item.get('tagline', '0')
					if tagline == '' or tagline == '0' or tagline is None:
						tagline = re.compile('[.!?][\s]{1,2}(?=[A-Z])').split(plot)[0]
				except:
					tagline = '0'


##--TMDb additional info
				url = self.tmdb_info_link % tmdb
				item = self.get_request(url)

				imdb = item.get('imdb_id', '0')
				if imdb == '' or imdb is None:
					imdb = '0'

				# studio = item['production_companies']
				# try: studio = [x['name'] for x in studio][0]
				# except: studio = '0'
				# if studio == '' or studio is None: studio = '0'

				genre = item['genres']
				try: genre = [x['name'] for x in genre]
				except: genre = '0'
				genre = ' / '.join(genre)
				if not genre:
					genre = 'NA'

				duration = str(item.get('runtime', '0'))

				mpaa = item['release_dates']['results']
				mpaa = [i for i in mpaa if i['iso_3166_1'] == 'US']
				try:
					mpaa = mpaa[0].get('release_dates')[-1].get('certification')
					if not mpaa:
						mpaa = mpaa[0].get('release_dates')[0].get('certification')
						if not mpaa:
							mpaa = mpaa[0].get('release_dates')[1].get('certification')
					mpaa = str(mpaa)
				except: mpaa = '0'

				director = item['credits']['crew']
				try: director = [x['name'] for x in director if x['job'] == 'Director']
				except: director = '0'
				if director == '' or director is None or director == []: director = '0'
				director = ' / '.join(director)

				writer = item['credits']['crew']
				try:
					writer = [x['name'] for x in writer if x['job'] in ['Writer', 'Screenplay']]
				except:
					writer = '0'
				try:
					writer = [x for n,x in enumerate(writer) if x not in writer[:n]]
				except:
					writer = '0'
				if writer == '' or writer is None or writer == []:
					writer = '0'
				writer = (' / '.join(writer))

				cast = item['credits']['cast']
				try:
					cast = [(x['name'], x['character']) for x in cast]
				except:
					cast = []

				item = {}
				item = {'content': 'movie', 'title': title, 'originaltitle': originaltitle, 'year': year, 'premiered': premiered, 'studio': '0', 'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes,
								'mpaa': mpaa, 'director': director, 'writer': writer, 'cast': cast, 'plot': plot, 'tagline': tagline, 'code': tmdb, 'imdb': imdb, 'tmdb': tmdb, 'tvdb': '0', 'poster': poster,
								'poster2': '0', 'poster3': '0', 'banner': '0', 'fanart': fanart, 'fanart2': '0', 'fanart3': '0', 'clearlogo': '0', 'clearart': '0', 'landscape': fanart, 'metacache': False, 'next': next}
				meta = {}
				meta = {'imdb': imdb, 'tmdb': tmdb, 'tvdb': '0', 'lang': self.lang, 'user': self.tmdb_key, 'item': item}

				# fanart_thread = threading.Thread
				if self.disable_fanarttv != 'true':
					from resources.lib.indexers import fanarttv
					extended_art = fanarttv.get_movie_art(imdb, tmdb)

					if extended_art is not None:
						item.update(extended_art)
						meta.update(item)

				self.list.append(item)
				self.meta.append(meta)
				metacache.insert(self.meta)

			except:
				pass
		return self.list


	def tmdb_art(self, tmdb):
		if (self.tmdb_key == '') or (tmdb == '0' or tmdb is None):
			return None

		art3 = self.get_request(self.tmdb_art_link % tmdb)
		if art3 is None:
			return None

		try:
			poster3 = art3['posters']
			poster3 = [(x['width'], x['file_path']) for x in poster3]
			poster3 = [x[1] for x in poster3]
			poster3 = self.tmdb_poster + poster3[0]
		except:
			poster3 = '0'

		try:
			fanart3 = art3['backdrops']
			fanart3 = [(x['width'], x['file_path']) for x in fanart3]
			fanart3 = [x[1] for x in fanart3]
			fanart3 = self.tmdb_fanart + fanart3[0]
		except:
			fanart3 = '0'

		extended_art = {'extended': True, 'poster3': poster3, 'fanart3': fanart3}
		return extended_art



class TVshows:
	def __init__(self):
		self.list = []
		self.meta = []

		self.datetime = (datetime.datetime.utcnow() - datetime.timedelta(hours = 5))

		self.lang = control.apiLanguage()['tvdb']

		self.tmdb_key = control.setting('tm.user')
		if self.tmdb_key == '' or self.tmdb_key is None:
			self.tmdb_key = '3320855e65a9758297fec4f7c9717698'

		self.tmdb_link = 'http://api.themoviedb.org'
		# self.tmdb_poster = 'http://image.tmdb.org/t/p/w500'
		self.tmdb_poster = 'http://image.tmdb.org/t/p/w300'
		# self.tmdb_fanart = 'http://image.tmdb.org/t/p/original'
		self.tmdb_fanart = 'http://image.tmdb.org/t/p/w1280'

		self.tmdb_info_link = 'http://api.themoviedb.org/3/tv/%s?api_key=%s&language=%s&append_to_response=credits,content_ratings,external_ids' % ('%s', self.tmdb_key, self.lang)
###                                                                                  other "append_to_response" options                                           alternative_titles,videos,images

		self.tmdb_art_link = 'http://api.themoviedb.org/3/tv/%s/images?api_key=%s&include_image_language=en,%s,null' % ('%s', self.tmdb_key, self.lang)

		self.disable_fanarttv = control.setting('disable.fanarttv')


	def get_request(self, url):
		try:
			try:
				response = requests.get(url)
			except requests.exceptions.SSLError:
				response = requests.get(url, verify=False)
		except requests.exceptions.ConnectionError:
			control.notification(title='default', message=32024, icon='INFO')
			return

		if '200' in str(response):
			return response.json()
		elif 'Retry-After' in response.headers:
			# API REQUESTS ARE BEING THROTTLED, INTRODUCE WAIT TIME
			throttleTime = response.headers['Retry-After']
			control.notification(title='default', message='TMDB Throttling Applied, Sleeping for %s seconds' % throttleTime, icon='INFO')
			# log_utils.log('TMDB Throttling Applied, Sleeping for %s seconds' % throttleTime, __name__, log_utils.LOGDEBUG)
			sleep(int(throttleTime) + 1)
			return self.get_request(url)
		else:
			log_utils.log('Get request failed to TMDB URL: %s' % url, __name__, log_utils.LOGDEBUG)
			log_utils.log('TMDB Response: %s' % response.text, __name__, log_utils.LOGDEBUG)
			return None


	def tmdb_list(self, url):
		next = url
		try:
			result = self.get_request(url % self.tmdb_key)
			items = result['results']
		except:
			return

		try:
			page = int(result['page'])
			total = int(result['total_pages'])
			if page >= total:
				raise Exception()
			if 'page=' not in url:
				raise Exception()
			next = '%s&page=%s' % (next.split('&page=', 1)[0], page+1)
		except:
			next = ''

		for item in items:
			try:
				title = (item.get('name')).encode('utf-8')

				year = str(item.get('first_air_date')[:4])

				tmdb = item.get('id')

				poster = '%s%s' % (self.tmdb_poster, item['poster_path']) if item['poster_path'] else '0'
				fanart = '%s%s' % (self.tmdb_fanart, item['backdrop_path']) if item['backdrop_path'] else '0'

				premiered = item.get('first_air_date')

				rating = str(item.get('vote_average', '0'))
				votes = str(format(int(item.get('vote_count', '0')),',d'))

				plot = item.get('overview')

				try:
					tagline = item.get('tagline', '0')
					if tagline == '' or tagline == '0' or tagline is None:
						tagline = re.compile('[.!?][\s]{1,2}(?=[A-Z])').split(plot)[0]
				except:
					tagline = '0'

##--TMDb additional info
				url = self.tmdb_info_link % tmdb
				item = self.get_request(url)

				tvdb = str(item.get('external_ids').get('tvdb_id'))
				if tvdb == '' or tvdb is None:
					tvdb = '0'

				imdb = (item.get('external_ids').get('imdb_id'))
				if imdb == '' or imdb is None:
					imdb = '0'

				genre = item['genres']
				try:
					genre = [x['name'] for x in genre]
				except:
					genre = '0'
				genre = ' / '.join(genre)
				if not genre:
					genre = 'NA'

				duration = str(item.get('episode_run_time', '0')[0])

				try:
					mpaa = [i['rating'] for i in item['content_ratings']['results'] if i['iso_3166_1'] == 'US'][0]
				except: 
					try:
						mpaa = item['content_ratings'][0]['rating']
					except: mpaa = 'NR'

				studio = item['networks']
				try: studio = [x['name'] for x in studio][0]
				except: studio = '0'
				if studio == '' or studio is None: studio = '0'

				director = item['credits']['crew']
				# try: director = [x['name'] for x in director if x['job'].encode('utf-8') == 'Director']
				try: director = [x['name'] for x in director if x['job'] == 'Director']
				except: director = '0'
				if director == '' or director is None or director == []: director = '0'
				director = ' / '.join(director)

				writer = item['credits']['crew']
				# try: writer = [x['name'] for x in writer if x['job'].encode('utf-8') in ['Writer', 'Screenplay']]
				try: writer = [x['name'] for x in writer if x['job'] in ['Writer', 'Screenplay']]
				except: writer = '0'
				try: writer = [x for n,x in enumerate(writer) if x not in writer[:n]]
				except: writer = '0'
				if writer == '' or writer is None or writer == []: writer = '0'
				writer = ' / '.join(writer)

				cast = item['credits']['cast']
				# try: cast = [(x['name'].encode('utf-8'), x['character'].encode('utf-8')) for x in cast]
				try: cast = [(x['name'], x['character']) for x in cast]
				except: cast = []


				item = {}
				item = {'content': 'tvshow', 'title': title, 'originaltitle': title, 'year': year, 'premiered': premiered, 'studio': studio, 'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes,
								'mpaa': mpaa, 'director': director, 'writer': writer, 'cast': cast, 'plot': plot, 'tagline': tagline, 'code': tmdb, 'imdb': imdb, 'tmdb': tmdb, 'tvdb': tvdb, 'poster': poster,
								'poster2': '0', 'banner': '0', 'banner2': '0', 'fanart': fanart, 'fanart2': '0', 'clearlogo': '0', 'clearart': '0', 'landscape': fanart, 'metacache': False, 'next': next}

				meta = {}
				meta = {'tmdb': tmdb, 'imdb': imdb, 'tvdb': tvdb, 'lang': self.lang, 'user': self.tmdb_key, 'item': item}

				# fanart_thread = threading.Thread
				if self.disable_fanarttv != 'true':
					from resources.lib.indexers import fanarttv
					extended_art = fanarttv.get_tvshow_art(tvdb)

					if extended_art is not None:
						item.update(extended_art)
						meta.update(item)

				self.list.append(item)
				self.meta.append(meta)
				metacache.insert(self.meta)
			except:
				pass
		return self.list


	def tmdb_collections_list(self, url):
		result = self.get_request(url)
		items = result['items']
		next = ''
		for item in items:
			try:
				media_type = item['media_type']

				title = (item.get('name')).encode('utf-8')

				year = str(item.get('first_air_date')[:4])

				tmdb = item.get('id')

				poster = '%s%s' % (self.tmdb_poster, item['poster_path']) if item['poster_path'] else '0'
				fanart = '%s%s' % (self.tmdb_fanart, item['backdrop_path']) if item['backdrop_path'] else '0'

				premiered = item.get('first_air_date')

				rating = str(item.get('vote_average', '0'))
				votes = str(format(int(item.get('vote_count', '0')),',d'))

				plot = (item.get('overview'))

				try:
					tagline = item.get('tagline', '0')
					if tagline == '' or tagline == '0' or tagline is None:
						tagline = re.compile('[.!?][\s]{1,2}(?=[A-Z])').split(plot)[0]
				except:
					tagline = '0'

##--TMDb additional info
				url = self.tmdb_info_link % tmdb
				item = self.get_request(url)

				tvdb = str(item.get('external_ids').get('tvdb_id'))
				if tvdb == '' or tvdb is None:
					tvdb = '0'

				imdb = (item.get('external_ids').get('imdb_id'))
				if imdb == '' or imdb is None:
					imdb = '0'

				genre = item['genres']
				try: genre = [x['name'] for x in genre]
				except: genre = '0'
				genre = ' / '.join(genre)
				if not genre:
					genre = 'NA'

				duration = str(item.get('episode_run_time', '0'))

				try:
					mpaa = [i['rating'] for i in item['content_ratings']['results'] if i['iso_3166_1'] == 'US'][0]
				except: 
					try:
						mpaa = item['content_ratings'][0]['rating']
					except: mpaa = 'NR'

				studio = item['networks']
				try: studio = [x['name'] for x in studio][0]
				except: studio = '0'
				if studio == '' or studio is None: studio = '0'

				director = item['credits']['crew']
				# try: director = [x['name'] for x in director if x['job'].encode('utf-8') == 'Director']
				try: director = [x['name'] for x in director if x['job'] == 'Director']
				except: director = '0'
				if director == '' or director is None or director == []: director = '0'
				director = ' / '.join(director)

				writer = item['credits']['crew']
				# try: writer = [x['name'] for x in writer if x['job'].encode('utf-8') in ['Writer', 'Screenplay']]
				try: writer = [x['name'] for x in writer if x['job'] in ['Writer', 'Screenplay']]
				except: writer = '0'
				try: writer = [x for n,x in enumerate(writer) if x not in writer[:n]]
				except: writer = '0'
				if writer == '' or writer is None or writer == []: writer = '0'
				writer = ' / '.join(writer)

				cast = item['credits']['cast']
				# try: cast = [(x['name'].encode('utf-8'), x['character'].encode('utf-8')) for x in cast]
				try: cast = [(x['name'], x['character']) for x in cast]
				except: cast = []

				item = {}
				item = {'content': 'movie', 'title': title, 'originaltitle': title, 'year': year, 'premiered': premiered, 'studio': studio, 'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes,
								'mpaa': mpaa, 'director': director, 'writer': writer, 'cast': cast, 'plot': plot, 'tagline': tagline, 'code': tmdb, 'imdb': imdb, 'tmdb': tmdb, 'tvdb': '0', 'poster': poster,
								'poster2': '0', 'poster3': '0', 'banner': '0', 'fanart': fanart, 'fanart2': '0', 'fanart3': '0', 'clearlogo': '0', 'clearart': '0', 'landscape': fanart, 'metacache': False, 'next': next}
				meta = {}
				meta = {'imdb': imdb, 'tmdb': tmdb, 'tvdb': '0', 'lang': self.lang, 'user': self.tmdb_key, 'item': item}

				# fanart_thread = threading.Thread
				if self.disable_fanarttv != 'true':
					from resources.lib.indexers import fanarttv
					extended_art = fanarttv.get_tvshow_art(tvdb)

					if extended_art is not None:
						item.update(extended_art)
						meta.update(item)

				self.list.append(item)
				self.meta.append(meta)
				metacache.insert(self.meta)
			except:
				pass
		return self.list


	def tmdb_art(self, tmdb):
		if (self.tmdb_key == '') or (tmdb == '0' or tmdb is None):
			return None

		art3 = self.get_request(self.tmdb_art_link % tmdb)
		if art3 is None:
			return None

		try:
			poster3 = art3['posters']
			poster3 = [(x['width'], x['file_path']) for x in poster3]
			poster3 = [x[1] for x in poster3]
			poster3 = self.tmdb_poster + poster3[0]
		except:
			poster3 = '0'

		try:
			fanart3 = art3['backdrops']
			fanart3 = [(x['width'], x['file_path']) for x in fanart3]
			fanart3 = [x[1] for x in fanart3]
			fanart3 = self.tmdb_fanart + fanart3[0]
		except:
			fanart3 = '0'

		extended_art = {'extended': True, 'poster3': poster3, 'fanart3': fanart3}
		return extended_art