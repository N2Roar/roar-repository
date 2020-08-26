# -*- coding: utf-8 -*-

'''
	Venom Add-on
'''

from sys import argv
import xbmcaddon
import xbmcgui

try:
	from urlparse import parse_qsl
	from urllib import quote_plus
except:
	from urllib.parse import parse_qsl, quote_plus

from resources.lib.modules import control

params = dict(parse_qsl(argv[2].replace('?','')))

action = params.get('action')
id = params.get('id')
name = params.get('name')
title = params.get('title')
year = params.get('year')
imdb = params.get('imdb')
tmdb = params.get('tmdb')
tvdb = params.get('tvdb')
season = params.get('season')
episode = params.get('episode')
tvshowtitle = params.get('tvshowtitle')
premiered = params.get('premiered')
type = params.get('type')
url = params.get('url')
meta = params.get('meta')
query = params.get('query')
source = params.get('source')

windowedtrailer = params.get('windowedtrailer')
windowedtrailer = int(windowedtrailer) if windowedtrailer in ("0","1") else 0

homeWindow = xbmcgui.Window(10000)
playAction = xbmcaddon.Addon('plugin.video.venom').getSetting('hosts.mode')
autoPlay = 'true' if playAction == '2' else ''
homeWindow.setProperty('plugin.video.venom.autoPlay', autoPlay)


if action is None:
	from resources.lib.menus import navigator
	from resources.lib.modules import cache
	run = control.setting('first.info')
	if run == '':
		run = 'true' #clean install scenerio
	if cache._find_cache_version():
		run = 'true'
	if run == 'true':
		control.execute('RunPlugin(plugin://plugin.video.venom/?action=cleanSettings)')
		from resources.lib.modules import changelog
		changelog.get()
		control.setSetting(id='first.info', value='false')
	cache.cache_version_check()
	navigator.Navigator().root()


####################################################
#---News, Updates, and Help
####################################################
elif action == 'infoCheck':
	from resources.lib.menus import navigator
	navigator.Navigator().infoCheck('')

elif action == 'ShowNews':
	from resources.lib.modules import newsinfo
	newsinfo.news()

elif action == 'ShowChangelog':
	from resources.lib.modules import changelog
	changelog.get()

elif action == 'ShowHelp':
	from resources.help import help
	help.get(name)
	control.openSettings(query)


elif action == 'setReuseLanguageInvoker':
	control.set_reuselanguageinvoker()
	# control.openSettings(query)




####################################################
#---MOVIES
####################################################
elif action == 'movieNavigator':
	from resources.lib.menus import navigator
	navigator.Navigator().movies()

elif action == 'movieliteNavigator':
	from resources.lib.menus import navigator
	navigator.Navigator().movies(lite=True)

elif action == 'mymovieNavigator':
	from resources.lib.menus import navigator
	navigator.Navigator().mymovies()

elif action == 'mymovieliteNavigator':
	from resources.lib.menus import navigator
	navigator.Navigator().mymovies(lite=True)

elif action == 'movies':
	from resources.lib.menus import movies
	movies.Movies().get(url)

elif action == 'moviePage':
	from resources.lib.menus import movies
	movies.Movies().get(url)

elif action == 'tmdbmovies':
	from resources.lib.menus import movies
	movies.Movies().getTMDb(url)

elif action == 'tmdbmoviePage':
	from resources.lib.menus import movies
	movies.Movies().getTMDb(url)

elif action == 'newMovies':
	from resources.lib.menus import movies
	movies.Movies().newMovies()

elif action == 'movieSearch':
	from resources.lib.menus import movies
	movies.Movies().search()

elif action == 'movieSearchnew':
	from resources.lib.menus import movies
	movies.Movies().search_new()

elif action == 'movieSearchterm':
	from resources.lib.menus import movies
	movies.Movies().search_term(name)

elif action == 'moviePerson':
	from resources.lib.menus import movies
	movies.Movies().person()

elif action == 'movieGenres':
	from resources.lib.menus import movies
	movies.Movies().genres()

elif action == 'movieLanguages':
	from resources.lib.menus import movies
	movies.Movies().languages()

elif action == 'movieCertificates':
	from resources.lib.menus import movies
	movies.Movies().certifications()

elif action == 'movieYears':
	from resources.lib.menus import movies
	movies.Movies().years()

elif action == 'moviePersons':
	from resources.lib.menus import movies
	movies.Movies().persons(url)

elif action == 'moviesUnfinished':
	from resources.lib.menus import movies
	movies.Movies().unfinished(url)

elif action == 'movieUserlists':
	from resources.lib.menus import movies
	movies.Movies().userlists()


####################################################
#---Collections
####################################################
if action and 'collections' in action:
	if action == 'collections_Navigator':
		from resources.lib.menus import collections
		collections.Collections().collections_Navigator()

	elif action == 'collections_Boxset':
		from resources.lib.menus import collections
		collections.Collections().collections_Boxset()

	elif action == 'collections_Kids':
		from resources.lib.menus import collections
		collections.Collections().collections_Kids()

	elif action == 'collections_BoxsetKids':
		from resources.lib.menus import collections
		collections.Collections().collections_BoxsetKids()

	elif action == 'collections_Superhero':
		from resources.lib.menus import collections
		collections.Collections().collections_Superhero()

	elif action == 'collections_MartialArts':
		from resources.lib.menus import collections
		collections.Collections().collections_martial_arts()

	elif action == 'collections_MartialArtsActors':
		from resources.lib.menus import collections
		collections.Collections().collections_martial_arts_actors()

	elif action == 'collections':
		from resources.lib.menus import collections
		collections.Collections().get(url)


####################################################
#---Furk
####################################################
if action and 'furk' in action:
	if action == "furkNavigator":
		from resources.lib.menus import navigator
		navigator.Navigator().furk()

	elif action == "furkMetaSearch":
		from resources.lib.menus import furk
		furk.Furk().furk_meta_search(url)

	elif action == "furkSearch":
		from resources.lib.menus import furk
		furk.Furk().search()

	elif action == "furkUserFiles":
		from resources.lib.menus import furk
		furk.Furk().user_files()

	elif action == "furkSearchNew":
		from resources.lib.menus import furk
		furk.Furk().search_new()


####################################################
# TV Shows
####################################################
if action == 'tvNavigator':
	from resources.lib.menus import navigator
	navigator.Navigator().tvshows()

elif action == 'tvliteNavigator':
	from resources.lib.menus import navigator
	navigator.Navigator().tvshows(lite=True)

elif action == 'mytvNavigator':
	from resources.lib.menus import navigator
	navigator.Navigator().mytvshows()

elif action == 'mytvliteNavigator':
	from resources.lib.menus import navigator
	navigator.Navigator().mytvshows(lite=True)

elif action == 'channels':
	from resources.lib.menus import channels
	channels.channels().get()

elif action == 'tvshows':
	from resources.lib.menus import tvshows
	tvshows.TVshows().get(url)

elif action == 'tvshowPage':
	from resources.lib.menus import tvshows
	tvshows.TVshows().get(url)

elif action == 'tmdbTvshows':
	from resources.lib.menus import tvshows
	tvshows.TVshows().getTMDb(url)

elif action == 'tmdbTvshowPage':
	from resources.lib.menus import tvshows
	tvshows.TVshows().getTMDb(url)

elif action == 'tvmazeTvshows':
	from resources.lib.menus import tvshows
	tvshows.TVshows().getTVmaze(url)

elif action == 'tvmazeTvshowPage':
	from resources.lib.menus import tvshows
	tvshows.TVshows().getTVmaze(url)

elif action == 'tvSearch':
	from resources.lib.menus import tvshows
	tvshows.TVshows().search()

elif action == 'tvSearchnew':
	from resources.lib.menus import tvshows
	tvshows.TVshows().search_new()

elif action == 'tvSearchterm':
	from resources.lib.menus import tvshows
	tvshows.TVshows().search_term(name)

elif action == 'tvPerson':
	from resources.lib.menus import tvshows
	tvshows.TVshows().person()

elif action == 'tvGenres':
	from resources.lib.menus import tvshows
	tvshows.TVshows().genres()

elif action == 'tvNetworks':
	from resources.lib.menus import tvshows
	tvshows.TVshows().networks()

elif action == 'tvLanguages':
	from resources.lib.menus import tvshows
	tvshows.TVshows().languages()

elif action == 'tvCertificates':
	from resources.lib.menus import tvshows
	tvshows.TVshows().certifications()

elif action == 'tvPersons':
	from resources.lib.menus import tvshows
	tvshows.TVshows().persons(url)

elif action == 'tvUserlists':
	from resources.lib.menus import tvshows
	tvshows.TVshows().userlists()


####################################################
#---SEASONS
####################################################
if action and 'seasons' in action:
	if action == 'seasons':
		from resources.lib.menus import seasons
		seasons.Seasons().get(tvshowtitle, year, imdb, tmdb, tvdb)

	elif action == 'seasonsUserlists':
		from resources.lib.indexers import seasons
		seasons.Seasons().userlists()

	elif action == 'seasonsList':
		from resources.lib.menus import seasons
		seasons.Seasons().seasonList(url)


####################################################
#---EPISODES
####################################################
if action == 'playEpisodesList':
	import json
	from resources.lib.menus import episodes
	items = episodes.Episodes().get(tvshowtitle, year, imdb, tmdb, tvdb, season, episode, idx=False)
	control.playlist.clear()
	for i in items:
		title = i['title']
		systitle = quote_plus(title)
		year = i['year']
		imdb = i['imdb']
		tvdb = i['tvdb']
		season = i['season']
		episode = i['episode']
		tvshowtitle = i['tvshowtitle']
		systvshowtitle = quote_plus(tvshowtitle)
		premiered = i['premiered']

		sysmeta = quote_plus(json.dumps(i))
		url = 'plugin://plugin.video.venom/?action=play&title=%s&year=%s&imdb=%s&tvdb=%s&season=%s&episode=%s&tvshowtitle=%s&premiered=%s&meta=%s&select="2"' % (
								systitle, year, imdb, tvdb, season, episode, systvshowtitle, premiered, sysmeta)
		item = control.item(label=title)
		control.playlist.add(url=url, listitem=item)
	control.player2().play(control.playlist)

elif action == 'episodes':
	from resources.lib.menus import episodes
	episodes.Episodes().get(tvshowtitle, year, imdb, tmdb, tvdb, season, episode)

elif action == 'episodesPage':
	from resources.lib.menus import episodes
	episodes.Episodes().get(tvshowtitle, year, imdb, tmdb, tvdb, season, episode)

elif action == 'tvWidget':
	from resources.lib.menus import episodes
	episodes.Episodes().widget()

elif action == 'calendar':
	from resources.lib.menus import episodes
	episodes.Episodes().calendar(url)

elif action == 'calendars':
	from resources.lib.menus import episodes
	episodes.Episodes().calendars()

elif action == 'episodesUnfinished':
	from resources.lib.menus import episodes
	episodes.Episodes().unfinished(url)

elif action == 'episodesUserlists':
	from resources.lib.menus import episodes
	episodes.Episodes().userlists()


####################################################
#---Premium Services
####################################################
elif action == 'premiumNavigator':
	from resources.lib.menus import navigator
	navigator.Navigator().premium_services()

elif action == 'premiumizeService':
	from resources.lib.menus import navigator
	navigator.Navigator().premiumize_service()

elif action == 'pmMyFiles':
	from resources.lib.modules import premiumize
	premiumize.Premiumize().my_files_to_listItem(id, name)

elif action == 'pmTransfers':
	from resources.lib.modules import premiumize
	premiumize.Premiumize().user_transfers_to_listItem()

elif action == 'pmAccountInfo':
	from resources.lib.modules import premiumize
	premiumize.Premiumize().acount_info_to_dialog()

elif action == 'pmAuthorize':
	from resources.lib.modules import premiumize
	premiumize.Premiumize().auth()

elif action == 'pmRename':
	from resources.lib.modules import premiumize
	premiumize.Premiumize().rename(type, id, name)

elif action == 'pmDelete':
	from resources.lib.modules import premiumize
	premiumize.Premiumize().delete(type, id, name)

elif action == 'pmDeleteTransfer':
	from resources.lib.modules import premiumize
	premiumize.Premiumize().delete_transfer(id, name)

elif action == 'pmClearFinishedTransfers':
	from resources.lib.modules import premiumize
	premiumize.Premiumize().clear_finished_transfers()

elif action == 'realdebridService':
	from resources.lib.menus import navigator
	navigator.Navigator().realdebrid_service()

elif action == 'rdUserTorrentsToListItem':
	from resources.lib.modules import realdebrid
	realdebrid.RealDebrid().user_torrents_to_listItem()

elif action == 'rdMyDownloads':
	from resources.lib.modules import realdebrid
	realdebrid.RealDebrid().my_downloads_to_listItem(int(query))

elif action == 'rdAccountInfo':
	from resources.lib.modules import realdebrid
	realdebrid.RealDebrid().user_info_to_dialog()

elif action == 'rdAuthorize':
	from resources.lib.modules import realdebrid
	realdebrid.RealDebrid().auth()

elif action == 'rdBrowseUserTorrents':
	from resources.lib.modules import realdebrid
	realdebrid.RealDebrid().browse_user_torrents(id)

elif action == 'rdDeleteUserTorrent':
	from resources.lib.modules import realdebrid
	realdebrid.RealDebrid().delete_user_torrent(id, name)

elif action == 'rdDeleteDownload':
	from resources.lib.modules import realdebrid
	realdebrid.RealDebrid().delete_download(id, name)



elif action == 'alldebridService':
	control.okDialog(title='default', message='Coming Soon!!')
	from resources.lib.menus import navigator
	navigator.Navigator().alldebrid_service()




####################################################
#---Anime
####################################################
if action and 'anime' in action:
	if action == 'animeNavigator':
		from resources.lib.menus import navigator
		navigator.Navigator().anime()

	elif action == 'animeMovies':
		from resources.lib.menus import movies
		movies.Movies().get(url)

	elif action == 'animeTVshows':
		from resources.lib.menus import tvshows
		tvshows.TVshows().get(url)


####################################################
#---Originals
####################################################
if action == 'originals':
	from resources.lib.menus import tvshows
	tvshows.TVshows().originals()


####################################################
#---YouTube
####################################################
elif action == 'youtube':
	from resources.lib.menus import youtube
	if id is None:
		youtube.yt_index().root(action)
	else:
		youtube.yt_index().get(action, id)

elif action == 'sectionItem':
    pass # Placeholder. This is a non-clickable menu item for notes, etc.



####################################################
#---Tools
####################################################
elif action == 'download':
	caller = params.get('caller')
	image = params.get('image')
	if caller == 'sources':
		control.busy()
		try:
			import json
			from resources.lib.modules import sources
			from resources.lib.modules import downloader
			downloader.download(name, image, sources.Sources().sourcesResolve(json.loads(source)[0], True))
		except:
			import traceback
			traceback.print_exc()
			pass
	if caller == 'premiumize':
		control.busy()
		try:
			from resources.lib.modules import downloader
			from resources.lib.modules import premiumize
			downloader.download(name, image, premiumize.Premiumize().add_headers_to_url(url.replace(' ', '%20')))
		except:
			import traceback
			traceback.print_exc()
			pass

	if caller == 'realdebrid':
		control.busy()
		try:
			from resources.lib.modules import downloader
			from resources.lib.modules import realdebrid
			if type == 'unrestrict':
				downloader.download(name, image, realdebrid.RealDebrid().unrestrict_link(url.replace(' ', '%20')))
			else:
				downloader.download(name, image, url.replace(' ', '%20'))
		except:
			import traceback
			traceback.print_exc()
			pass

	# if caller == 'alldebrid':
		# control.busy()
		# try:
			# from resources.lib.modules import downloader
			# from resources.lib.modules import alldebrid
			# downloader.download(name, image, alldebrid.AllDebrid().add_headers_to_url(url.replace(' ', '%20')))
		# except:
			# import traceback
			# traceback.print_exc()
			# pass


elif action == 'downloadNavigator':
	from resources.lib.menus import navigator
	navigator.Navigator().downloads()



elif action == 'libraryNavigator':
	from resources.lib.menus import navigator
	navigator.Navigator().library()

elif action == 'toolNavigator':
	from resources.lib.menus import navigator
	navigator.Navigator().tools()

elif action == 'searchNavigator':
	from resources.lib.menus import navigator
	navigator.Navigator().search()

elif action == 'viewsNavigator':
	from resources.lib.menus import navigator
	navigator.Navigator().views()

elif action == 'resetViewTypes':
	from resources.lib.modules import views
	views.clearViews()

elif action == 'cleanSettings':
	control.clean_settings()

elif action == 'addView':
	from resources.lib.modules import views
	content = params.get('content')
	views.addView(content)

elif action == 'refresh':
	control.refresh()

elif action == 'openSettings':
	control.openSettings(query)

elif action == 'open.Settings.CacheProviders':
	control.openSettings(query)

elif action == 'artwork':
	control.artwork()

elif action == 'UpNextSettings':
	control.openSettings('0.0', 'service.upnext')

elif action == 'contextVenomSettings':
	control.openSettings('0.0', 'context.venom')
	control.trigger_widget_refresh()

elif action == 'openscrapersSettings':
	control.openSettings('0.0', 'script.module.openscrapers')

elif action == 'urlResolver':
	try:
		import resolveurl
		resolveurl.display_settings()
	except:
		pass

elif action == 'urlResolverRDTorrent':
	control.openSettings(query, "script.module.resolveurl")


####################################################
#---Playcount
####################################################
elif action == 'moviePlaycount':
	from resources.lib.modules import playcount
	playcount.movies(name, imdb, query)

elif action == 'episodePlaycount':
	from resources.lib.modules import playcount
	playcount.episodes(name, imdb, tvdb, season, episode, query)

elif action == 'tvPlaycount':
	from resources.lib.modules import playcount
	playcount.tvshows(name, imdb, tvdb, season, query)


####################################################
#---Trakt
####################################################
elif action == 'traktManager':
	from resources.lib.modules import trakt
	trakt.manager(name, imdb, tvdb, season, episode)

elif action == 'authTrakt':
	from resources.lib.modules import trakt
	trakt.authTrakt()
	if params.get('opensettings') == 'true':
		control.openSettings(query, "plugin.video.venom")

elif action == 'cachesyncMovies':
	from resources.lib.modules import trakt
	trakt.cachesyncMovies()

elif action == 'cachesyncTVShows':
	from resources.lib.modules import trakt
	trakt.cachesyncTVShows()


####################################################
#---TMDb
####################################################
elif action == 'authTMDb':
	from resources.lib.indexers import tmdb
	tmdb.Auth().create_session_id()
	if params.get('opensettings') == 'true':
		control.openSettings(query, "plugin.video.venom")

elif action == 'revokeTMDb':
	from resources.lib.indexers import tmdb
	tmdb.Auth().revoke_session_id()
	if params.get('opensettings') == 'true':
		control.openSettings(query, "plugin.video.venom")


####################################################
#---Playlist
####################################################
elif action == 'playlistManager':
	from resources.lib.modules import playlist
	art = params.get('art')
	playlist.playlistManager(name, url, meta, art)

elif action == 'showPlaylist':
	from resources.lib.modules import playlist
	playlist.playlistShow()

elif action == 'clearPlaylist':
	from resources.lib.modules import playlist
	playlist.playlistClear()

elif action == 'queueItem':
	control.queueItem()
	if name is None:
		control.notification(title=35515, message=35519, icon='default', sound=(control.setting('notification.sound') == 'true'))
	else:
		control.notification(title=name, message=35519, icon='default', sound=(control.setting('notification.sound') == 'true'))



####################################################
#---Play
####################################################
elif action == 'play':
	from resources.lib.modules import sources
	rescrape = params.get('rescrape')
	select = params.get('select')
	sources.Sources().play(title, year, imdb, tvdb, season, episode, tvshowtitle, premiered, meta, select, rescrape)

elif action == 'playAll':
	control.player2().play(control.playlist)

elif action == 'playURL':
	caller = params.get('caller')
	if caller == 'realdebrid':
		from resources.lib.modules import realdebrid
		if type == 'unrestrict':
			control.player2().play(realdebrid.RealDebrid().unrestrict_link(url.replace(' ', '%20')))
		else:
			control.player2().play(url.replace(' ', '%20'))
	else:
		control.player2().play(url.replace(' ', '%20'))

elif action == 'playItem':
	from resources.lib.modules import sources
	sources.Sources().playItem(title, source)

elif action == 'addItem':
	from resources.lib.modules import sources
	sources.Sources().addItem(title)

elif action == 'alterSources':
	from resources.lib.modules import sources
	sources.Sources().alterSources(url, meta)

elif action == 'trailer':
	from resources.lib.modules import trailer
	trailer.Trailer().play(type, name, year, url, imdb, windowedtrailer)

elif action == 'showDebridPack':
	from resources.lib.modules.sources import Sources
	caller = params.get('caller')
	Sources().debridPackDialog(caller, name, url, source)

elif action == 'cacheTorrent':
	caller = params.get('caller')
	if caller == 'Real-Debrid':
		from resources.lib.modules.realdebrid import RealDebrid as debrid_function
	elif caller == 'Premiumize.me':
		from resources.lib.modules.premiumize import Premiumize as debrid_function
	debrid_function().create_transfer(url)

elif action == 'random':
	rtype = params.get('rtype')

	if rtype == 'movie':
		from resources.lib.menus import movies
		rlist = movies.Movies().get(url, idx=False)
		r = argv[0]+"?action=play"

	elif rtype == 'episode':
		from resources.lib.menus import episodes
		rlist = episodes.Episodes().get(tvshowtitle, year, imdb, tmdb, tvdb, season, idx=False)
		r = argv[0]+"?action=play"

	elif rtype == 'season':
		from resources.lib.menus import seasons
		rlist = seasons.Seasons().get(tvshowtitle, year, imdb, tmdb, tvdb, idx=False)
		r = argv[0]+"?action=random&rtype=episode"

	elif rtype == 'show':
		from resources.lib.menus import tvshows
		rlist = tvshows.TVshows().get(url, idx=False)
		r = argv[0]+"?action=random&rtype=season"

	from random import randint
	import json

	try:
		rand = randint(1,len(rlist))-1
		for p in ['title', 'year', 'imdb', 'tvdb', 'season', 'episode', 'tvshowtitle', 'premiered', 'select']:
			if rtype == "show" and p == "tvshowtitle":
				try:
					r += '&'+p+'='+quote_plus(rlist[rand]['title'])
				except:
					pass
			else:
				try:
					r += '&'+p+'='+quote_plus(rlist[rand][p])
				except:
					pass
		try:
			r += '&meta='+quote_plus(json.dumps(rlist[rand]))
		except:
			r += '&meta='+quote_plus("{}")
		if rtype == "movie":
			try:
				control.notification(title=32536, message=rlist[rand]['title'], icon='default', sound=(control.setting('notification.sound') == 'true'))
			except:
				pass
		elif rtype == "episode":
			try:
				control.notification(title=32536, message=rlist[rand]['tvshowtitle']+" - Season "+rlist[rand]['season']+" - "+rlist[rand]['title'], icon='default', sound=(control.setting('notification.sound') == 'true'))
			except:
				pass
		control.execute('RunPlugin(%s)' % r)
	except:
		control.notification(title='default', message=32537, icon='default', sound=(control.setting('notification.sound') == 'true'))

####################################################
#---Library Actions
####################################################
elif action == 'movieToLibrary':
	from resources.lib.modules import libtools
	libtools.libmovies().add(name, title, year, imdb, tmdb)

elif action == 'moviesToLibrary':
	from resources.lib.modules import libtools
	libtools.libmovies().range(url, name)

elif action == 'moviesListToLibrary':
	from resources.lib.menus import movies
	movies.Movies().moviesListToLibrary(url)

elif action == 'moviesToLibrarySilent':
	from resources.lib.modules import libtools
	libtools.libmovies().silent(url)

elif action == 'tvshowToLibrary':
	from resources.lib.modules import libtools
	libtools.libtvshows().add(tvshowtitle, year, imdb, tmdb, tvdb)

elif action == 'tvshowsToLibrary':
	from resources.lib.modules import libtools
	libtools.libtvshows().range(url, name)

elif action == 'tvshowsListToLibrary':
	from resources.lib.menus import tvshows
	tvshows.TVshows().tvshowsListToLibrary(url)

elif action == 'tvshowsToLibrarySilent':
	from resources.lib.modules import libtools
	libtools.libtvshows().silent(url)

elif action == 'updateLibrary':
	from resources.lib.modules import libtools
	libtools.libepisodes().update()
	libtools.libmovies().list_update()
	libtools.libtvshows().list_update()

elif action == 'cleanLibrary':
	from resources.lib.modules import libtools
	libtools.lib_tools().clean()

elif action == 'librarySetup':
	from resources.lib.modules import libtools
	libtools.lib_tools().total_setup()

elif action == 'service':
	from resources.lib.modules import libtools
	libtools.lib_tools().service()


####################################################
#---Clear Cache actions
####################################################
elif action == 'cfNavigator':
	from resources.lib.menus import navigator
	navigator.Navigator().cf()

elif action == 'clearAllCache':
	from resources.lib.menus import navigator
	navigator.Navigator().clearCacheAll()
	if params.get('opensettings') == 'true':
		control.openSettings(query, 'plugin.video.venom')

elif action == 'clearSources':
	from resources.lib.menus import navigator
	navigator.Navigator().clearCacheProviders()
	if params.get('opensettings') == 'true':
		control.openSettings(query, 'plugin.video.venom')

elif action == 'clearMetaCache':
	from resources.lib.menus import navigator
	navigator.Navigator().clearCacheMeta()
	if params.get('opensettings') == 'true':
		control.openSettings(query, 'plugin.video.venom')

elif action == 'clearCache':
	from resources.lib.menus import navigator
	navigator.Navigator().clearCache()
	if params.get('opensettings') == 'true':
		control.openSettings(query, 'plugin.video.venom')

elif action == 'clearCacheSearch':
	from resources.lib.menus import navigator
	navigator.Navigator().clearCacheSearch() 
	if params.get('opensettings') == 'true':
		control.openSettings(query, 'plugin.video.venom')

elif action == 'clearSearchPhrase':
	from resources.lib.menus import navigator
	navigator.Navigator().clearCacheSearchPhrase(source, name)

elif action == 'clearBookmarks':
	from resources.lib.menus import navigator
	navigator.Navigator().clearBookmarks()
	if params.get('opensettings') == 'true':
		control.openSettings(query, 'plugin.video.venom')

elif action == 'clearBookmark':
	from resources.lib.menus import navigator
	navigator.Navigator().clearBookmark(name, year)
	if params.get('opensettings') == 'true':
		control.openSettings(query, 'plugin.video.venom')

elif action == 'clearLocalBookmark':
	from resources.lib.modules import cache
	cache.clear_local_bookmark(url)

elif action == 'clearResolveURLcache':
	if control.condVisibility('System.HasAddon(script.module.resolveurl)'):
		control.execute('RunPlugin(plugin://script.module.resolveurl/?mode=reset_cache)')

elif action == 'widgetRefresh':
	control.trigger_widget_refresh()