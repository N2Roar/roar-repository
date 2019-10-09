# -*- coding: utf-8 -*-

"""
	Venom
"""

import re, datetime
import requests
import threading
from time import sleep

from resources.lib.modules import control, cache
from resources.lib.modules import metacache
from resources.lib.modules import log_utils



class Movies:
	def __init__(self):
		self.list = []
		self.meta = []
		self.disable_fanarttv = control.setting('disable.fanarttv')

		self.datetime = (datetime.datetime.utcnow() - datetime.timedelta(hours = 5))

		self.lang = control.apiLanguage()['trakt']

		self.tmdb_key = control.setting('tm.user')
		if self.tmdb_key == '' or self.tmdb_key is None:
			self.tmdb_key = '3320855e65a9758297fec4f7c9717698'

		self.tmdb_link = 'http://api.themoviedb.org'
		# self.tmdb_poster = 'http://image.tmdb.org/t/p/w500'
		self.tmdb_poster = 'http://image.tmdb.org/t/p/w300'
		# self.tmdb_fanart = 'http://image.tmdb.org/t/p/original'
		self.tmdb_fanart = 'http://image.tmdb.org/t/p/w1280'

		self.tmdb_info_link = 'http://api.themoviedb.org/3/movie/%s?api_key=%s&language=%s&append_to_response=credits,release_dates' % ('%s', self.tmdb_key, self.lang)
###                                                                             other "append_to_response" options                             external_ids,alternative_titles,videos,images

		self.tmdb_art_link = 'http://api.themoviedb.org/3/movie/%s/images?api_key=%s&include_image_language=en,%s,null' % ('%s', self.tmdb_key, self.lang)

		self.tmdb_credits_link = 'https://api.themoviedb.org/3/movie/%s/credits?api_key=%s' % ('%s', self.tmdb_key)


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
			sleep(int(throttleTime) + 1)
			return self.get_request(url)
		else:
			log_utils.log('Get request failed to TMDB URL: %s' % url, __name__, log_utils.LOGDEBUG)
			log_utils.log('TMDB Response: %s' % response.text, __name__, log_utils.LOGDEBUG)
			return None


	def tmdb_list(self, url):
		next = ''
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
			next = '%s&page=%s' % (url.split('&page=', 1)[0], page+1)
		except:
			next = ''

		for item in items:
			try:
				title = (item.get('title')).encode('utf-8')
			except:
				title = item.get('title')

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

			if self.disable_fanarttv != 'true':
				fanart_thread = threading.Thread
				imdb = None
				fanart_thread = fanart_thread(target=self.get_fanarttv_art, args=(imdb, tmdb),)
				fanart_thread.run()

##--TMDb additional info
			url = self.tmdb_info_link % tmdb
			item = self.get_request(url)

			imdb = item.get('imdb_id', '0')
			if imdb == '' or imdb is None or imdb == 'None':
				imdb = '0'

			# try:
				# studio = item.get('production_companies', None)[0]['name']
			# except:
				# studio = '0'

			genre = []
			for i in item['genres']:
				genre.append(i.get('name'))
			if genre == []: genre = 'NA'

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
			except:
				mpaa = '0'

			credits = item['credits']
			director = writer = '0'
			for person in credits['crew']:
				if 'Director' in person['job']:
					director = ', '.join([director['name'].encode('utf-8') for director in credits['crew'] if director['job'].lower() == 'director'])
				if person['job'] in ['Writer', 'Screenplay', 'Author', 'Novel']:
					writer = ', '.join([writer['name'].encode('utf-8') for writer in credits['crew'] if writer['job'].lower() in ['writer', 'screenplay', 'author', 'novel']])

			castandart = []
			for person in item['credits']['cast']:
				try:
					try:
						castandart.append({'name': person['name'].encode('utf-8'), 'role': person['character'].encode('utf-8'), 'thumbnail': ((self.tmdb_poster + person.get('profile_path')) if person.get('profile_path') is not None else '0')})
					except:
						castandart.append({'name': person['name'], 'role': person['character'], 'thumbnail': ((self.tmdb_poster + person.get('profile_path')) if person.get('profile_path') is not None else '0')})
				except:
					castandart = []

			item = {}
			item = {'content': 'movie', 'title': title, 'originaltitle': originaltitle, 'year': year, 'premiered': premiered,
						'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes, 'mpaa': mpaa, 'director': director, 'writer': writer,
						'castandart': castandart, 'plot': plot, 'tagline': tagline, 'code': tmdb, 'imdb': imdb, 'tmdb': tmdb, 'tvdb': '0', 'poster': poster,
						'poster2': '0', 'poster3': '0', 'banner': '0', 'fanart': fanart, 'fanart2': '0', 'fanart3': '0', 'clearlogo': '0', 'clearart': '0',
						'landscape': fanart, 'metacache': False, 'next': next}
			meta = {}
			meta = {'imdb': imdb, 'tmdb': tmdb, 'tvdb': '0', 'lang': self.lang, 'user': self.tmdb_key, 'item': item}

			if self.disable_fanarttv != 'true':
				while fanart_thread.is_alive():
					sleep(.2)
				extended_art = self.fanarttv
				if extended_art is not None:
					item.update(extended_art)
					meta.update(item)

			item = dict((k,v) for k, v in item.iteritems() if v != '0')
			self.list.append(item)

			if 'next' in meta.get('item'):
				del meta['item']['next']

			self.meta.append(meta)
			metacache.insert(self.meta)

		return self.list


	def tmdb_collections_list(self, url):
		next = ''
		try:
			result = self.get_request(url)
			if '/3/' in url:
				items = result['items']
			else:
				items = result['results']
		except:
			return

		# log_utils.log('len items = %s' % str(len(items)), __name__, log_utils.LOGDEBUG)

		try:
			page = int(result['page'])
			total = int(result['total_pages'])
			if page >= total:
				raise Exception()
			if 'page=' not in url:
				raise Exception()
			next = '%s&page=%s' % (url.split('&page=', 1)[0], page+1)
		except:
			next = ''

		for item in items:
			try:
				media_type = item.get('media_type')
				if media_type == 'tv':
					raise Exception()

				try:
					title = item.get('title').encode('utf-8')
				except:
					title = item.get('title')

				try: 
					originaltitle = item.get('original_title').encode('utf-8')
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

				if self.disable_fanarttv != 'true':
					fanart_thread = threading.Thread
					imdb = None
					fanart_thread = fanart_thread(target=self.get_fanarttv_art, args=(imdb, tmdb),)
					# fanart_thread = fanart_thread(target=cache.get(self.get_fanarttv_art, 168, imdb, tmdb),,)
					fanart_thread.run()

##--TMDb additional info
				url = self.tmdb_info_link % tmdb
				item = self.get_request(url)

				imdb = item.get('imdb_id', '0')
				if imdb == '' or imdb is None or imdb == 'None':
					imdb = '0'

				# try:
					# studio = item.get('production_companies', None)[0]['name']
				# except:
					# studio = '0'

				genre = []
				for i in item['genres']:
					genre.append(i.get('name'))
				if genre == []: genre = 'NA'

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
				except:
					mpaa = '0'

				credits = item['credits']
				director = writer = '0'
				for person in credits['crew']:
					if 'Director' in person['job']:
						director = ', '.join([director['name'].encode('utf-8') for director in credits['crew'] if director['job'].lower() == 'director'])
					if person['job'] in ['Writer', 'Screenplay', 'Author', 'Novel']:
						writer = ', '.join([writer['name'].encode('utf-8') for writer in credits['crew'] if writer['job'].lower() in ['writer', 'screenplay', 'author', 'novel']])

				castandart = []
				for person in item['credits']['cast']:
					try:
						try:
							castandart.append({'name': person['name'].encode('utf-8'), 'role': person['character'].encode('utf-8'), 'thumbnail': ((self.tmdb_poster + person.get('profile_path')) if person.get('profile_path') is not None else '0')})
						except:
							castandart.append({'name': person['name'], 'role': person['character'], 'thumbnail': ((self.tmdb_poster + person.get('profile_path')) if person.get('profile_path') is not None else '0')})
					except:
						castandart = []

				item = {}
				item = {'content': 'movie', 'title': title, 'originaltitle': originaltitle, 'year': year, 'premiered': premiered,
							'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes, 'mpaa': mpaa, 'director': director, 'writer': writer,
							'castandart': castandart, 'plot': plot, 'tagline': tagline, 'code': tmdb, 'imdb': imdb, 'tmdb': tmdb, 'tvdb': '0', 'poster': poster,
							'poster2': '0', 'poster3': '0', 'banner': '0', 'fanart': fanart, 'fanart2': '0', 'fanart3': '0', 'clearlogo': '0', 'clearart': '0',
							'landscape': fanart, 'metacache': False, 'next': next}
				meta = {}
				meta = {'imdb': imdb, 'tmdb': tmdb, 'tvdb': '0', 'lang': self.lang, 'user': self.tmdb_key, 'item': item}

				# if self.disable_fanarttv != 'true':
					# from resources.lib.indexers import fanarttv
					# extended_art = cache.get(fanarttv.get_movie_art, 168, imdb, tmdb)
					# if extended_art is not None:
						# item.update(extended_art)
						# meta.update(item)

				if self.disable_fanarttv != 'true':
					while fanart_thread.is_alive():
						sleep(.2)
					extended_art = self.fanarttv
					if extended_art is not None:
						item.update(extended_art)
						meta.update(item)

				item = dict((k,v) for k, v in item.iteritems() if v != '0')
				self.list.append(item)

				if 'next' in meta.get('item'):
					del meta['item']['next']

				self.meta.append(meta)
				metacache.insert(self.meta)
			except:
				pass
		return self.list


	def tmdb_userlist(self, url):
		next = ''
		list = []
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
			next = '%s&page=%s' % (url.split('&page=', 1)[0], page+1)
		except:
			next = ''

		for item in items:
			media_type = item.get('list_type')
			name = item.get('name')
			list_id =  item.get('id')
			# url = 'https://api.themoviedb.org/4/list/%s?api_key=%s&sort_by=%s%s&page=1' % (list_id, self.tmdb_key, tmdb_sort, tmdb_sort_order)
			url = 'https://api.themoviedb.org/4/list/%s?api_key=%s&sort_by=original_order.asc&page=1' % (list_id, self.tmdb_key)
			item = {}
			item = {'media_type': media_type, 'name': name, 'list_id': list_id, 'url': url, 'context': url, 'next': next}

			list.append(item)
		return list


	def tmdb_get_details(self, tmdb, imdb):
		item = self.get_request(self.tmdb_info_link % tmdb)
		if item is None:
			item = self.get_request(self.tmdb_info_link % imdb)
		return item


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


	def tmdb_credits(self, tmdb):
		if (self.tmdb_key == '') or (tmdb == '0' or tmdb is None):
			return None
		people = self.get_request(self.tmdb_credits_link % tmdb)
		if people is None:
			return None
		return people


	def get_fanarttv_art(self, imdb=None, tmdb=None):
		from resources.lib.indexers import fanarttv
		self.fanarttv = fanarttv.get_movie_art(imdb, tmdb)


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
			sleep(int(throttleTime) + 1)
			return self.get_request(url)
		else:
			log_utils.log('Get request failed to TMDB URL: %s' % url, __name__, log_utils.LOGDEBUG)
			log_utils.log('TMDB Response: %s' % response.text, __name__, log_utils.LOGDEBUG)
			return None


	def tmdb_list(self, url):
		next = ''
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
			next = '%s&page=%s' % (url.split('&page=', 1)[0], page+1)
		except:
			next = ''

		for item in items:
			try:
				try:
					title = item.get('name').encode('utf-8')
				except:
					title = item.get('name')

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

				tvdb = str(item.get('external_ids').get('tvdb_id', '0'))
				if tvdb == '' or tvdb is None or tvdb == 'None':
					tvdb = '0'

				imdb = item.get('external_ids').get('imdb_id', '0')
				if imdb == '' or imdb is None or imdb == 'None':
					imdb = '0'

				genre = []
				for i in item['genres']:
					genre.append(i.get('name'))
				if genre == []: genre = 'NA'

				duration = str(item.get('episode_run_time', '0')[0])

				try:
					mpaa = [i['rating'] for i in item['content_ratings']['results'] if i['iso_3166_1'] == 'US'][0]
				except: 
					try:
						mpaa = item['content_ratings'][0]['rating']
					except:
						mpaa = 'NR'

				try:
					studio = item.get('networks', None)[0]['name']
				except:
					studio = '0'

				credits = item['credits']
				director = writer = '0'
				for person in credits['crew']:
					if 'Director' in person['job']:
						director = ', '.join([director['name'].encode('utf-8') for director in credits['crew'] if director['job'].lower() == 'director'])
					if person['job'] in ['Writer', 'Screenplay', 'Author', 'Novel']:
						writer = ', '.join([writer['name'].encode('utf-8') for writer in credits['crew'] if writer['job'].lower() in ['writer', 'screenplay', 'author', 'novel']])

				castandart = []
				for person in item['credits']['cast']:
					try:
						try:
							castandart.append({'name': person['name'].encode('utf-8'), 'role': person['character'].encode('utf-8'), 'thumbnail': ((self.tmdb_poster + person.get('profile_path')) if person.get('profile_path') is not None else '0')})
						except:
							castandart.append({'name': person['name'], 'role': person['character'], 'thumbnail': ((self.tmdb_poster + person.get('profile_path')) if person.get('profile_path') is not None else '0')})
					except:
						castandart = []

				item = {}
				item = {'content': 'tvshow', 'title': title, 'originaltitle': title, 'year': year, 'premiered': premiered, 'studio': studio, 'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes,
								'mpaa': mpaa, 'director': director, 'writer': writer, 'castandart': castandart, 'plot': plot, 'tagline': tagline, 'code': tmdb, 'imdb': imdb, 'tmdb': tmdb, 'tvdb': tvdb, 'poster': poster,
								'poster2': '0', 'banner': '0', 'banner2': '0', 'fanart': fanart, 'fanart2': '0', 'clearlogo': '0', 'clearart': '0', 'landscape': fanart, 'metacache': False, 'next': next}

				meta = {}
				meta = {'tmdb': tmdb, 'imdb': imdb, 'tvdb': tvdb, 'lang': self.lang, 'user': self.tmdb_key, 'item': item}

				if self.disable_fanarttv != 'true':
					from resources.lib.indexers import fanarttv
					extended_art = cache.get(fanarttv.get_tvshow_art, 168, tvdb)
					if extended_art is not None:
						item.update(extended_art)
						meta.update(item)

				item = dict((k,v) for k, v in item.iteritems() if v != '0')
				self.list.append(item)

				if 'next' in meta.get('item'):
					del meta['item']['next']

				self.meta.append(meta)
				metacache.insert(self.meta)
			except:
				pass
		return self.list


	def tmdb_collections_list(self, url):
		next = ''
		try:
			result = self.get_request(url)
			if '/3/' in url:
				items = result['items']
			else:
				items = result['results']
		except:
			return

		# log_utils.log('len items = %s' % str(len(items)), __name__, log_utils.LOGDEBUG)

		try:
			page = int(result['page'])
			total = int(result['total_pages'])
			if page >= total:
				raise Exception()
			if 'page=' not in url:
				raise Exception()
			next = '%s&page=%s' % (url.split('&page=', 1)[0], page+1)
		except:
			next = ''

		for item in items:
			try:
				media_type = item.get('media_type')
				if media_type == 'movie':
					raise Exception()

				try:
					title = item.get('name').encode('utf-8')
				except:
					title = item.get('name')

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

				tvdb = str(item.get('external_ids').get('tvdb_id', '0'))
				if tvdb == '' or tvdb is None or tvdb == 'None':
					tvdb = '0'

				imdb = item.get('external_ids').get('imdb_id', '0')
				if imdb == '' or imdb is None or imdb == 'None':
					imdb = '0'

				genre = []
				for i in item['genres']:
					genre.append(i.get('name'))
				if genre == []: genre = 'NA'

				duration = str(item.get('episode_run_time', '0'))

				try:
					mpaa = [i['rating'] for i in item['content_ratings']['results'] if i['iso_3166_1'] == 'US'][0]
				except: 
					try:
						mpaa = item['content_ratings'][0]['rating']
					except: mpaa = 'NR'

				try:
					studio = item.get('networks', None)[0]['name']
				except:
					studio = '0'

				credits = item['credits']
				director = writer = '0'
				for person in credits['crew']:
					if 'Director' in person['job']:
						director = ', '.join([director['name'].encode('utf-8') for director in credits['crew'] if director['job'].lower() == 'director'])
					if person['job'] in ['Writer', 'Screenplay', 'Author', 'Novel']:
						writer = ', '.join([writer['name'].encode('utf-8') for writer in credits['crew'] if writer['job'].lower() in ['writer', 'screenplay', 'author', 'novel']])

				castandart = []
				for person in item['credits']['cast']:
					try:
						try:
							castandart.append({'name': person['name'].encode('utf-8'), 'role': person['character'].encode('utf-8'), 'thumbnail': ((self.tmdb_poster + person.get('profile_path')) if person.get('profile_path') is not None else '0')})
						except:
							castandart.append({'name': person['name'], 'role': person['character'], 'thumbnail': ((self.tmdb_poster + person.get('profile_path')) if person.get('profile_path') is not None else '0')})
					except:
						castandart = []

				item = {}
				item = {'content': 'movie', 'title': title, 'originaltitle': title, 'year': year, 'premiered': premiered, 'studio': studio, 'genre': genre, 'duration': duration, 'rating': rating, 'votes': votes,
								'mpaa': mpaa, 'director': director, 'writer': writer, 'castandart': castandart, 'plot': plot, 'tagline': tagline, 'code': tmdb, 'imdb': imdb, 'tmdb': tmdb, 'tvdb': '0', 'poster': poster,
								'poster2': '0', 'poster3': '0', 'banner': '0', 'fanart': fanart, 'fanart2': '0', 'fanart3': '0', 'clearlogo': '0', 'clearart': '0', 'landscape': fanart, 'metacache': False, 'next': next}
				meta = {}
				meta = {'imdb': imdb, 'tmdb': tmdb, 'tvdb': '0', 'lang': self.lang, 'user': self.tmdb_key, 'item': item}

				if self.disable_fanarttv != 'true':
					from resources.lib.indexers import fanarttv
					extended_art = cache.get(fanarttv.get_tvshow_art, 168, tvdb)
					if extended_art is not None:
						item.update(extended_art)
						meta.update(item)

				item = dict((k,v) for k, v in item.iteritems() if v != '0')
				self.list.append(item)

				if 'next' in meta.get('item'):
					del meta['item']['next']

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


	def get_fanarttv_art(self, imdb=None, tmdb=None):
		from resources.lib.indexers import fanarttv
		self.fanarttv = fanarttv.get_movie_art(imdb, tmdb)


class Auth:
	def __init__(self):
		self.auth_base_link = 'https://api.themoviedb.org/3/authentication'
		self.tmdb_key = control.setting('tm.user')
		if self.tmdb_key == '' or self.tmdb_key is None:
			self.tmdb_key = '3320855e65a9758297fec4f7c9717698'


	def create_session_id(self):
		try:
			if control.setting('tmdb.username') == '' or control.setting('tmdb.password') == '':
				control.notification(title='default', message='TMDb Account info missing', icon='ERROR')
				raise Exception()

			url = self.auth_base_link + '/token/new?api_key=%s' % self.tmdb_key
			result = requests.get(url).json()
			token = result.get('request_token').encode('utf-8')

			url2 = self.auth_base_link + '/token/validate_with_login?api_key=%s' % self.tmdb_key
			post2 = {"username": "%s" % control.setting('tmdb.username'),
							"password": "%s" % control.setting('tmdb.password'),
							"request_token": "%s" % token}
			result2 = requests.post(url2, data=post2).json()

			url3 = self.auth_base_link + '/session/new?api_key=%s' % self.tmdb_key
			post3 = {"request_token": "%s" % token}
			result3 = requests.post(url3, data=post3).json()

			if result3.get('success') is True:
				session_id = result3.get('session_id')
				control.setSetting('tmdb.session_id', session_id)
				control.notification(title='default', message='TMDb Successfully Authorized', icon='default')
			else:
				control.notification(title='default', message='TMDb Authorization FAILED', icon='ERROR')

		except:
			pass


	def revoke_session_id(self):
		try:
			url = self.auth_base_link + '/session?api_key=%s' % self.tmdb_key
			post = {"session_id": "%s" % control.setting('tmdb.session_id')}

			result = requests.delete(url, data=post).json()

			if result.get('success') is True:
				control.setSetting('tmdb.session_id', '')
				control.notification(title='default', message='TMDb session_id successfully deleted', icon='default')
			else:
				control.notification(title='default', message='TMDb session_id deletion FAILED', icon='ERROR')
		except:
			pass

