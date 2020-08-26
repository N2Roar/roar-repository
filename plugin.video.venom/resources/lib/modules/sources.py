# -*- coding: utf-8 -*-

"""
	Venom Add-on
"""

from datetime import datetime, timedelta
import json
import re
# Import _strptime to workaround python 2 bug with threads
import _strptime
import sys
import time

try:
	from urllib import quote_plus, unquote
	from urlparse import parse_qsl
except:
	from urllib.parse import quote_plus, parse_qsl, unquote

from resources.lib.modules import cleantitle
from resources.lib.modules import client
from resources.lib.modules import control
from resources.lib.modules import debrid
from resources.lib.modules import log_utils
from resources.lib.modules import metacache
from resources.lib.modules import premiumize
from resources.lib.modules import providerscache
from resources.lib.modules import realdebrid
from resources.lib.modules import source_utils
from resources.lib.modules import trakt
from resources.lib.modules import workers

try:
	from sqlite3 import dbapi2 as database
except:
	from pysqlite2 import dbapi2 as database
try:
	import resolveurl
except:
	pass


class Sources:
	def __init__(self):
		self.time = datetime.now()
		self.single_expiry = timedelta(hours=6)
		self.season_expiry = timedelta(hours=48)
		self.show_expiry = timedelta(hours=48)
		self.getConstants()
		self.sources = []
		self.uncached_sources = []
		self.sourceFile = control.providercacheFile
		self.enablePacks = control.setting('enable.season.packs') == 'true'
		self.dev_mode = control.setting('dev.mode.enable') == 'true'
		self.dev_disable_single = control.setting('dev.disable.single') == 'true'
		# self.dev_disable_single_filter = control.setting('dev.disable.single.filter') == 'true'
		self.dev_disable_season_packs = control.setting('dev.disable.season.packs') == 'true'
		self.dev_disable_season_filter = control.setting('dev.disable.season.filter') == 'true'
		self.dev_disable_show_packs = control.setting('dev.disable.show.packs') == 'true'
		self.dev_disable_show_filter = control.setting('dev.disable.show.filter') == 'true'


	def timeIt(func):
		import time
		fnc_name = func.__name__
		def wrap(*args, **kwargs):
			started_at = time.time()
			result = func(*args, **kwargs)
			log_utils.log('%s.%s = %s' % (__name__ , fnc_name, time.time() - started_at), log_utils.LOGDEBUG)
			return result
		return wrap


	def profileIt(func):
		import cProfile, pstats
		from io import BytesIO as StringIO
		def wrapper(*args, **kwargs):
			LOGPATH = control.transPath('special://logpath/')
			datafn = func.__name__ + ".profile" # Name the data file sensibly
			log_file = control.joinPath(LOGPATH, datafn)
			prof = cProfile.Profile()
			retval = prof.runcall(func, *args, **kwargs)
			s = StringIO()
			# sortby = 'cumulative'
 			sortby = 'tottime'
			ps = pstats.Stats(prof, stream=s).sort_stats(sortby)
			ps.print_stats()
			with open(log_file, 'a') as perf_file:
				perf_file.write(s.getvalue())
			return retval
		return wrapper


	def play(self, title, year, imdb, tvdb, season, episode, tvshowtitle, premiered, meta, select, rescrape=None):
		control.busy()
		try:
			control.window.clearProperty(self.metaProperty)
			control.window.setProperty(self.metaProperty, meta)
			control.window.clearProperty(self.seasonProperty)
			control.window.setProperty(self.seasonProperty, season)
			control.window.clearProperty(self.episodeProperty)
			control.window.setProperty(self.episodeProperty, episode)
			control.window.clearProperty(self.titleProperty)
			control.window.setProperty(self.titleProperty, title)
			control.window.clearProperty(self.imdbProperty)
			control.window.setProperty(self.imdbProperty, imdb)
			control.window.clearProperty(self.tvdbProperty)
			control.window.setProperty(self.tvdbProperty, tvdb)

			url = None
			self.mediatype = 'movie'

			external_caller = 'plugin.video.venom' not in control.infoLabel('Container.PluginName')
			isSTRM = control.infoLabel('ListItem.FileExtension') == 'strm'

			#check IMDB for year since TMDB and Trakt differ on a ratio of 1 in 20 and year is off by 1 and some meta titles mismatch
			if tvshowtitle is None:
				year, title = self.movie_chk_imdb(imdb, title, year)

			# fix incorect year passed from TMDBHelper. Need series premiered not variable season premiered.
			# TMDBHelper added "{showyear}" for player files 7/29/20. Check on removing this
			if external_caller and tvshowtitle is not None:
				year = self.tmdbhelper_fix(imdb, year)

			# get "total_season" to satisfy showPack scrapers. 1st=passed meta, 2nd=matacache check, 3rd=trakt.getSeasons() request
			# also get "is_airing" status of season for showPack scrapers. 1st=passed meta, 2nd=matacache check, 3rd=tvdb v1 xml request
			if tvshowtitle is not None:
				self.mediatype = 'episode'
				self.total_seasons, self.is_airing = self.get_season_info(imdb, tvdb, meta, season)

			if rescrape :
				self.clr_item_providers(title, year, imdb, tvdb, season, episode, tvshowtitle, premiered)

			if isSTRM or external_caller:
				items = self.getSources(title, year, imdb, tvdb, season, episode, tvshowtitle, premiered)
				# items, uncached_items = self.getSources(title, year, imdb, tvdb, season, episode, tvshowtitle, premiered)
			else:
				items = providerscache.get(self.getSources, 48, title, year, imdb, tvdb, season, episode, tvshowtitle, premiered)
				# items, uncached_items = providerscache.get(self.getSources, 48, title, year, imdb, tvdb, season, episode, tvshowtitle, premiered)

			if not items:
				self.url = url
				return self.errorForSources()

			if select is None:
				if episode is not None and control.setting('enable.upnext') == 'true':
					select = '2'
				else:
					select = control.setting('hosts.mode')
					if control.condVisibility("Window.IsActive(script.extendedinfo-DialogVideoInfo-Netflix.xml)") or \
							control.condVisibility("Window.IsActive(script.extendedinfo-DialogVideoInfo-Estuary.xml)") or \
							control.condVisibility("Window.IsActive(script.extendedinfo-DialogVideoInfo-Aura.xml)") or \
							control.condVisibility("Window.IsActive(script.extendedinfo-DialogVideoInfo.xml)") and select == '1':
						select = '0'
			else:
				select = select

			title = tvshowtitle if tvshowtitle is not None else title

			if len(items) > 0:
				if select == '1' and 'plugin' in control.infoLabel('Container.PluginName'):
					control.window.clearProperty(self.itemProperty)
					control.window.setProperty(self.itemProperty, json.dumps(items))
					control.sleep(200)
					control.hide()
					return control.execute('Container.Update(%s?action=addItem&title=%s)' % (sys.argv[0], quote_plus(title)))
				elif select == '0' or select == '1':
					url = self.sourcesDialog(items)
				else:
					url = self.sourcesAutoPlay(items)

			if url == 'close://' or url is None:
				self.url = url
				return self.errorForSources()

			try:
				meta = json.loads(unquote(meta.replace('%22', '\\"')))
			except:
				pass

			from resources.lib.modules import player
			control.sleep(200) # added 5/14
			control.hide()
			player.Player().play_source(title, year, season, episode, imdb, tvdb, url, meta, select)

		except:
			log_utils.error()
			pass


	# @timeIt
	def addItem(self, title):
		control.sleep(200)
		control.hide()
		def sourcesDirMeta(metadata):
			if not metadata:
				return metadata
			allowed = ['poster', 'season_poster', 'fanart', 'thumb', 'title', 'year', 'tvshowtitle', 'season', 'episode']
			return {k: v for k, v in metadata.iteritems() if k in allowed}

		control.playlist.clear()
		items = control.window.getProperty(self.itemProperty)
		items = json.loads(items)

		if not items:
			control.sleep(200) # added 5/14
			control.hide()
			sys.exit()

		meta = json.loads(unquote(control.window.getProperty(self.metaProperty).replace('%22', '\\"')))
		meta = sourcesDirMeta(meta)

		sysaddon = sys.argv[0]
		syshandle = int(sys.argv[1])

		downloads = True if control.setting('downloads') == 'true' and (control.setting(
			'movie.download.path') != '' or control.setting('tv.download.path') != '') else False

		systitle = sysname = quote_plus(title)

		poster = meta.get('poster') or control.addonPoster()
		if 'tvshowtitle' in meta and 'season' in meta and 'episode' in meta:
			poster = meta.get('season_poster') or poster or control.addonPoster()
			sysname += quote_plus(' S%02dE%02d' % (int(meta['season']), int(meta['episode'])))
		elif 'year' in meta:
			sysname += quote_plus(' (%s)' % meta['year'])

		fanart = meta.get('fanart')
		if control.setting('fanart') != 'true':
			fanart = '0'

		sysimage = quote_plus(poster.encode('utf-8'))
		downloadMenu = control.lang(32403)

		multiline = control.setting('sourcelist.multiline')

		for i in range(len(items)):
			try:
				if multiline == 'true':
					label = str(items[i]['multiline_label'])
				else:
					label = str(items[i]['label'])

				syssource = quote_plus(json.dumps([items[i]]))
				sysurl = '%s?action=playItem&title=%s&source=%s' % (sysaddon, systitle, syssource)

				cm = []
				if downloads:
					if not 'uncached' in items[i]['source']:
						try:
							new_sysname = quote_plus(items[i]['name'])
						except:
							new_sysname = sysname
							pass
						cm.append((downloadMenu, 'RunPlugin(%s?action=download&name=%s&image=%s&source=%s&caller=sources)' %
								(sysaddon, new_sysname, sysimage, syssource)))

				if 'package' in items[i]:
					if not 'uncached' in items[i]['source']:
						cm.append(('Browse Debrid Pack', 'RunPlugin(%s?action=showDebridPack&caller=%s&name=%s&url=%s&source=%s)' %
								(sysaddon, quote_plus(items[i]['debrid']), quote_plus(items[i]['name']), quote_plus(items[i]['url']), quote_plus(items[i]['hash']))))

				if 'uncached' in items[i]['source']:
					seeders = int(items[i]['seeders'])
					if seeders > 0:
						d = self.debrid_abv(items[i]['debrid'])
						cm.append(('Cache to %s Cloud (seeders=%s)' % (d, seeders), 'RunPlugin(%s?action=cacheTorrent&caller=%s&url=%s)' %
								(sysaddon, quote_plus(items[i]['debrid']), quote_plus(items[i]['url']))))

				if control.setting('enable.resquality.icons') == 'true':
					quality = items[i]['quality']
					thumb = '%s%s' % (quality, '.png')
					artPath = control.artPath()
					thumb = control.joinPath(artPath, thumb) if artPath else ''
				else:
					thumb = meta.get('thumb')
					thumb = thumb or poster or fanart or control.addonThumb()

				item = control.item(label=label)
				item.setArt({'icon': thumb, 'thumb': thumb, 'poster': poster, 'fanart': fanart})
				video_streaminfo = {'codec': 'h264'}
				item.addStreamInfo('video', video_streaminfo)
				item.addContextMenuItems(cm)

				# item.setProperty('IsPlayable', 'true') # test
				item.setProperty('IsPlayable', 'false')

				item.setInfo(type='video', infoLabels=control.metadataClean(meta))
				control.addItem(handle=syshandle, url=sysurl, listitem=item, isFolder=False)
			except:
				log_utils.error()
				pass

		control.content(syshandle, 'files')
		control.directory(syshandle, cacheToDisc=True)


	def playItem(self, title, source):
		try:
			meta = json.loads(unquote(control.window.getProperty(self.metaProperty).replace('%22', '\\"')))
			year = meta['year'] if 'year' in meta else None
			if 'tvshowtitle' in meta:
				year = meta['tvshowyear'] if 'tvshowyear' in meta else year #year was changed to year of premiered in episodes module so can't use that, need original shows year.

			season = meta['season'] if 'season' in meta else None
			episode = meta['episode'] if 'episode' in meta else None

			imdb = meta['imdb'] if 'imdb' in meta else None
			tvdb = meta['tvdb'] if 'tvdb' in meta else None

			next = []
			prev = []
			total = []

			for i in range(1, 1000):
				try:
					u = control.infoLabel('ListItem(%s).FolderPath' % str(i))
					if u in total:
						raise Exception()
					total.append(u)
					u = dict(parse_qsl(u.replace('?', '')))
					u = json.loads(u['source'])[0]
					next.append(u)
				except:
					break

			for i in range(-1000, 0)[::-1]:
				try:
					u = control.infoLabel('ListItem(%s).FolderPath' % str(i))
					if u in total:
						raise Exception()
					total.append(u)
					u = dict(parse_qsl(u.replace('?', '')))
					u = json.loads(u['source'])[0]
					prev.append(u)
				except:
					break

			items = json.loads(source)

			# items = [i for i in items + next + prev][:40]
			items = [i for i in items + next + prev][:1000]

			header = control.addonInfo('name')
			header2 = header.upper()

			progressDialog = control.progressDialog if control.setting('progress.dialog') == '0' else control.progressDialogBG
			progressDialog.create(header, '')
			progressDialog.update(0)

			block = None

			for i in range(len(items)):
				try:
					try:
						if progressDialog.iscanceled():
							break
						progressDialog.update(int((100 / float(len(items))) * i), str(items[i]['label']), str(' '))
						# progressDialog.update(int((100 / float(len(items))) * i), str(items[i]['label']).replace('\n    ', ' | '))
					except:
						progressDialog.update(int((100 / float(len(items))) * i), str(header2), str(items[i]['label']))

					if items[i]['source'] == block:
						raise Exception()

					w = workers.Thread(self.sourcesResolve, items[i])
					w.start()

					if items[i].get('source') in self.hostcapDict:
						offset = 60 * 2
					elif items[i].get('source') == 'torrent':
						offset = float('inf')
					else:
						offset = 0

					m = ''
					for x in range(3600):
						try:
							if control.monitor.abortRequested():
								return sys.exit()
							if progressDialog.iscanceled():
								return progressDialog.close()
						except:
							pass

						k = control.condVisibility('Window.IsActive(virtualkeyboard)')
						if k:
							m += '1'
							m = m[-1]
						if (not w.is_alive() or x > 30 + offset) and not k:
							break
						k = control.condVisibility('Window.IsActive(yesnoDialog)')
						if k:
							m += '1'
							m = m[-1]
						if (not w.is_alive() or x > 30 + offset) and not k:
							break
						time.sleep(0.5)

					for x in range(30):
						try:
							if control.monitor.abortRequested():
								return sys.exit()
							if progressDialog.iscanceled():
								return progressDialog.close()
						except:
							pass

						if m == '':
							break
						if not w.is_alive():
							break
						time.sleep(0.5)

					if w.is_alive():
						block = items[i]['source']

					if self.url is None:
						raise Exception()

					try:
						progressDialog.close()
					except:
						pass

					control.sleep(200)
					control.execute('Dialog.Close(virtualkeyboard)')
					control.execute('Dialog.Close(yesnoDialog)')

					from resources.lib.modules import player
					control.sleep(200) # added 5/14
					control.hide()
					player.Player().play_source(title, year, season, episode, imdb, tvdb, self.url, meta, select='1')

					return self.url
				except:
					log_utils.error()
					pass

			try:
				progressDialog.close()
			except:
				pass

			self.errorForSources()
		except:
			log_utils.error()
			pass


	# @timeIt
	def getSources(self, title, year, imdb, tvdb, season, episode, tvshowtitle, premiered, quality='HD', timeout=30):
		control.sleep(200)
		control.hide()
		progressDialog = control.progressDialog if control.setting(
			'progress.dialog') == '0' else control.progressDialogBG
		progressDialog.create(control.addonInfo('name'), '')
		progressDialog.update(0)
		self.prepareSources()
		sourceDict = self.sourceDict
		progressDialog.update(0, control.lang(32600))

		try:
			meta = json.loads(unquote(control.window.getProperty(self.metaProperty).replace('%22', '\\"')))
			genres = [i.lower() for i in meta.get('genre')]
		except:
			log_utils.error()
			genres = None
			pass

		content = 'movie' if tvshowtitle is None else 'episode'
		if content == 'movie':
			sourceDict = [(i[0], i[1], getattr(i[1], 'movie', None)) for i in sourceDict]
			if not genres:
				genres = trakt.getGenre('movie', 'imdb', imdb)
		else:
			sourceDict = [(i[0], i[1], getattr(i[1], 'tvshow', None)) for i in sourceDict]
			if not genres:
				genres = trakt.getGenre('show', 'tvdb', tvdb)
		sourceDict = [(i[0], i[1], i[2]) for i in sourceDict if not hasattr(i[1], 'genre_filter') or not i[1].genre_filter or any(
								x in i[1].genre_filter for x in genres)]
		sourceDict = [(i[0], i[1]) for i in sourceDict if i[2] is not None]
		language = self.getLanguage()
		sourceDict = [(i[0], i[1], i[1].language) for i in sourceDict]
		sourceDict = [(i[0], i[1]) for i in sourceDict if any(x in i[2] for x in language)]

		try:
			sourceDict = [(i[0], i[1], control.setting('provider.' + i[0])) for i in sourceDict]
		except:
			sourceDict = [(i[0], i[1], 'true') for i in sourceDict]
		sourceDict = [(i[0], i[1]) for i in sourceDict if i[2] != 'false']

		if control.setting('cf.disable') == 'true':
			sourceDict = [(i[0], i[1]) for i in sourceDict if not any(x in i[0] for x in self.sourcecfDict)]
		sourceDict = [(i[0], i[1], i[1].priority) for i in sourceDict]
		sourceDict = sorted(sourceDict, key=lambda i: i[2]) # sorted by scraper priority num

		threads = []
		if content == 'movie':
			title = self.getTitle(title)
			localtitle = self.getLocalTitle(title, imdb, tvdb, content)
			aliases = self.getAliasTitles(imdb, localtitle, content)
			for i in sourceDict:
				threads.append(workers.Thread(self.getMovieSource, title, localtitle, aliases, year, imdb, i[0], i[1]))
		else:
			tvshowtitle = self.getTitle(tvshowtitle)
			localtvshowtitle = self.getLocalTitle(tvshowtitle, imdb, tvdb, content)
			aliases = self.getAliasTitles(imdb, localtvshowtitle, content)
			for i in sourceDict:
				threads.append(workers.Thread(self.getEpisodeSource, title, year, imdb, tvdb, season,
											episode, tvshowtitle, localtvshowtitle, aliases, premiered, i[0], i[1]))

		s = [i[0] + (i[1],) for i in zip(sourceDict, threads)]
		s = [(i[3].getName(), i[0], i[2]) for i in s]

		mainsourceDict = [i[0] for i in s if i[2] == 0]
		sourcelabelDict = dict([(i[0], i[1].upper()) for i in s])

		[i.start() for i in threads]

		pdpc = control.setting('progress.dialog.prem.color')
		pdpc = control.getColor(pdpc)
		pdfc = control.setting('progress.dialog.free.color')
		pdfc = control.getColor(pdfc)

		string1 = control.lang(32404)
		string2 = control.lang(32405)
		string3 = control.lang(32406)
		string4 = control.lang(32601)
		string5 = control.lang(32602)
		string6 = control.lang(32606) % pdpc
		string7 = control.lang(32607) % pdfc

		try:
			timeout = int(control.setting('scrapers.timeout.1'))
		except:
			pass

		quality = control.setting('hosts.quality')
		if quality == '':
			quality = '0'

		line1 = line2 = line3 = ""

		pre_emp = str(control.setting('preemptive.termination'))
		pre_emp_limit = int(control.setting('preemptive.limit'))
		pre_emp_res = str(control.setting('preemptive.res'))

		source_4k = d_source_4k = 0
		source_1080 = d_source_1080 = 0
		source_720 = d_source_720 = 0
		source_sd = d_source_sd = 0
		total = d_total = 0

		debrid_list = debrid.debrid_resolvers
		debrid_status = debrid.status()

		total_format = '[COLOR %s][B]%s[/B][/COLOR]'
		pdiag_format = ' 4K: %s | 1080p: %s | 720p: %s | SD: %s | %s: %s'.split('|')
		pdiag_bg_format = '4K:%s(%s)|1080p:%s(%s)|720p:%s(%s)|SD:%s(%s)|T:%s(%s)'.split('|')

		for i in range(0, 4 * timeout):
			if pre_emp == 'true':
				if pre_emp_res == '0':
					if (source_4k + d_source_4k) >= pre_emp_limit:
						break
				elif pre_emp_res == '1':
					if (source_1080 + d_source_1080) >= pre_emp_limit:
						break
				elif pre_emp_res == '2':
					if (source_720 + d_source_720) >= pre_emp_limit:
						break
				elif pre_emp_res == '3':
					if (source_sd + d_source_sd) >= pre_emp_limit:
						break
				else:
					if (source_sd + d_source_sd) >= pre_emp_limit:
						break
			try:
				if control.monitor.abortRequested():
					return sys.exit()
				try:
					if progressDialog.iscanceled():
						break
				except:
					pass

				if len(self.sources) > 0:
					if quality == '0':
						source_4k = len([e for e in self.sources if e['quality'] == '4K' and e['debridonly'] is False])
						source_1080 = len([e for e in self.sources if e['quality'] == '1080p' and e['debridonly'] is False])
						source_720 = len([e for e in self.sources if e['quality'] in ['720p', 'HD'] and e['debridonly'] is False])
						source_sd = len([e for e in self.sources if e['quality'] in ['SD', 'SCR', 'CAM'] and e['debridonly'] is False])
					elif quality == '1':
						source_1080 = len([e for e in self.sources if e['quality'] == '1080p' and e['debridonly'] is False])
						source_720 = len([e for e in self.sources if e['quality'] in ['720p', 'HD'] and e['debridonly'] is False])
						source_sd = len([e for e in self.sources if e['quality'] in ['SD', 'SCR', 'CAM'] and e['debridonly'] is False])
					elif quality == '2':
						source_720 = len([e for e in self.sources if e['quality'] in ['720p', 'HD'] and e['debridonly'] is False])
						source_sd = len([e for e in self.sources if e['quality'] in ['SD', 'SCR', 'CAM'] and e['debridonly'] is False])
					else:
						source_sd = len([e for e in self.sources if e['quality'] in ['SD', 'SCR', 'CAM'] and e['debridonly'] is False])

					total = source_4k + source_1080 + source_720 + source_sd

				source_4k_label = total_format % ('red', source_4k) if source_4k == 0 else total_format % (pdfc, source_4k)
				source_1080_label = total_format % ('red', source_1080) if source_1080 == 0 else total_format % (pdfc, source_1080)
				source_720_label = total_format % ('red', source_720) if source_720 == 0 else total_format % (pdfc, source_720)
				source_sd_label = total_format % ('red', source_sd) if source_sd == 0 else total_format % (pdfc, source_sd)
				source_total_label = total_format % ('red', total) if total == 0 else total_format % (pdfc, total)

				if debrid_status:
					if len(self.sources) > 0:
						for d in debrid_list:
							if quality == '0':
								d_source_4k = len([e for e in self.sources if e['quality'] == '4K' and d.valid_url(e['url'], e['source'])])
								d_source_1080 = len([e for e in self.sources if e['quality'] == '1080p' and d.valid_url(e['url'], e['source'])])
								d_source_720 = len([e for e in self.sources if e['quality'] in ['720p', 'HD'] and d.valid_url(e['url'], e['source'])])
								d_source_sd = len([e for e in self.sources if e['quality'] in ['SD', 'SCR', 'CAM'] and d.valid_url(e['url'], e['source'])])
							elif quality == '1':
								d_source_1080 = len([e for e in self.sources if e['quality'] == '1080p' and d.valid_url(e['url'], e['source'])])
								d_source_720 = len([e for e in self.sources if e['quality'] in ['720p', 'HD'] and d.valid_url(e['url'], e['source'])])
								d_source_sd = len([e for e in self.sources if e['quality'] in ['SD', 'SCR', 'CAM'] and d.valid_url(e['url'], e['source'])])
							elif quality == '2':
								d_source_720 = len([e for e in self.sources if e['quality'] in ['720p', 'HD'] and d.valid_url(e['url'], e['source'])])
								d_source_sd = len([e for e in self.sources if e['quality'] in ['SD', 'SCR', 'CAM'] and d.valid_url(e['url'], e['source'])])
							else:
								d_source_sd = len([e for e in self.sources if e['quality'] in ['SD', 'SCR', 'CAM'] and d.valid_url(e['url'], e['source'])])

							d_total = d_source_4k + d_source_1080 + d_source_720 + d_source_sd

					d_4k_label = total_format % ('red', d_source_4k) if d_source_4k == 0 else total_format % (pdpc, d_source_4k)
					d_1080_label = total_format % ('red', d_source_1080) if d_source_1080 == 0 else total_format % (pdpc, d_source_1080)
					d_720_label = total_format % ('red', d_source_720) if d_source_720 == 0 else total_format % (pdpc, d_source_720)
					d_sd_label = total_format % ('red', d_source_sd) if d_source_sd == 0 else total_format % (pdpc, d_source_sd)
					d_total_label = total_format % ('red', d_total) if d_total == 0 else total_format % (pdpc, d_total)

				if (i / 2) < timeout:
					try:
						mainleft = [sourcelabelDict[x.getName()] for x in threads if x.is_alive() and x.getName() in mainsourceDict]
						info = [sourcelabelDict[x.getName()] for x in threads if x.is_alive()]
						if i >= timeout and len(mainleft) == 0 and len(self.sources) >= 100 * len(info):
							break

						if debrid_status:
							if quality == '0':
								if progressDialog != control.progressDialogBG:
									line1 = ('%s:' + '|'.join(pdiag_format)) % (string6, d_4k_label, d_1080_label, d_720_label, d_sd_label, str(string4), d_total_label)
									line2 = ('%s:' + '|'.join(pdiag_format)) % (string7, source_4k_label, source_1080_label, source_720_label, source_sd_label, str(string4), source_total_label)
								else:
									control.hide()
									line1 = '|'.join(pdiag_bg_format[:-1]) % (source_4k_label, d_4k_label, source_1080_label, d_1080_label, source_720_label, d_720_label, source_sd_label, d_sd_label)

							elif quality == '1':
								if progressDialog != control.progressDialogBG:
									line1 = ('%s:' + '|'.join(pdiag_format[1:])) % (string6, d_1080_label, d_720_label, d_sd_label, str(string4), d_total_label)
									line2 = ('%s:' + '|'.join(pdiag_format[1:])) % (string7, source_1080_label, source_720_label, source_sd_label, str(string4), source_total_label)
								else:
									control.hide()
									line1 = '|'.join(pdiag_bg_format[1:]) % (source_1080_label, d_1080_label, source_720_label, d_720_label, source_sd_label, d_sd_label, source_total_label, d_total_label)

							elif quality == '2':
								if progressDialog != control.progressDialogBG:
									line1 = ('%s:' + '|'.join(pdiag_format[2:])) % (string6, d_720_label, d_sd_label, str(string4), d_total_label)
									line2 = ('%s:' + '|'.join(pdiag_format[2:])) % (string7, source_720_label, source_sd_label, str(string4), source_total_label)
								else:
									control.hide()
									line1 = '|'.join(pdiag_bg_format[2:]) % (source_720_label, d_720_label, source_sd_label, d_sd_label, source_total_label, d_total_label)

							else:
								if progressDialog != control.progressDialogBG:
									line1 = ('%s:' + '|'.join(pdiag_format[3:])) % (string6, d_sd_label, str(string4), d_total_label)
									line2 = ('%s:' + '|'.join(pdiag_format[3:])) % (string7, source_sd_label, str(string4), source_total_label)
								else:
									control.hide()
									line1 = '|'.join(pdiag_bg_format[3:]) % (source_sd_label, d_sd_label, source_total_label, d_total_label)
						else:
							if quality == '0':
								line1 = '|'.join(pdiag_format) % (source_4k_label, source_1080_label, source_720_label, source_sd_label, str(string4), source_total_label)
							elif quality == '1':
								line1 = '|'.join(pdiag_format[1:]) % (source_1080_label, source_720_label, source_sd_label, str(string4), source_total_label)
							elif quality == '2':
								line1 = '|'.join(pdiag_format[2:]) % (source_720_label, source_sd_label, str(string4), source_total_label)
							else:
								line1 = '|'.join(pdiag_format[3:]) % (source_sd_label, str(string4), source_total_label)

						if debrid_status:
							if len(info) > 6:
								line3 = string3 % (str(len(info)))
							elif len(info) > 0:
								line3 = string3 % (', '.join(info))
							else:
								break
							percent = int(100 * float(i) / (2 * timeout) + 0.5)

							if progressDialog != control.progressDialogBG:
								progressDialog.update(max(1, percent), line1, line2, line3)
							else:
								progressDialog.update(max(1, percent), line1, line3)

						else:
							if len(info) > 6:
								line2 = string3 % (str(len(info)))
							elif len(info) > 0:
								line2 = string3 % (', '.join(info))
							else:
								break
							percent = int(100 * float(i) / (2 * timeout) + 0.5)
							progressDialog.update(max(1, percent), line1, line2)
					except Exception as e:
						log_utils.log('Exception Raised: %s' % str(e), log_utils.LOGERROR)
				else:
					try:
						mainleft = [sourcelabelDict[x.getName()] for x in threads if x.is_alive() and x.getName() in mainsourceDict]
						info = mainleft

						if debrid_status:
							if len(info) > 6:
								line3 = 'Waiting for: %s' % (str(len(info)))
							elif len(info) > 0:
								line3 = 'Waiting for: %s' % (', '.join(info))
							else:
								break

							percent = int(100 * float(i) / (2 * timeout) + 0.5) % 100

							if progressDialog != control.progressDialogBG:
								progressDialog.update(max(1, percent), line1, line2, line3)
							else:
								progressDialog.update(max(1, percent), line1, line3)

						else:
							if len(info) > 6:
								line2 = 'Waiting for: %s' % (str(len(info)))
							elif len(info) > 0:
								line2 = 'Waiting for: %s' % (', '.join(info))
							else:
								break
							percent = int(100 * float(i) / (2 * timeout) + 0.5) % 100
							progressDialog.update(max(1, percent), line1, line2)
					except:
						break
				time.sleep(0.5)
			except:
				log_utils.error()
				pass

		try:
			progressDialog.close()
		except:
			pass
		# log_utils.log('self.sources = %s' % self.sources, __name__, log_utils.LOGDEBUG)
		if len(self.sources) > 0:
			self.sourcesFilter()
		return self.sources
		# return self.sources, self.uncached_sources


	# @timeIt
	def prepareSources(self):
		try:
			control.makeFile(control.dataPath)
			dbcon = database.connect(self.sourceFile)
			dbcur = dbcon.cursor()
			dbcur.execute(
				"CREATE TABLE IF NOT EXISTS rel_url (""source TEXT, ""imdb_id TEXT, ""season TEXT, ""episode TEXT, ""rel_url TEXT, ""UNIQUE(source, imdb_id, season, episode)"");")
			dbcur.execute(
				"CREATE TABLE IF NOT EXISTS rel_src (""source TEXT, ""imdb_id TEXT, ""season TEXT, ""episode TEXT, ""hosts TEXT, ""added TEXT, ""UNIQUE(source, imdb_id, season, episode)"");")
			dbcur.connection.commit()
			dbcon.close()
		except:
			log_utils.error()
			pass


	# @timeIt
	def getMovieSource(self, title, localtitle, aliases, year, imdb, source, call):
		try:
			dbcon = database.connect(self.sourceFile, timeout=60)
			dbcur = dbcon.cursor()
		except:
			pass

		''' Fix to stop items passed with a 0 IMDB id pulling old unrelated sources from the database. '''
		if imdb == '0':
			try:
				dbcur.execute(
					"DELETE FROM rel_src WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (
					source, imdb, '', ''))
				dbcur.execute(
					"DELETE FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (
					source, imdb, '', ''))
				dbcur.connection.commit()
			except:
				log_utils.error()
				pass
		''' END '''

		try:
			sources = []
			dbcur.execute(
				"SELECT * FROM rel_src WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (
				source, imdb, '', ''))
			db_movie = dbcur.fetchone()
			if db_movie:
				timestamp = control.datetime_workaround(str(db_movie[5]), '%Y-%m-%d %H:%M:%S.%f', False)
				db_movie_valid = abs(self.time - timestamp) < self.single_expiry
				if db_movie_valid:
					sources = eval(db_movie[4].encode('utf-8'))
					return self.sources.extend(sources)
		except:
			log_utils.error()
			pass

		try:
			url = None
			dbcur.execute(
				"SELECT * FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (
				source, imdb, '', ''))
			url = dbcur.fetchone()
			if url:
				url = eval(url[4].encode('utf-8'))
		except:
			log_utils.error()
			pass

		try:
			if not url:
				url = call.movie(imdb, title, localtitle, aliases, year)
			if url:
				dbcur.execute("INSERT OR REPLACE INTO rel_url Values (?, ?, ?, ?, ?)", (source, imdb, '', '', repr(url)))
				dbcur.connection.commit()
		except:
			log_utils.error()
			pass

		try:
			sources = []
			sources = call.sources(url, self.hostDict, self.hostprDict)
			if sources:
				sources = [json.loads(t) for t in set(json.dumps(d, sort_keys=True) for d in sources)]
				for i in sources:
					i.update({'provider': source})
				self.sources.extend(sources)
				dbcur.execute("INSERT OR REPLACE INTO rel_src Values (?, ?, ?, ?, ?, ?)", (source, imdb, '', '', repr(sources), datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")))
				dbcur.connection.commit()
		except:
			log_utils.error()
			pass
		dbcon.close()


	# @timeIt
	def getEpisodeSource(self, title, year, imdb, tvdb, season, episode, tvshowtitle, localtvshowtitle, aliases, premiered, source, call):
		try:
			dbcon = database.connect(self.sourceFile, timeout=60)
			self.dbcon = dbcon
			dbcur = dbcon.cursor()
		except:
			pass

# consider adding tvdb_id table column for better matching of cases where imdb_id not available. Wheeler Dealer BS shows..lol
		''' Fix to stop items passed with a 0 IMDB id pulling old unrelated sources from the database. '''
		if imdb == '0':
			try:
				dbcur.execute(
					"DELETE FROM rel_src WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (
					source, imdb, season, episode))
				dbcur.execute(
					"DELETE FROM rel_src WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (
					source, imdb, season, ''))
				dbcur.execute(
					"DELETE FROM rel_src WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (
					source, imdb, '', ''))
				dbcur.execute(
					"DELETE FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (
					source, imdb, season, episode))
				dbcur.execute(
					"DELETE FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (
					source, imdb, '', ''))
				dbcur.connection.commit()
			except:
				log_utils.error()
				pass
		''' END '''

		try:
			# singleEpisodes db check
			db_singleEpisodes_valid = False
			if self.dev_mode and self.dev_disable_single:
				raise Exception()
			sources = []
			dbcur.execute(
				"SELECT * FROM rel_src WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (
				source, imdb, season, episode))
			db_singleEpisodes = dbcur.fetchone()
			if db_singleEpisodes:
				timestamp = control.datetime_workaround(str(db_singleEpisodes[5]), '%Y-%m-%d %H:%M:%S.%f', False)
				db_singleEpisodes_valid = abs(self.time - timestamp) < self.single_expiry
				if db_singleEpisodes_valid:
					sources = eval(db_singleEpisodes[4].encode('utf-8'))
					self.sources.extend(sources)
					if not self.enablePacks:
						return self.sources
		except:
			log_utils.error()
			pass

		try:
			# seasonPacks db check
			db_seasonPacks_valid = False
			if not self.enablePacks:
				raise Exception()
			if self.is_airing:
				raise Exception()
			if self.dev_mode and self.dev_disable_season_packs:
				raise Exception()
			sources = []
			dbcur.execute(
				"SELECT * FROM rel_src WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (
				source, imdb, season, ''))
			db_seasonPacks = dbcur.fetchone()
			if db_seasonPacks:
				timestamp = control.datetime_workaround(str(db_seasonPacks[5]), '%Y-%m-%d %H:%M:%S.%f', False)
				db_seasonPacks_valid = abs(self.time - timestamp) < self.season_expiry
				if db_seasonPacks_valid:
					sources = eval(db_seasonPacks[4].encode('utf-8'))
					self.sources.extend(sources)
		except:
			log_utils.error()
			pass

		try:
			# # showPacks db check
			db_showPacks_valid = False
			if not self.enablePacks:
				raise Exception()
			if self.dev_mode and self.dev_disable_show_packs:
				raise Exception()
			sources = []
			dbcur.execute(
				"SELECT * FROM rel_src WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (
				source, imdb, '', ''))
			db_showPacks = dbcur.fetchone()
			if db_showPacks:
				timestamp = control.datetime_workaround(str(db_showPacks[5]), '%Y-%m-%d %H:%M:%S.%f', False)
				db_showPacks_valid = abs(self.time - timestamp) < self.show_expiry
				if db_showPacks_valid:
					sources = eval(db_showPacks[4].encode('utf-8'))
					sources = [i for i in sources if i.get('last_season') >= int(season)] # filter out range items that do not apply to current season
					self.sources.extend(sources)
					if db_singleEpisodes_valid and db_seasonPacks_valid:
						return self.sources
		except:
			log_utils.error()
			pass

		try:
			url = None
			dbcur.execute(
				"SELECT * FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (source, imdb, '', ''))
			url = dbcur.fetchone()
			if url:
				url = eval(url[4].encode('utf-8'))
		except:
			log_utils.error()
			pass

		try:
			if not url:
				url = call.tvshow(imdb, tvdb, tvshowtitle, localtvshowtitle, aliases, year)
			if url:
				dbcur.execute("INSERT OR REPLACE INTO rel_url Values (?, ?, ?, ?, ?)", (source, imdb, '', '', repr(url)))
				dbcur.connection.commit()
		except:
			log_utils.error()
			pass

		try:
			ep_url = None
			dbcur.execute(
				"SELECT * FROM rel_url WHERE source = '%s' AND imdb_id = '%s' AND season = '%s' AND episode = '%s'" % (
				source, imdb, season, episode))
			ep_url = dbcur.fetchone()
			if ep_url:
				ep_url = eval(ep_url[4].encode('utf-8'))
		except:
			log_utils.error()
			pass

		try:
			if url:
				if not ep_url:
					ep_url = call.episode(url, imdb, tvdb, title, premiered, season, episode)
				if ep_url:
					dbcur.execute("INSERT OR REPLACE INTO rel_url Values (?, ?, ?, ?, ?)", (source, imdb, season, episode, repr(ep_url)))
					dbcur.connection.commit()
		except:
			log_utils.error()
			pass

		try:
			# singleEpisodes scraper call
			if self.dev_mode and self.dev_disable_single:
				raise Exception()
			if db_singleEpisodes_valid:
				raise Exception()
			sources = []
			sources = call.sources(ep_url, self.hostDict, self.hostprDict)
			if sources:
				sources = [json.loads(t) for t in set(json.dumps(d, sort_keys=True) for d in sources)]
				for i in sources:
					i.update({'provider': source})
				self.sources.extend(sources)
				dbcur.execute("INSERT OR REPLACE INTO rel_src Values (?, ?, ?, ?, ?, ?)", (source, imdb, season, episode, repr(sources), datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")))
				dbcur.connection.commit()
		except:
			log_utils.error()
			pass

		try:
		# seasonPacks scraper call
			if self.dev_mode and self.dev_disable_season_packs:
				raise Exception()
			if self.is_airing:
				raise Exception()
			if self.enablePacks and source in self.packDict:
				if db_seasonPacks_valid:
					raise Exception()
				sources = []
				sources = call.sources_packs(ep_url, self.hostDict, self.hostprDict, bypass_filter=self.dev_disable_season_filter)
				if sources:
					sources = [json.loads(t) for t in set(json.dumps(d, sort_keys=True) for d in sources)]
					for i in sources:
						i.update({'provider': source})
					self.sources.extend(sources)
					dbcur.execute("INSERT OR REPLACE INTO rel_src Values (?, ?, ?, ?, ?, ?)", (source, imdb, season,'', repr(sources), datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")))
					dbcur.connection.commit()
		except:
			log_utils.error()
			pass

		try:
		# showPacks scraper call
			if self.dev_mode and self.dev_disable_show_packs:
				raise Exception()
			if self.enablePacks and source in self.packDict:
				if db_showPacks_valid:
					raise Exception()
				sources = []
				sources = call.sources_packs(ep_url, self.hostDict, self.hostprDict, search_series=True, total_seasons=self.total_seasons, bypass_filter=self.dev_disable_show_filter)
				if sources:
					sources = [json.loads(t) for t in set(json.dumps(d, sort_keys=True) for d in sources)]
					for i in sources:
						i.update({'provider': source})
					sources = [i for i in sources if i.get('last_season') >= int(season)] # filter out range items that do not apply to current season
					self.sources.extend(sources)
					dbcur.execute("INSERT OR REPLACE INTO rel_src Values (?, ?, ?, ?, ?, ?)", (source, imdb, '', '', repr(sources), datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")))
					dbcur.connection.commit()
		except:
			log_utils.error()
			pass
		dbcon.close()


	def alterSources(self, url, meta):
		try:
			if control.setting('hosts.mode') == '2' or (control.setting('enable.upnext') == 'true' and 'episode' in meta):
				url += '&select=1'
			else:
				url += '&select=2'
			# control.execute('RunPlugin(%s)' % url)
			control.execute('PlayMedia(%s)' % url)
		except:
			log_utils.error()
			pass

	# @timeIt
	def sourcesFilter(self):
		control.busy()
		quality = control.setting('hosts.quality')
		if quality == '':
			quality = '0'

		if control.setting('remove.duplicates') == 'true':
			self.sources = self.filter_dupes()

		if control.setting('source.enablesizelimit') == 'true':
			self.sources = [i for i in self.sources if i.get('size', 0) <= int(control.setting('source.sizelimit'))]

		if control.setting('remove.hevc') == 'true':
			self.sources = [i for i in self.sources if 'HEVC' not in i.get('info', '')] # scrapers write HEVC to info

		if control.setting('remove.CamSd.sources') == 'true':
			if any(i for i in self.sources if any(value in i['quality'] for value in ['4K', '1080p', '720p'])): #only remove CAM and SD if better quality does exist
				# if pre_emp is enabled it seems as if a threads not terminated and SD sources still get through.
				self.sources = [i for i in self.sources if not any(value in i['quality'] for value in ['CAM', 'SD'])]

		if control.setting('remove.3D.sources') == 'true':
			self.sources = [i for i in self.sources if '3D' not in i.get('info', '')] # scrapers write 3D to info

		if control.setting('hosts.sort.provider') == 'true':
			self.sources = sorted(self.sources, key=lambda k: k['provider'])

		# calculate episode size of pack files
		if self.mediatype == 'episode':
			self.sources = self.calc_pack_size()

		if control.setting('torrent.size.sort') == 'true':
			filter = []
			filter += [i for i in self.sources if 'magnet:' in i['url']]
			filter.sort(key=lambda k: k.get('size', 0), reverse=True)
			filter += [i for i in self.sources if 'magnet:' not in i['url']]
			self.sources = filter

		local = [i for i in self.sources if 'local' in i and i['local'] is True]
		for i in local:
			i.update({'language': self._getPrimaryLang() or 'en'})
		self.sources = [i for i in self.sources if not i in local]

		filter = []
		import copy
		for d in debrid.debrid_resolvers:
			valid_hoster = set([i['source'] for i in self.sources])
			valid_hoster = [i for i in valid_hoster if d.valid_url('', i)]
			if d.name == 'Premiumize.me':
				if control.setting('pm.chk.cached') == 'true':
					try:
						pmTorrent_List = copy.deepcopy(self.sources)
						pmTorrent_List = [i for i in pmTorrent_List if 'magnet:' in i['url']]
						if pmTorrent_List == []:
							raise Exception()
						pmCached = self.pm_cache_chk_list(pmTorrent_List, d)
						# self.uncached_sources += [dict(i.items() + [('debrid', d.name)]) for i in pmCached if re.match(r'uncached.*torrent', i['source'])]
						if control.setting('pm.remove.uncached') == 'true':
							filter += [dict(i.items() + [('debrid', d.name)]) for i in pmCached if re.match(r'cached.*torrent', i['source'])]
						else:
							filter += [dict(i.items() + [('debrid', d.name)]) for i in pmCached if 'magnet:' in i['url']]
					except:
						log_utils.error()
						pass
				else:
					filter += [dict(i.items() + [('debrid', d.name)]) for i in self.sources if 'magnet:' in i['url']]
				filter += [dict(i.items() + [('debrid', d.name)]) for i in self.sources if i['source'] in valid_hoster and 'magnet:' not in i['url']]

			if d.name == 'Real-Debrid':
				if control.setting('rd.chk.cached') == 'true':
					try:
						rdTorrent_List = copy.deepcopy(self.sources)
						rdTorrent_List = [i for i in rdTorrent_List if 'magnet:' in i['url']]
						if rdTorrent_List == []:
							raise Exception()
						rdCached = self.rd_cache_chk_list(rdTorrent_List, d)
						# self.uncached_sources += [dict(i.items() + [('debrid', d.name)]) for i in rdCached if re.match(r'uncached.*torrent', i['source'])]
						if control.setting('rd.remove.uncached') == 'true':
							filter += [dict(i.items() + [('debrid', d.name)]) for i in rdCached if re.match(r'cached.*torrent', i['source'])]
						else:
							filter += [dict(i.items() + [('debrid', d.name)]) for i in rdCached if 'magnet:' in i['url']]
					except:
						log_utils.error()
						pass
				else:
					filter += [dict(i.items() + [('debrid', d.name)]) for i in self.sources if 'magnet:' in i['url']]
				filter += [dict(i.items() + [('debrid', d.name)]) for i in self.sources if i['source'] in valid_hoster and 'magnet:' not in i['url']]

			if d.name != 'Premiumize.me' and d.name != 'Real-Debrid':
				filter += [dict(i.items() + [('debrid', d.name)]) for i in self.sources if 'magnet:' in i['url']]
				filter += [dict(i.items() + [('debrid', d.name)]) for i in self.sources if i['source'] in valid_hoster and 'magnet:' not in i['url']]

		if control.setting('debrid.only') == 'false' or debrid.status() is False:
			filter += [i for i in self.sources if not i['source'] in self.hostprDict and i['debridonly'] is False]

		self.sources = filter

		if control.setting('torrent.group.sort') == '1':
			filter = []
			filter += [i for i in self.sources if 'torrent' in i['source']]  #torrents first
			if control.setting('torrent.size.sort') == 'true':
				filter.sort(key=lambda k: k.get('size', 0), reverse=True)
			filter += [i for i in self.sources if 'torrent' not in i['source'] and i['debridonly'] is True]  #prem. next
			filter += [i for i in self.sources if 'torrent' not in i['source'] and i['debridonly'] is False]  #free hosters fucking last
			self.sources = filter

		filter = []
		filter += local

		if quality in ['0']:
			filter += [i for i in self.sources if i['quality'] == '4K' and 'debrid' in i]
			filter += [i for i in self.sources if i['quality'] == '4K' and not 'debrid' in i]

		if quality in ['0', '1']:
			filter += [i for i in self.sources if i['quality'] == '1080p' and 'debrid' in i]
			filter += [i for i in self.sources if i['quality'] == '1080p' and not 'debrid' in i]

		if quality in ['0', '1', '2']:
			filter += [i for i in self.sources if i['quality'] == '720p' and 'debrid' in i]
			filter += [i for i in self.sources if i['quality'] == '720p' and not 'debrid' in i]

		filter += [i for i in self.sources if i['quality'] == 'SCR']
		filter += [i for i in self.sources if i['quality'] == 'SD']
		filter += [i for i in self.sources if i['quality'] == 'CAM']
		self.sources = filter

		if control.setting('remove.captcha') == 'true':
			self.sources = [i for i in self.sources if not (i['source'] in self.hostcapDict and not 'debrid' in i)]

		self.sources = [i for i in self.sources if not i['source'] in self.hostblockDict]

		multi = [i['language'] for i in self.sources]
		multi = [x for y, x in enumerate(multi) if x not in multi[:y]]
		multi = True if len(multi) > 1 else False

		if multi:
			self.sources = [i for i in self.sources if i['language'] != 'en'] + [i for i in self.sources if i['language'] == 'en']

		self.sources = self.sources[:4000]

		extra_info = control.setting('sources.extrainfo')

		prem_identify = control.setting('prem.identify')
		prem_identify = control.getColor(prem_identify)

		torr_identify = control.setting('torrent.identify')
		torr_identify = control.getColor(torr_identify)

		sec_color = control.setting('sec.identify')
		sec_identify = control.getColor(sec_color)
		sec_identify2 = control.setting('sec.identify2')

		for i in range(len(self.sources)):
			if extra_info == 'true':
				t = source_utils.getFileType(self.sources[i]['url'])
			else:
				t = ''

			u = self.sources[i]['url']
			q = self.sources[i]['quality']
			p = self.sources[i]['provider'].upper()
			s = self.sources[i]['source'].upper()
			s = s.rsplit('.', 1)[0]
			l = self.sources[i]['language']

			try:
				f = (' / '.join(['%s ' % info.strip() for info in self.sources[i]['info'].split('|')]))
			except:
				f = ''

			try:
				d = self.debrid_abv(self.sources[i]['debrid'])
			except:
				d = self.sources[i]['debrid'] = ''

			prem_color = 'nocolor'
			if d:
				if 'TORRENT' in s and torr_identify != 'nocolor':
					prem_color = torr_identify
				elif 'TORRENT' not in s and prem_identify != 'nocolor':
					prem_color = prem_identify

			if d != '':
				label = '[COLOR %s]%02d  |  [B]%s[/B]  |  %s  |  %s  |  [B]%s[/B][/COLOR]' % (prem_color, int(i + 1), q, d, p, s)
			else:
				label = '%02d  |  %s  |  %s  |  %s' % (int(i + 1), q, p, s)

			# if multi is True and l != 'en':
			if l != 'en':
				label += '[COLOR %s]  |  [B]%s[/B][/COLOR]' % (prem_color, l.upper())

			multiline_label = label
			mLabel = label
			l1 = label

			if t != '':
				if f != '' and f != '0 ' and f != ' ':
					multiline_label += '\n       [COLOR %s][I]%s / %s[/I][/COLOR]' % (sec_identify, f, t)
					label += '[COLOR %s] / %s / %s[/COLOR]' % (prem_color, f, t)
				else:
					multiline_label += '\n       [COLOR %s][I]%s[/I][/COLOR]' % (sec_identify, t)
					label += '[COLOR %s] / %s[/COLOR]' % (prem_color, t)
			else:
				if f != '' and f != '0 ' and f != ' ':
					multiline_label += '\n       [COLOR %s][I]%s[/I][/COLOR]' % (sec_identify, f)
					label += '[COLOR %s] / %s[/COLOR]' % (prem_color, f)

			if sec_identify2 == 'magnet title':
				if 'magnet:' in u:
					link_title = self.sources[i]['name']
					size = ''
					if f:
						size = f.split(' /', 1)[0]
						l1 += '[COLOR %s]  |  %s[/COLOR]' % (prem_color, size)
						l1l = len(l1)-58
						l2 = '\n       [COLOR %s][I]%s[/I][/COLOR]' % (sec_identify, link_title)
						l2l = len(l2)-27
						if l2l > l1l:
							adjust = l2l - l1l
							l1 = l1.ljust(l1l+76+adjust)
					multiline_label = l1 + l2

			self.sources[i]['multiline_label'] = multiline_label
			# self.uncached_sources[i]['multiline_label'] = multiline_label
			self.sources[i]['label'] = label
			# self.uncached_sources[i]['label'] = label

		# self.sources = [i for i in self.sources if 'label' or 'multiline_label' in i['label']]
		return self.sources
		# return self.sources, self.uncached_sources


	def sourcesResolve(self, item, info=False):
		if 'package' in item:
			self.url = None
			if not 'uncached' in item['source']:
				try:
					meta = control.window.getProperty(self.metaProperty)
					if meta:
						meta = json.loads(unquote(meta.replace('%22', '\\"')))
						season = meta.get('season')
						episode = meta.get('episode')
						title = meta.get('title')
					else:
						season = control.window.getProperty(self.seasonProperty)
						episode = control.window.getProperty(self.episodeProperty)
						title = control.window.getProperty(self.titleProperty)
					if item['debrid'] == 'Real-Debrid':
						from resources.lib.modules.realdebrid import RealDebrid
						url = RealDebrid().resolve_magnet_pack(item['url'], item['hash'], season, episode, title)
					elif item['debrid'] == 'Premiumize.me':
						from resources.lib.modules.premiumize import Premiumize
						url = Premiumize().resolve_magnet_pack(item['url'], season, episode, title)
					self.url = url
					return url
				except:
					log_utils.error()
					return
		else:
			self.url = None
			# may need to add a check if user turned off "cached torrents" only in resolveURL and want them to be sent to their cloud
			# if not 'uncached' in item['source']:
			try:
				u = url = item['url']
				d = item['debrid']
				direct = item['direct']
				local = item.get('local', False)
				provider = item['provider']
				call = [i[1] for i in self.sourceDict if i[0] == provider][0]
				u = url = call.resolve(url)
				if url is None or ('://' not in url and not local and 'magnet:' not in url):
					raise Exception()
				if not local:
					url = url[8:] if url.startswith('stack:') else url
					urls = []
					for part in url.split(' , '):
						u = part
						if d != '':
							part = debrid.resolver(part, d)
						elif direct is not True:
							hmf = resolveurl.HostedMediaFile(url=u, include_disabled=True, include_universal=False)
							if hmf.valid_url() is True:
								part = hmf.resolve()
						urls.append(part)
					url = 'stack://' + ' , '.join(urls) if len(urls) > 1 else urls[0]
				if url is False or url is None:
					raise Exception()
				ext = url.split('?')[0].split('&')[0].split('|')[0].rsplit('.')[-1].replace('/', '').lower()
				if ext == 'rar':
					raise Exception()
				try:
					headers = url.rsplit('|', 1)[1]
				except:
					headers = ''
				headers = quote_plus(headers).replace('%3D', '=') if ' ' in headers else headers
				headers = dict(parse_qsl(headers))

				if url.startswith('http') and '.m3u8' in url:
					result = client.request(url.split('|')[0], headers=headers, output='geturl', timeout='20')
					if result is None:
						raise Exception()

				elif url.startswith('http'):
					result = client.request(url.split('|')[0], headers=headers, output='chunk', timeout='20')
					if result is None:
						raise Exception()

				self.url = url
				return url
			except:
				if info:
					control.notification(title='default', message='Skipping unplayable resolveURL link', icon='default', sound=(control.setting('notification.sound') == 'true'))
				log_utils.error()
				return


	# @timeIt
	def sourcesDialog(self, items):
		try:
			multiline = control.setting('sourcelist.multiline') == 'true'
			if multiline:
				labels = [i['multiline_label'] for i in items]
			else:
				labels = [i['label'] for i in items]

			select = control.selectDialog(labels)
			if select == -1:
				return 'close://'

			tot_items = len(items)
			next = [y for x, y in enumerate(items) if x >= select]
			prev = [y for x, y in enumerate(items) if x < select][::-1]

			items = [items[select]]

			# items = [i for i in items + next + prev][:40]
			items = [i for i in items + next + prev][:tot_items]

			header = control.addonInfo('name')
			header2 = header.upper()

			progressDialog = control.progressDialog if control.setting('progress.dialog') == '0' else control.progressDialogBG
			progressDialog.create(header, '')
			progressDialog.update(0)

			block = None

			for i in range(len(items)):
				try:
					if items[i]['source'] == block:
						raise Exception()

					w = workers.Thread(self.sourcesResolve, items[i])
					w.start()

					try:
						if progressDialog.iscanceled():
							break
						progressDialog.update(int((100 / float(len(items))) * i), str(items[i]['label']), str(' '))
					except:
						progressDialog.update(int((100 / float(len(items))) * i), str(header2), str(items[i]['label']))

					if items[i].get('source') in self.hostcapDict:
						offset = 60 * 2
					elif items[i].get('source') == 'torrent':
						offset = float('inf')
					else:
						offset = 0

					m = ''
					for x in range(3600):
						try:
							if control.monitor.abortRequested():
								control.notification(title='default', message='Sources Cancelled', icon='default', sound=(control.setting('notification.sound') == 'true'))
								return sys.exit()
							if progressDialog.iscanceled():
								control.notification(title='default', message='Sources Cancelled', icon='default', sound=(control.setting('notification.sound') == 'true'))
								return progressDialog.close()
						except:
							pass

						k = control.condVisibility('Window.IsActive(virtualkeyboard)')
						if k:
							m += '1'
							m = m[-1]
						if (not w.is_alive() or x > 30 + offset) and not k:
							break

						k = control.condVisibility('Window.IsActive(yesnoDialog)')
						if k:
							m += '1'
							m = m[-1]
						if (not w.is_alive() or x > 30 + offset) and not k:
							break
						time.sleep(0.5)

					for x in range(30):
						try:
							if control.monitor.abortRequested():
								control.notification(title='default', message='Sources Cancelled', icon='default', sound=(control.setting('notification.sound') == 'true'))
								return sys.exit()
							if progressDialog.iscanceled():
								control.notification(title='default', message='Sources Cancelled', icon='default', sound=(control.setting('notification.sound') == 'true'))
								return progressDialog.close()
						except:
							log_utils.error()
							pass

						if m == '':
							break

						if not w.is_alive():
							break
						time.sleep(0.5)

					if w.is_alive():
						block = items[i]['source']

					if not self.url:
						raise Exception()

					self.selectedSource = items[i]['label']

					try:
						progressDialog.close()
					except:
						pass

					control.execute('Dialog.Close(virtualkeyboard)')
					control.execute('Dialog.Close(yesnoDialog)')
					return self.url
				except:
					pass

			try:
				progressDialog.close()
			except:
				pass

		except Exception as e:
			try:
				progressDialog.close()
			except:
				pass
			log_utils.log('Error %s' % str(e), __name__, log_utils.LOGNOTICE)


	# @timeIt
	def sourcesAutoPlay(self, items):
		filter = [i for i in items if i['source'] in self.hostcapDict and i['debrid'] == '']
		items = [i for i in items if not i in filter]

		filter = [i for i in items if i['source'] in self.hostblockDict]# and i['debrid'] == '']
		items = [i for i in items if not i in filter]
		# items = [i for i in items if ('autoplay' in i and i['autoplay'] is True) or not 'autoplay' in i] # wtf...nothing writes autoplay to the sources

		if control.setting('autoplay.sd') == 'true':
			items = [i for i in items if not i['quality'] in ['4K', '1080p', '720p', 'HD']]

		u = None

		header = control.addonInfo('name')
		header2 = header.upper()

		try:
			control.sleep(1000)
			if control.setting('progress.dialog') == '0':
				progressDialog = control.progressDialog
			else:
				progressDialog = control.progressDialogBG
			progressDialog.create(header, '')
			progressDialog.update(0)
		except:
			pass

		for i in range(len(items)):
			try:
				if progressDialog.iscanceled():
					break
				progressDialog.update(int((100 / float(len(items))) * i), str(items[i]['label']), str(' '))
			except:
				progressDialog.update(int((100 / float(len(items))) * i), str(header2), str(items[i]['label']))
				pass

			try:
				if control.monitor.abortRequested():
					return sys.exit()

				url = self.sourcesResolve(items[i])
				if not u:
					u = url
				if url:
					break
			except:
				pass
		try:
			progressDialog.close()
		except:
			pass
		return u


	def debridPackDialog(self, provider, name, magnet_url, info_hash):
		try:
			if provider == 'Real-Debrid':
				from resources.lib.modules.realdebrid import RealDebrid as debrid_function
			elif provider == 'Premiumize.me':
				from resources.lib.modules.premiumize import Premiumize as debrid_function

			debrid_files = None
			control.busy()
			try:
				debrid_files = debrid_function().display_magnet_pack(magnet_url, info_hash)
			except:
				pass

			if not debrid_files:
				control.hide()
				return control.notification(message='Error with Debrid Pack')

			debrid_files = sorted(debrid_files, key=lambda k: k['filename'].lower())

			display_list = ['%02d | [B]%.2f GB[/B] | [I]%s[/I]' % \
							(count,
							i['size'],
							i['filename'].upper()) for count, i in enumerate(debrid_files, 1)]

			control.hide()

			chosen = control.selectDialog(display_list, heading=name)
			if chosen < 0:
				return None

			chosen_result = debrid_files[chosen]

			if provider  == 'Real-Debrid':
				self.url = debrid_function().unrestrict_link(chosen_result['link'])
			elif provider == 'Premiumize.me':
				self.url = debrid_function().add_headers_to_url(chosen_result['link'])

			from resources.lib.modules import player
			from resources.lib.modules.source_utils import seas_ep_filter
			meta = json.loads(unquote(control.window.getProperty(self.metaProperty).replace('%22', '\\"')))
			title = meta['tvshowtitle']
			year = meta['year'] if 'year' in meta else None

			if 'tvshowtitle' in meta:
				year = meta['tvshowyear'] if 'tvshowyear' in meta else year

			season = meta['season'] if 'season' in meta else None
			episode = meta['episode'] if 'episode' in meta else None

			imdb = meta['imdb'] if 'imdb' in meta else None
			tvdb = meta['tvdb'] if 'tvdb' in meta else None

			release_title = re.sub('[^A-Za-z0-9]+', '.', unquote(chosen_result['filename'])).lower()

			if seas_ep_filter(season, episode, release_title):
				return player.Player().play_source(title, year, season, episode, imdb, tvdb, self.url, meta, select='1')
			else:
				return player.Player().play(self.url)

		except Exception as e:
			control.hide()
			log_utils.log('Error debridPackDialog %s' % str(e), __name__, log_utils.LOGNOTICE)


	def errorForSources(self):
		try:
			control.sleep(200) # added 5/14
			control.hide()
			if self.url == 'close://':
				control.notification(title='default', message='Sources Cancelled', icon='default', sound=(control.setting('notification.sound') == 'true'))
			else:
				control.notification(title='default', message=32401, icon='default', sound=(control.setting('notification.sound') == 'true'))
			control.cancelPlayback()
		except:
			log_utils.error()


	def getLanguage(self):
		langDict = {
			'English': ['en'], 'German': ['de'], 'German+English': ['de', 'en'],
			'French': ['fr'], 'French+English': ['fr', 'en'], 'Portuguese': ['pt'],
			'Portuguese+English': ['pt', 'en'], 'Polish': ['pl'], 'Polish+English': ['pl', 'en'],
			'Korean': ['ko'], 'Korean+English': ['ko', 'en'], 'Russian': ['ru'],
			'Russian+English': ['ru', 'en'], 'Spanish': ['es'], 'Spanish+English': ['es', 'en'],
			'Greek': ['gr'], 'Italian': ['it'], 'Italian+English': ['it', 'en'],
			'Greek+English': ['gr', 'en']}
		name = control.setting('providers.lang')
		return langDict.get(name, ['en'])


	def getLocalTitle(self, title, imdb, tvdb, content):
		lang = self._getPrimaryLang()
		if not lang:
			return title
		if content == 'movie':
			t = trakt.getMovieTranslation(imdb, lang)
		else:
			from resources.lib.modules import tvmaze
			t = tvmaze.tvMaze().getTVShowTranslation(tvdb, lang)
		return t or title


	def getAliasTitles(self, imdb, localtitle, content):
		lang = self._getPrimaryLang()
		try:
			t = trakt.getMovieAliases(imdb) if content == 'movie' else trakt.getTVShowAliases(imdb)
			if not t:
				return []
			t = [i for i in t if i.get('country', '').lower() in [lang, '', 'us'] and i.get('title', '').lower() != localtitle.lower()]
			return json.dumps(t)
		except:
			log_utils.error()
			return []


	def _getPrimaryLang(self):
		langDict = {'English': 'en', 'German': 'de', 'German+English': 'de', 'French': 'fr', 'French+English': 'fr',
						'Portuguese': 'pt', 'Portuguese+English': 'pt', 'Polish': 'pl', 'Polish+English': 'pl', 'Korean': 'ko',
						'Korean+English': 'ko', 'Russian': 'ru', 'Russian+English': 'ru', 'Spanish': 'es', 'Spanish+English': 'es',
						'Italian': 'it', 'Italian+English': 'it', 'Greek': 'gr', 'Greek+English': 'gr'}
		name = control.setting('providers.lang')
		lang = langDict.get(name)
		return lang


	def getTitle(self, title):
		title = cleantitle.normalize(title)
		return title


	# @timeIt
	def getConstants(self):
		self.itemProperty = 'plugin.video.venom.container.items'
		self.metaProperty = 'plugin.video.venom.container.meta'
		self.seasonProperty = 'plugin.video.venom.container.season'
		self.episodeProperty = 'plugin.video.venom.container.episode'
		self.titleProperty = 'plugin.video.venom.container.title'
		self.imdbProperty = 'plugin.video.venom.container.imdb'
		self.tvdbProperty = 'plugin.video.venom.container.tvdb'

		from openscrapers import sources
		self.sourceDict = sources()

		from openscrapers import pack_sources
		self.packDict = pack_sources()

		try:
			self.hostDict = resolveurl.relevant_resolvers(order_matters=True)
			self.hostDict = [i.domains for i in self.hostDict if not '*' in i.domains]
			self.hostDict = [i for i in reduce(lambda x, y: x+y, self.hostDict)] # domains already in lower case
			self.hostDict = [x for y, x in enumerate(self.hostDict) if x not in self.hostDict[:y]]
		except:
			log_utils.error()
			self.hostDict = []

		self.hostprDict = ['1fichier.com', 'filefactory.com', 'filefreak.com', 'multiup.org', 'nitroflare.com', 'oboom.com', 'rapidgator.net', 'rg.to', 'turbobit.net',
									'uploaded.net', 'uploaded.to', 'uploadgig.com', 'ul.to', 'uploadrocket.net']

		self.hostcapDict = ['flashx.tv', 'flashx.to', 'flashx.sx', 'flashx.bz', 'flashx.cc', 'hugefiles.cc', 'hugefiles.net', 'jetload.net', 'jetload.tv',
									'jetload.to''kingfiles.net', 'streamin.to', 'thevideo.me', 'torba.se', 'uptobox.com', 'uptostream.com', 'vidup.io',
									'vidup.me', 'vidup.tv', 'vshare.eu', 'vshare.io', 'vev.io']

		self.hosthqDict = ['gvideo', 'google.com', 'thevideo.me', 'raptu.com', 'filez.tv', 'uptobox.com', 'uptostream.com',
									'xvidstage.com', 'xstreamcdn.com', 'idtbox.com', 'streamvid.co']

		self.hostblockDict = ['divxme.com', 'divxstage.eu', 'estream.to', 'facebook.com', 'oload.download', 'oload.fun', 'oload.icu', 'oload.info',
									'oload.life', 'oload.space', 'oload.stream', 'oload.tv', 'oload.win', 'openload.co', 'openload.io', 'openload.pw', 'rapidvideo.com',
									'rapidvideo.is', 'rapidvid.to', 'streamango.com', 'streamcherry.com', 'twitch.tv', 'youtube.com', 'zippyshare.com']

		self.sourcecfDict = ['1putlocker', '123movies', '123movieshubz', 'animebase', 'animetoon', 'cartoonhdto', 'cmovieshd', 'extramovies', 'filmpalast',
									'filmxy', 'fmovies', 'ganoolcam', 'gomoviesonl', 'hdfilme', 'iload', 'movietown', 'projectfreetv', 'putlockeronl', 'seehd', 'series9',
									'streamdreams', 'timewatch', 'xwatchseries', 'ganool', 'maxrls', 'mkvhub', 'rapidmoviez', 'rlsbb', 'scenerls', 'tvdownload', 'btdb',
									'extratorrent', 'limetorrents', 'moviemagnet', 'torrentgalaxy', 'torrentz']


	# @timeIt
	def filter_dupes(self):
		filter = []
		for i in self.sources:
			a = i['url'].lower()
			for sublist in filter:
				try:
					b = sublist['url'].lower()
					if 'magnet:' in a and debrid.status():
						# info_hash = re.search('magnet:.+?urn:\w+:([a-z0-9]+)', a)
						info_hash = i['hash'].lower()
						if info_hash:
							# if info_hash.group(1) in b:
							if info_hash in b:
								filter.remove(sublist)
								if control.setting('remove.duplicates.logging') != 'true':
									log_utils.log('Removing %s - %s (DUPLICATE TORRENT) ALREADY IN :: %s' % (sublist['provider'], b, i['provider']), log_utils.LOGDEBUG)
								break
					elif a == b:
						filter.remove(sublist)
						if control.setting('remove.duplicates.logging') != 'true':
							log_utils.log('Removing %s - %s (DUPLICATE LINK) ALREADY IN :: %s' % (sublist['source'], i['url'], i['provider']), log_utils.LOGDEBUG)
						break
				except:
					log_utils.error()
					pass
			filter.append(i)
		log_utils.log('Removed %s duplicate sources from list' % (len(self.sources) - len(filter)), log_utils.LOGDEBUG)
		self.sources = filter
		return self.sources


	def calc_pack_size(self):
		seasoncount = None
		counts = None
		try:
			meta = control.window.getProperty(self.metaProperty)
			if meta:
				meta = json.loads(unquote(meta.replace('%22', '\\"')))
				seasoncount = meta.get('seasoncount', None)
				counts = meta.get('counts', None)
		except:
			log_utils.error()
			pass

		# check metacache, 2nd fallback
		if not seasoncount or not counts:
			try:
				imdb_user = control.setting('imdb.user').replace('ur', '')
				tvdb_key_list = [
					'MDZjZmYzMDY5MGY5Yjk2MjI5NTcwNDRmMjE1OWZmYWU=',
					'MUQ2MkYyRjkwMDMwQzQ0NA==',
					'N1I4U1paWDkwVUE5WU1CVQ==']
				tvdb_key = tvdb_key_list[int(control.setting('tvdb.api.key'))]
				user = str(imdb_user) + str(tvdb_key)
				meta_lang = control.apiLanguage()['tvdb']
				if meta:
					imdb = meta.get('imdb')
					tvdb = meta.get('tvdb')
				else:
					imdb = control.window.getProperty(self.imdbProperty)
					tvdb = control.window.getProperty(self.tvdbProperty)
				ids = [{'imdb': imdb, 'tvdb': tvdb}]
				meta2 = metacache.fetch(ids, meta_lang, user)[0]
				if not seasoncount:
					seasoncount = meta2.get('seasoncount', None)
				if not counts:
					counts = meta2.get('counts', None)
			except:
				log_utils.error()
				pass

		# make request, 3rd fallback
		if not seasoncount or not counts:
			try:
				if meta:
					season = meta.get('season')
				else:
					season = control.window.getProperty(self.seasonProperty)
				from resources.lib.indexers import tvdb_v1
				counts = tvdb_v1.get_counts(tvdb)
				seasoncount = counts[season]
			except:
				log_utils.error()
				return self.sources

		for i in self.sources:
			try:
				if 'package' in i:
					dsize = i.get('size')
					if not dsize:
						continue
					if i['package'] == 'season':
						divider = int(seasoncount)
						if not divider:
							continue
					else:
						if not counts:
							continue
						season_count = 1
						divider = 0
						while season_count <= int(i['last_season']):
							divider += int(counts[str(season_count)])
							season_count += 1
					float_size = float(dsize) / divider
					if round(float_size, 2) == 0:
						continue
					str_size = '%.2f GB' % float_size

					info = i['info']
					try:
						info = [i['info'].split(' | ', 1)[1]]
					except:
						info = []

					info.insert(0, str_size)
					info = ' | '.join(info)
					i.update({'size': float_size, 'info': info})
				else:
					continue

			except:
				log_utils.error()
				continue
		return self.sources


	# @timeIt
	def pm_cache_chk_list(self, torrent_List, d):
		if len(torrent_List) == 0:
			return
		try:
			hashList = [i['hash'] for i in torrent_List]
			cached = premiumize.Premiumize().check_cache_list(hashList)
			count = 0
			for i in torrent_List:
				if cached[count] is False:
					if 'package' in i:
						i.update({'source': 'uncached (pack) torrent'})
					else:
						i.update({'source': 'uncached torrent'})
				else:
					if 'package' in i:
						i.update({'source': 'cached (pack) torrent'})
					else:
						i.update({'source': 'cached torrent'})
				count += 1
			return torrent_List
		except:
			log_utils.error()
			pass


	# @timeIt
	def rd_cache_chk_list(self, torrent_List, d):
		if len(torrent_List) == 0:
			return
		try:
			hashList = [i['hash'] for i in torrent_List]
			cached = realdebrid.RealDebrid().check_cache_list(hashList)
			for i in torrent_List:
				if 'rd' not in cached.get(i['hash'].lower(), {}):
					if 'package' in i:
						i.update({'source': 'uncached (pack) torrent'})
					else:
						i.update({'source': 'uncached torrent'})
					continue
				elif len(cached[i['hash'].lower()]['rd']) >= 1:
					if 'package' in i:
						i.update({'source': 'cached (pack) torrent'})
					else:
						i.update({'source': 'cached torrent'})
				else:
					if 'package' in i:
						i.update({'source': 'uncached (pack) torrent'})
					else:
						i.update({'source': 'uncached torrent'})
			return torrent_List
		except:
			log_utils.error()
			pass


	def clr_item_providers(self, title, year, imdb, tvdb, season, episode, tvshowtitle, premiered):
		providerscache.remove(self.getSources, title, year, imdb, tvdb, season, episode, tvshowtitle, premiered) # function cache removal of item
		# if not season:
			# season = episode = ''
		try:
			dbcon = database.connect(self.sourceFile)
			dbcur = dbcon.cursor()
			dbcur.execute("SELECT count(name) FROM sqlite_master WHERE type='table' AND name='rel_url'")
			if dbcur.fetchone()[0] == 1: # table exists so both all will
				dbcur.execute(
					"DELETE FROM rel_url WHERE imdb_id = '%s'" % imdb)
				dbcur.execute(
					"DELETE FROM rel_src WHERE imdb_id = '%s'" % imdb)
				dbcur.connection.commit()
				dbcon.close()
		except:
			log_utils.error()
			pass


	# @timeIt
	def movie_chk_imdb(self, imdb, title, year):
		try:
			if not imdb or imdb == '0':
				raise Exception()
			result = client.request('https://v2.sg.media-imdb.com/suggestion/t/{}.json'.format(imdb))
			result = json.loads(result)['d'][0]
			year_ck = str(result['y'])
			title_ck = result['l'].encode('utf-8')
			if not year_ck or not title_ck:
				raise Exception()
			if year != year_ck:
				year = year_ck
			if title != title_ck:
				title = title_ck
			return year, title
		except:
			log_utils.error()
			return year, title


	def tmdbhelper_fix(self, imdb, year):
		try:
			if not imdb or imdb == '0':
				raise Exception()
			result = client.request('https://v2.sg.media-imdb.com/suggestion/t/{}.json'.format(imdb))
			result = json.loads(result)['d'][0]
			year_ck = result['y']
			if not year_ck:
				raise Exception()
			if year != year_ck:
				year = year_ck
			return year
		except:
			log_utils.error()
			return year


	def get_season_info(self, imdb, tvdb, meta, season):
		total_seasons = None
		is_airing = None
		try:
			meta = json.loads(unquote(meta.replace('%22', '\\"')))
			total_seasons = meta.get('total_seasons', None)
			is_airing = meta.get('is_airing', None)
		except:
			pass

		# check metacache, 2nd fallback
		if not total_seasons or not is_airing:
			try:
				imdb_user = control.setting('imdb.user').replace('ur', '')
				tvdb_key_list = [
					'MDZjZmYzMDY5MGY5Yjk2MjI5NTcwNDRmMjE1OWZmYWU=',
					'MUQ2MkYyRjkwMDMwQzQ0NA==',
					'N1I4U1paWDkwVUE5WU1CVQ==']
				tvdb_key = tvdb_key_list[int(control.setting('tvdb.api.key'))]
				user = str(imdb_user) + str(tvdb_key)
				meta_lang = control.apiLanguage()['tvdb']
				ids = [{'imdb': imdb, 'tvdb': tvdb}]
				meta2 = metacache.fetch(ids, meta_lang, user)[0]
				if not total_seasons:
					total_seasons = meta2.get('total_seasons', None)
				if not is_airing:
					is_airing = meta2.get('is_airing', None)
			except:
				log_utils.error()
				pass

		# make request, 3rd fallback
		if not total_seasons:
			try:
				total_seasons = trakt.getSeasons(imdb, full=False)
				if total_seasons:
					total_seasons = [i['number'] for i in total_seasons]
					season_special = True if 0 in total_seasons else False
					total_seasons = len(total_seasons)
					if season_special:
						total_seasons = total_seasons - 1
			except:
				log_utils.error()
				pass

		if not is_airing:
			try:
				from resources.lib.indexers import tvdb_v1
				is_airing = tvdb_v1.get_is_airing(tvdb, season)
			except:
				log_utils.error()
				pass
		return total_seasons, is_airing


	def debrid_abv(self, debrid):
		try:
			d_dict = {'AllDebrid': 'AD', 'Linksnappy': 'LS', 'MegaDebrid': 'MD', 'Premiumize.me': 'PM', 'Real-Debrid': 'RD', 'Simply-Debrid': 'SD', 'Zevera': 'ZVR'}
			d = d_dict[debrid]
		except:
			log_utils.error()
			d = self.sources[i]['debrid'] = ''
			pass
		return d