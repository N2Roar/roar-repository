# -*- coding: utf-8 -*-

"""
	Venom Add-on
"""

import sys
from resources.lib.modules import control
from resources.lib.modules import log_utils
from resources.lib.modules import trakt

artPath = control.artPath()
traktCredentials = trakt.getTraktCredentialsInfo()
traktIndicators = trakt.getTraktIndicatorsInfo()
imdbCredentials = control.setting('imdb.user') != ''
tmdbSessionID = control.setting('tmdb.session_id') != ''
indexLabels = control.setting('index.labels') == 'true'
iconLogos = control.setting('icon.logos') != 'Traditional'


class Navigator:
	def root(self):
		self.addDirectoryItem(32001, 'movieNavigator', 'movies.png', 'DefaultMovies.png')
		self.addDirectoryItem(32002, 'tvNavigator', 'tvshows.png', 'DefaultTVShows.png')
		if control.getMenuEnabled('navi.anime'):
			self.addDirectoryItem('Anime', 'anime_Navigator', 'boxsets.png', 'DefaultFolder.png')
		if control.getMenuEnabled('mylists.widget'):
			self.addDirectoryItem(32003, 'mymovieNavigator', 'mymovies.png','DefaultVideoPlaylists.png')
			self.addDirectoryItem(32004, 'mytvNavigator', 'mytvshows.png', 'DefaultVideoPlaylists.png')

		if control.setting('newmovies.widget') != '0':
			indexer = 32478
			indexer_icon = 'imdb.png'
			setting = control.setting('newmovies.widget')
			if setting == '2':
				indexer = 32479
				indexer_icon = 'trakt.png'
			self.addDirectoryItem(indexer if indexLabels else 32477, 'newMovies', indexer_icon if iconLogos else 'latest-movies.png', 'DefaultRecentlyAddedMovies.png')

		if (traktCredentials and control.setting('tv.widget.alt') != '0') or (not traktCredentials and control.setting('tv.widget') != '0'):
			indexer = 32481
			indexer_icon = 'tvmaze.png'
			setting = control.setting('tv.widget.alt')
			if setting == '2' or setting == '3':
				indexer = 32482
				indexer_icon = 'trakt.png'
			self.addDirectoryItem(indexer if indexLabels else 32480, 'tvWidget', indexer_icon if iconLogos else 'latest-episodes.png', 'DefaultRecentlyAddedEpisodes.png')
			self.addDirectoryItem(32484 if indexLabels else 32483, 'calendar&url=added', 'tvmaze.png' if iconLogos else 'latest-episodes.png', 'DefaultTVShows.png', queue=True)

		if control.setting('furk.api') != '':
			self.addDirectoryItem('Furk.net', 'furkNavigator', 'movies.png',  'DefaultMovies.png')

		if control.getMenuEnabled('navi.youtube'):
			self.addDirectoryItem('You Tube Videos', 'youtube', 'youtube.png', 'youtube.png')

		self.addDirectoryItem(32010, 'searchNavigator', 'search.png', 'DefaultAddonsSearch.png')
		self.addDirectoryItem(32008, 'toolNavigator', 'tools.png', 'DefaultAddonService.png')

		downloads = True if control.setting('downloads') == 'true' and (len(control.listDir(control.setting('movie.download.path'))[0]) > 0 or len(control.listDir(control.setting('tv.download.path'))[0]) > 0) else False
		if downloads:
			self.addDirectoryItem(32009, 'downloadNavigator', 'downloads.png', 'DefaultFolder.png')

		if control.getMenuEnabled('navi.prem.services'):
			self.addDirectoryItem('Premium Services', 'premiumNavigator', 'premium.png', 'DefaultFolder.png')

		if control.getMenuEnabled('navi.news'):
			self.addDirectoryItem(32013, 'ShowNews', 'icon.png', 'DefaultAddonHelper.png', isFolder=False)
		if control.getMenuEnabled('navi.changelog'):
			self.addDirectoryItem(32014, 'ShowChangelog', 'icon.png', 'DefaultAddonsUpdates.png', isFolder=False)
		self.endDirectory()


	def furk(self):
		self.addDirectoryItem('User Files', 'furkUserFiles', 'mytvnavigator.png', 'mytvnavigator.png')
		self.addDirectoryItem('Search', 'furkSearch', 'search.png', 'search.png')
		self.endDirectory()


	def movies(self, lite=False):
		if control.getMenuEnabled('navi.movie.imdb.intheater'):
			self.addDirectoryItem(32421 if indexLabels else 32420, 'movies&url=theaters', 'imdb.png' if iconLogos else 'in-theaters.png', 'DefaultMovies.png')
		if control.getMenuEnabled('navi.movie.tmdb.nowplaying'):
			self.addDirectoryItem(32423 if indexLabels else 32422, 'tmdbmovies&url=tmdb_nowplaying', 'tmdb.png' if iconLogos else 'in-theaters.png', 'DefaultMovies.png')
		if control.getMenuEnabled('navi.movie.trakt.anticipated'):
			self.addDirectoryItem(32425 if indexLabels else 32424, 'movies&url=traktanticipated', 'trakt.png' if iconLogos else 'in-theaters.png', 'DefaultMovies.png')
		if control.getMenuEnabled('navi.movie.tmdb.upcoming'):
			self.addDirectoryItem(32427 if indexLabels else 32426, 'tmdbmovies&url=tmdb_upcoming', 'tmdb.png' if iconLogos else 'in-theaters.png', 'DefaultMovies.png')
		if control.getMenuEnabled('navi.movie.imdb.popular'):
			self.addDirectoryItem(32429 if indexLabels else 32428, 'movies&url=mostpopular', 'imdb.png' if iconLogos else 'most-popular.png', 'DefaultMovies.png')
		if control.getMenuEnabled('navi.movie.tmdb.popular'):
			self.addDirectoryItem(32431 if indexLabels else 32430, 'tmdbmovies&url=tmdb_popular', 'tmdb.png' if iconLogos else 'most-popular.png', 'DefaultMovies.png')
		if control.getMenuEnabled('navi.movie.trakt.popular'):
			self.addDirectoryItem(32433 if indexLabels else 32432, 'movies&url=traktpopular', 'trakt.png' if iconLogos else 'most-popular.png', 'DefaultMovies.png')
		if control.getMenuEnabled('navi.movie.imdb.boxoffice'):
			self.addDirectoryItem(32435 if indexLabels else 32434, 'movies&url=imdbboxoffice', 'imdb.png' if iconLogos else 'box-office.png', 'DefaultMovies.png')
		if control.getMenuEnabled('navi.movie.tmdb.boxoffice'):
			self.addDirectoryItem(32436 if indexLabels else 32434, 'tmdbmovies&url=tmdb_boxoffice', 'tmdb.png' if iconLogos else 'box-office.png', 'DefaultMovies.png')
		if control.getMenuEnabled('navi.movie.trakt.boxoffice'):
			self.addDirectoryItem(32437 if indexLabels else 32434, 'movies&url=traktboxoffice', 'trakt.png' if iconLogos else 'box-office.png', 'DefaultMovies.png')
		if control.getMenuEnabled('navi.movie.imdb.mostvoted'):
			self.addDirectoryItem(32439 if indexLabels else 32438, 'movies&url=mostvoted', 'imdb.png' if iconLogos else 'most-voted.png', 'DefaultMovies.png')
		if control.getMenuEnabled('navi.movie.tmdb.toprated'):
			self.addDirectoryItem(32441 if indexLabels else 32440, 'tmdbmovies&url=tmdb_toprated', 'tmdb.png' if iconLogos else 'most-voted.png', 'DefaultMovies.png')
		if control.getMenuEnabled('navi.movie.trakt.trending'):
			self.addDirectoryItem(32443 if indexLabels else 32442, 'movies&url=trakttrending', 'trakt.png' if iconLogos else 'trending.png', 'DefaultMovies.png')
		if control.getMenuEnabled('navi.movie.trakt.recommended'):
			self.addDirectoryItem(32445 if indexLabels else 32444, 'movies&url=traktrecommendations', 'trakt.png' if iconLogos else 'highly-rated.png', 'DefaultMovies.png')
		if control.getMenuEnabled('navi.movie.imdb.featured'):
			self.addDirectoryItem(32447 if indexLabels else 32446, 'movies&url=featured', 'imdb.png' if iconLogos else 'movies.png', 'DefaultMovies.png')
		if control.setting('newmovies.widget') != '0':
			self.addDirectoryItem(32478 if indexLabels else 32477, 'newMovies', 'imdb.png' if iconLogos else 'movies.png', 'DefaultRecentlyAddedMovies.png')
		if control.getMenuEnabled('navi.movie.collections'):
			self.addDirectoryItem(32000, 'collections_Navigator', 'boxsets.png', 'DefaultSets.png')
		if control.getMenuEnabled('navi.movie.imdb.oscarwinners'):
			self.addDirectoryItem(32452 if indexLabels else 32451, 'movies&url=oscars', 'imdb.png' if iconLogos else 'oscar-winners.png', 'DefaultMovies.png')
		if control.getMenuEnabled('navi.movie.imdb.oscarnominees'):
			self.addDirectoryItem(32454 if indexLabels else 32453, 'movies&url=oscarsnominees', 'imdb.png' if iconLogos else 'oscar-winners.png', 'DefaultMovies.png')
		if control.getMenuEnabled('navi.movie.imdb.genres'):
			self.addDirectoryItem(32456 if indexLabels else 32455, 'movieGenres', 'imdb.png' if iconLogos else 'genres.png', 'DefaultGenre.png')
		if control.getMenuEnabled('navi.movie.imdb.years'):
			self.addDirectoryItem(32458 if indexLabels else 32457, 'movieYears', 'imdb.png' if iconLogos else 'years.png', 'DefaultYear.png')
		if control.getMenuEnabled('navi.movie.imdb.people'):
			self.addDirectoryItem(32460 if indexLabels else 32459, 'moviePersons', 'imdb.png' if iconLogos else 'people.png', 'DefaultActor.png')
		if control.getMenuEnabled('navi.movie.imdb.languages'):
			self.addDirectoryItem(32462 if indexLabels else 32461, 'movieLanguages', 'imdb.png' if iconLogos else 'languages.png', 'DefaultAddonLanguage.png')
		if control.getMenuEnabled('navi.movie.imdb.certificates'):
			self.addDirectoryItem(32464 if indexLabels else 32463, 'movieCertificates', 'imdb.png' if iconLogos else 'certificates.png', 'DefaultMovies.png')

		if not lite:
			if control.getMenuEnabled('mylists.widget'):
				self.addDirectoryItem(32003, 'mymovieliteNavigator', 'mymovies.png', 'DefaultMovies.png')
			self.addDirectoryItem(32028, 'moviePerson', 'imdb.png' if iconLogos else 'people-search.png', 'DefaultAddonsSearch.png')
			self.addDirectoryItem(32010, 'movieSearch', 'trakt.png' if iconLogos else 'search.png', 'DefaultAddonsSearch.png')
		self.endDirectory()


	def mymovies(self, lite=False):
		self.accountCheck()
		self.addDirectoryItem(32039, 'movieUserlists', 'userlists.png', 'DefaultVideoPlaylists.png')
		if traktCredentials:
			if traktIndicators:
				self.addDirectoryItem(35308, 'moviesUnfinished&url=traktunfinished', 'trakt.png', 'DefaultVideoPlaylists.png', queue=True)
				self.addDirectoryItem(32036, 'movies&url=trakthistory', 'trakt.png', 'DefaultVideoPlaylists.png', queue=True)
			self.addDirectoryItem(32033, 'movies&url=traktwatchlist', 'trakt.png', 'DefaultVideoPlaylists.png', queue=True, context=(32551, 'library_moviesToLibrary&url=traktwatchlist&name=traktwatchlist'))
			self.addDirectoryItem(32032, 'movies&url=traktcollection', 'trakt.png', 'DefaultVideoPlaylists.png', queue=True, context=(32551, 'library_moviesToLibrary&url=traktcollection&name=traktcollection'))
		if imdbCredentials:
			self.addDirectoryItem(32033, 'movies&url=imdbwatchlist', 'imdb.png', 'DefaultVideoPlaylists.png', queue=True)
		if not lite:
			self.addDirectoryItem(32031, 'movieliteNavigator', 'movies.png', 'DefaultMovies.png')
			self.addDirectoryItem(32029, 'moviePerson', 'imdb.png' if iconLogos else 'people-search.png', 'DefaultAddonsSearch.png')
			self.addDirectoryItem(32010, 'movieSearch', 'search.png' if iconLogos else 'search.png', 'DefaultAddonsSearch.png')
		self.endDirectory()


	def tvshows(self, lite=False):
		if control.getMenuEnabled('navi.originals'):
			self.addDirectoryItem(40071 if indexLabels else 40070, 'tvOriginals', 'tvmaze.png' if iconLogos else 'networks.png', 'DefaultNetwork.png')
		if control.getMenuEnabled('navi.tv.imdb.popular'):
			self.addDirectoryItem(32429 if indexLabels else 32428, 'tvshows&url=popular', 'imdb.png' if iconLogos else 'most-popular.png', 'DefaultTVShows.png')
		if control.getMenuEnabled('navi.tv.tmdb.popular'):
			self.addDirectoryItem(32431 if indexLabels else 32430, 'tmdbTvshows&url=tmdb_popular', 'tmdb.png' if iconLogos else 'most-popular.png', 'DefaultTVShows.png')
		if control.getMenuEnabled('navi.tv.trakt.popular'):
			self.addDirectoryItem(32433 if indexLabels else 32432, 'tvshows&url=traktpopular', 'trakt.png' if iconLogos else 'most-popular.png', 'DefaultTVShows.png', queue=True)
		if control.getMenuEnabled('navi.tv.imdb.mostvoted'):
			self.addDirectoryItem(32439 if indexLabels else 32438, 'tvshows&url=views', 'imdb.png' if iconLogos else 'most-voted.png', 'DefaultTVShows.png')
		if control.getMenuEnabled('navi.tv.tmdb.toprated'):
			self.addDirectoryItem(32441 if indexLabels else 32440, 'tmdbTvshows&url=tmdb_toprated', 'tmdb.png' if iconLogos else 'most-voted.png', 'DefaultTVShows.png')
		if control.getMenuEnabled('navi.tv.trakt.trending'):
			self.addDirectoryItem(32443 if indexLabels else 32442, 'tvshows&url=trakttrending', 'trakt.png' if iconLogos else 'trending.png', 'DefaultTVShows.png')
		if control.getMenuEnabled('navi.tv.imdb.highlyrated'):
			self.addDirectoryItem(32449 if indexLabels else 32448, 'tvshows&url=rating', 'imdb.png' if iconLogos else 'highly-rated.png', 'DefaultTVShows.png')
		if control.getMenuEnabled('navi.tv.trakt.recommended'):
			self.addDirectoryItem(32445 if indexLabels else 32444, 'tvshows&url=traktrecommendations', 'trakt.png' if iconLogos else 'highly-rated.png', 'DefaultTVShows.png', queue=True)
		if control.getMenuEnabled('navi.tv.imdb.genres'):
			self.addDirectoryItem(32456 if indexLabels else 32455, 'tvGenres', 'imdb.png' if iconLogos else 'genres.png', 'DefaultGenre.png')
		if control.getMenuEnabled('navi.tv.tvmaze.networks'):
			self.addDirectoryItem(32470 if indexLabels else 32469, 'tvNetworks', 'tvmaze.png' if iconLogos else 'networks.png', 'DefaultNetwork.png')
		if control.getMenuEnabled('navi.tv.imdb.languages'):
			self.addDirectoryItem(32462 if indexLabels else 32461, 'tvLanguages', 'imdb.png' if iconLogos else 'languages.png', 'DefaultAddonLanguage.png')
		if control.getMenuEnabled('navi.tv.imdb.certificates'):
			self.addDirectoryItem(32464 if indexLabels else 32463, 'tvCertificates', 'imdb.png' if iconLogos else 'certificates.png', 'DefaultTVShows.png')
		if control.getMenuEnabled('navi.tv.tmdb.airingtoday'):
			self.addDirectoryItem(32467 if indexLabels else 32465, 'tmdbTvshows&url=tmdb_airingtoday', 'tmdb.png' if iconLogos else 'airing-today.png', 'DefaultRecentlyAddedEpisodes.png')
		if control.getMenuEnabled('navi.tv.imdb.airingtoday'):
			self.addDirectoryItem(32466 if indexLabels else 32465, 'tvshows&url=airing', 'imdb.png' if iconLogos else 'airing-today.png', 'DefaultRecentlyAddedEpisodes.png')
		if control.getMenuEnabled('navi.tv.tmdb.ontv'):
			self.addDirectoryItem(32472 if indexLabels else 32471, 'tmdbTvshows&url=tmdb_ontheair', 'tmdb.png' if iconLogos else 'new-tvshows.png', 'DefaultRecentlyAddedEpisodes.png')
		if control.getMenuEnabled('navi.tv.imdb.returningtvshows'):
			self.addDirectoryItem(32474 if indexLabels else 32473, 'tvshows&url=active', 'imdb.png' if iconLogos else 'returning-tvshows.png', 'DefaultRecentlyAddedEpisodes.png')
		if control.getMenuEnabled('navi.tv.imdb.newtvshows'):
			self.addDirectoryItem(32476 if indexLabels else 32475, 'tvshows&url=premiere', 'imdb.png' if iconLogos else 'new-tvshows.png', 'DefaultRecentlyAddedEpisodes.png')
		if control.getMenuEnabled('navi.tv.tvmaze.calendar'):
			self.addDirectoryItem(32450 if indexLabels else 32027, 'calendars', 'tvmaze.png' if iconLogos else 'calendar.png', 'DefaultYear.png')

		if (traktCredentials and control.setting('tv.widget.alt') != '0') or (not traktCredentials and control.setting('tv.widget') != '0'):
			self.addDirectoryItem(32006, 'tvWidget', 'latest-episodes.png', 'DefaultRecentlyAddedEpisodes.png')

		if not lite:
			if control.getMenuEnabled('mylists.widget'):
				self.addDirectoryItem(32004, 'mytvliteNavigator', 'mytvshows.png', 'DefaultTVShows.png')

			self.addDirectoryItem(32028, 'tvPerson', 'imdb.png' if iconLogos else 'people-search.png', 'DefaultAddonsSearch.png')
			self.addDirectoryItem(32010, 'tvSearch', 'trakt.png' if iconLogos else 'search.png', 'DefaultAddonsSearch.png')
		self.endDirectory()


	def mytvshows(self, lite=False):
		self.accountCheck()
		self.addDirectoryItem(32040, 'tvUserlists', 'userlists.png', 'DefaultVideoPlaylists.png')
		if traktCredentials:
			if traktIndicators:
				self.addDirectoryItem(35308, 'episodesUnfinished&url=traktunfinished', 'trakt.png', 'DefaultVideoPlaylists.png', queue=True)
				self.addDirectoryItem(32036, 'calendar&url=trakthistory', 'trakt.png', 'DefaultVideoPlaylists.png', queue=True)
				self.addDirectoryItem(32037, 'calendar&url=progress', 'trakt.png', 'DefaultVideoPlaylists.png', queue=True)
				self.addDirectoryItem(32027, 'calendar&url=mycalendar', 'trakt.png', 'DefaultYear.png', queue=True)
				self.addDirectoryItem(32033, 'tvshows&url=imdbwatchlist', 'imdb.png', 'DefaultVideoPlaylists.png')
			self.addDirectoryItem(32033, 'tvshows&url=traktwatchlist', 'trakt.png', 'DefaultVideoPlaylists.png', context=(32551, 'library_tvshowsToLibrary&url=traktwatchlist&name=traktwatchlist'))
			self.addDirectoryItem(32032, 'tvshows&url=traktcollection', 'trakt.png', 'DefaultVideoPlaylists.png', context=(32551, 'library_tvshowsToLibrary&url=traktcollection&name=traktcollection'))
			self.addDirectoryItem(32041, 'episodesUserlists', 'userlists.png', 'DefaultVideoPlaylists.png')
		if imdbCredentials:
			self.addDirectoryItem(32033, 'tvshows&url=imdbwatchlist', 'imdb.png', 'DefaultVideoPlaylists.png')
		if not lite:
			self.addDirectoryItem(32031, 'tvliteNavigator', 'tvshows.png', 'DefaultTVShows.png')
			self.addDirectoryItem(32030, 'tvPerson', 'imdb.png' if iconLogos else 'people-search.png', 'DefaultAddonsSearch.png')
			self.addDirectoryItem(32010, 'tvSearch', 'trakt.png' if iconLogos else 'search.png', 'DefaultAddonsSearch.png')
		self.endDirectory()


	def anime(self, lite=False):
		self.addDirectoryItem(32001, 'anime_Movies&url=anime', 'movies.png', 'DefaultMovies.png')
		self.addDirectoryItem(32002, 'anime_TVshows&url=anime', 'tvshows.png', 'DefaultTVShows.png')
		self.endDirectory()


	def tools(self):
		self.addDirectoryItem(32510, 'cache_Navigator', 'tools.png', 'DefaultAddonService.png', isFolder=True)
		self.addDirectoryItem(32609, 'resolveurlSettings&query=0.0', 'resolveURL.png', 'DefaultAddonService.png', isFolder=False)
		self.addDirectoryItem(32504, 'cache_clearResolveURLcache', 'resolveURL.png', 'DefaultAddonProgram.png', isFolder=False)
		if control.condVisibility('System.HasAddon(service.upnext)'):
			self.addDirectoryItem(32505, 'UpNextSettings', 'UpNext.png', 'DefaultAddonProgram.png', isFolder=False)
		self.addDirectoryItem(32506, 'contextVenomSettings', 'icon.png', 'DefaultAddonProgram.png', isFolder=False)
		#-- Providers - 4
		self.addDirectoryItem(32651, 'openscrapersSettings', 'OpenScrapers.png', 'DefaultAddonService.png', isFolder=False)
		self.addDirectoryItem(32083, 'cleanSettings', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
		#-- General - 0
		self.addDirectoryItem(32043, 'openSettings&query=0.0', 'tools.png', 'DefaultAddonService.png', isFolder=False)
		#-- Navigation - 1
		self.addDirectoryItem(32362, 'openSettings&query=1.1', 'tools.png', 'DefaultAddonService.png', isFolder=False)
		#-- Playback - 3
		self.addDirectoryItem(32045, 'openSettings&query=3.1', 'tools.png', 'DefaultAddonService.png', isFolder=False)
		#-- Api-keys - 8
		self.addDirectoryItem(32044, 'openSettings&query=8.0', 'tools.png', 'DefaultAddonService.png', isFolder=False)
		#-- Downloads - 10
		self.addDirectoryItem(32048, 'openSettings&query=10.0', 'tools.png', 'DefaultAddonService.png', isFolder=False)
		#-- Subtitles - 11
		self.addDirectoryItem(32046, 'openSettings&query=11.0', 'tools.png', 'DefaultAddonService.png', isFolder=False)
		self.addDirectoryItem(32556, 'library_Navigator', 'tools.png', 'DefaultAddonService.png', isFolder=True)
		self.addDirectoryItem(32049, 'viewsNavigator', 'tools.png', 'DefaultAddonService.png', isFolder=True)
		self.addDirectoryItem(32361, 'resetViewTypes', 'tools.png', 'DefaultAddonService.png', isFolder=False)
		self.addDirectoryItem(32073, 'authTrakt&opensettings=false', 'trakt.png', 'DefaultAddonService.png', isFolder=False)
		self.endDirectory()


	def cf(self):
		self.addDirectoryItem(32610, 'cache_clearAll&opensettings=false', 'tools.png', 'DefaultAddonService.png', isFolder=False)
		self.addDirectoryItem(32611, 'cache_clearSources&opensettings=false', 'tools.png', 'DefaultAddonService.png', isFolder=False)
		self.addDirectoryItem(32612, 'cache_clearMeta&opensettings=false', 'tools.png', 'DefaultAddonService.png', isFolder=False)
		self.addDirectoryItem(32613, 'cache_clearCache&opensettings=false', 'tools.png', 'DefaultAddonService.png', isFolder=False)
		self.addDirectoryItem(32614, 'cache_clearSearch&opensettings=false', 'tools.png', 'DefaultAddonService.png', isFolder=False)
		self.addDirectoryItem(32615, 'cache_clearBookmarks&opensettings=false', 'tools.png', 'DefaultAddonService.png', isFolder=False)
		self.endDirectory()


	def library(self):
	# -- Library - 9
		self.addDirectoryItem(32557, 'openSettings&query=9.0', 'tools.png', 'DefaultAddonProgram.png', isFolder=False)
		self.addDirectoryItem(32558, 'library_update', 'library_update.png', 'DefaultAddonLibrary.png', isFolder=False)
		self.addDirectoryItem(32676, 'library_clean', 'library_update.png', 'DefaultAddonLibrary.png', isFolder=False)
		self.addDirectoryItem(32559, control.setting('library.movie'), 'movies.png', 'DefaultMovies.png', isAction=False)
		self.addDirectoryItem(32560, control.setting('library.tv'), 'tvshows.png', 'DefaultTVShows.png', isAction=False)

		if traktCredentials:
			self.addDirectoryItem(32561, 'library_moviesToLibrary&url=traktcollection&name=traktcollection', 'trakt.png', 'DefaultMovies.png', isFolder=False)
			self.addDirectoryItem(32562, 'library_moviesToLibrary&url=traktwatchlist&name=traktwatchlist', 'trakt.png', 'DefaultMovies.png', isFolder=False)
			self.addDirectoryItem(32672, 'library_moviesListToLibrary&url=traktlists', 'trakt.png', 'DefaultMovies.png', isFolder=False)
			self.addDirectoryItem(32673, 'library_moviesListToLibrary&url=traktlikedlists', 'trakt.png', 'DefaultMovies.png', isFolder=False)

		if tmdbSessionID:
			self.addDirectoryItem('TMDb: Import Movie Watchlist...', 'library_moviesToLibrary&url=tmdb_watchlist&name=tmdb_watchlist', 'tmdb.png', 'DefaultMovies.png', isFolder=False)
			self.addDirectoryItem('TMDb: Import Movie Favorites...', 'library_moviesToLibrary&url=tmdb_favorites&name=tmdb_favorites', 'tmdb.png', 'DefaultMovies.png', isFolder=False)
			self.addDirectoryItem('TMDb: Import Movie User list...', 'library_moviesListToLibrary&url=tmdb_userlists', 'tmdb.png', 'DefaultMovies.png', isFolder=False)

		if traktCredentials:
			self.addDirectoryItem(32563, 'library_tvshowsToLibrary&url=traktcollection&name=traktcollection', 'trakt.png', 'DefaultTVShows.png', isFolder=False)
			self.addDirectoryItem(32564, 'library_tvshowsToLibrary&url=traktwatchlist&name=traktwatchlist', 'trakt.png', 'DefaultTVShows.png', isFolder=False)
			self.addDirectoryItem(32674, 'library_tvshowsListToLibrary&url=traktlists', 'trakt.png', 'DefaultMovies.png', isFolder=False)
			self.addDirectoryItem(32675, 'library_tvshowsListToLibrary&url=traktlikedlists', 'trakt.png', 'DefaultMovies.png', isFolder=False)

		if tmdbSessionID:
			self.addDirectoryItem('TMDb: Import TV Watchlist...', 'library_tvshowsToLibrary&url=tmdb_watchlist&name=tmdb_watchlist', 'tmdb.png', 'DefaultMovies.png', isFolder=False)
			self.addDirectoryItem('TMDb: Import TV Favorites...', 'library_tvshowsToLibrary&url=tmdb_favorites&name=tmdb_favorites', 'tmdb.png', 'DefaultMovies.png', isFolder=False)
			self.addDirectoryItem('TMDb: Import TV User list...', 'library_tvshowsListToLibrary&url=tmdb_userlists', 'tmdb.png', 'DefaultMovies.png', isFolder=False)
		self.endDirectory()


	def downloads(self):
		movie_downloads = control.setting('movie.download.path')
		tv_downloads = control.setting('tv.download.path')
		if len(control.listDir(movie_downloads)[0]) > 0:
			self.addDirectoryItem(32001, movie_downloads, 'movies.png', 'DefaultMovies.png', isAction=False)
		if len(control.listDir(tv_downloads)[0]) > 0:
			self.addDirectoryItem(32002, tv_downloads, 'tvshows.png', 'DefaultTVShows.png', isAction=False)
		self.endDirectory()


	def premium_services(self):
		self.addDirectoryItem(40057, 'pm_ServiceNavigator', 'premiumize.png', 'DefaultAddonService.png')
		self.addDirectoryItem(40058, 'rd_ServiceNavigator', 'realdebrid.png', 'DefaultAddonService.png')
		self.addDirectoryItem(40059, 'ad_ServiceNavigator', 'alldebrid.png', 'DefaultAddonService.png')
		self.endDirectory()


	def premiumize_service(self):
		pm_token = control.addon('script.module.resolveurl').getSetting('PremiumizeMeResolver_token')
		if pm_token:
			self.addDirectoryItem('Premiumize: My Files', 'pm_MyFiles', 'premiumize.png', 'DefaultAddonService.png')
			self.addDirectoryItem('Premiumize: Transfers', 'pm_Transfers', 'premiumize.png', 'DefaultAddonService.png')
			self.addDirectoryItem('Premiumize: Account Info', 'pm_AccountInfo', 'premiumize.png', 'DefaultAddonService.png', isFolder=False)
		self.addDirectoryItem('Premiumize: (Re)Authorize', 'pm_Authorize&opensettings=false', 'premiumize.png', 'DefaultAddonService.png', isFolder=False)
		self.endDirectory()


	def realdebrid_service(self):
		rd_token = control.addon('script.module.resolveurl').getSetting('RealDebridResolver_token')
		if rd_token:
			self.addDirectoryItem('Real-Debrid: Torrent Transfers', 'rd_UserTorrentsToListItem', 'realdebrid.png', 'DefaultAddonService.png')
			self.addDirectoryItem('Real-Debrid: My Downloads', 'rd_MyDownloads&query=1', 'realdebrid.png', 'DefaultAddonService.png')
			self.addDirectoryItem('Real-Debrid: Account Info', 'rd_AccountInfo', 'realdebrid.png', 'DefaultAddonService.png',isFolder=False )
		self.addDirectoryItem('Real-Debrid: (Re)Authorize', 'rd_Authorize', 'realdebrid.png', 'DefaultAddonService.png',isFolder=False )
		self.endDirectory()


	def alldebrid_service(self):
		ad_token = control.addon('script.module.resolveurl').getSetting('AllDebridResolver_token')
		if ad_token:
			self.addDirectoryItem('All-Debrid: Cloud Storage', 'ad_CloudStorage', 'alldebrid.png', 'DefaultAddonService.png')
			self.addDirectoryItem('All-Debrid: Transfers', 'ad_Transfers', 'alldebrid.png', 'DefaultAddonService.png')
			self.addDirectoryItem('All-Debrid: Account Info', 'ad_AccountInfo', 'alldebrid.png', 'DefaultAddonService.png', isFolder=False)
		self.addDirectoryItem('All-Debrid: (Re)Authorize', 'ad_Authorize', 'alldebrid.png', 'DefaultAddonService.png', isFolder=False)
		self.endDirectory()


	def search(self):
		self.addDirectoryItem(32001, 'movieSearch', 'trakt.png' if iconLogos else 'search.png', 'DefaultAddonsSearch.png')
		self.addDirectoryItem(32002, 'tvSearch', 'trakt.png' if iconLogos else 'search.png', 'DefaultAddonsSearch.png')
		self.addDirectoryItem(32029, 'moviePerson', 'imdb.png' if iconLogos else 'people-search.png', 'DefaultAddonsSearch.png')
		self.addDirectoryItem(32030, 'tvPerson', 'imdb.png' if iconLogos else 'people-search.png', 'DefaultAddonsSearch.png')
		self.endDirectory()


	def views(self):
		try:
			control.hide()
			items = [ (control.lang(32001), 'movies'), (control.lang(32002), 'tvshows'),
							(control.lang(32054), 'seasons'), (control.lang(32038), 'episodes') ]
			select = control.selectDialog([i[0] for i in items], control.lang(32049))
			if select == -1:
				return
			content = items[select][1]
			title = control.lang(32059)
			url = '%s?action=addView&content=%s' % (sys.argv[0], content)
			poster, banner, fanart = control.addonPoster(), control.addonBanner(), control.addonFanart()
			item = control.item(label=title)
			item.setInfo(type='video', infoLabels = {'title': title})
			item.setArt({'icon': poster, 'thumb': poster, 'poster': poster, 'fanart': fanart, 'banner': banner})
			item.setProperty('IsPlayable', 'false')
			control.addItem(handle = int(sys.argv[1]), url=url, listitem=item, isFolder=False)
			control.content(int(sys.argv[1]), content)
			control.directory(int(sys.argv[1]), cacheToDisc=True)
			from resources.lib.modules import views
			views.setView(content, {})
		except:
			log_utils.error()
			return


	def accountCheck(self):
		if not traktCredentials and not imdbCredentials:
			control.hide()
			control.notification(title='default', message=32042, icon='WARNING', sound=(control.setting('notification.sound') == 'true'))
			sys.exit()


	def infoCheck(self, version):
		try:
			control.notification(title='default', message=32074, icon='WARNING',  time=5000, sound=(control.setting('notification.sound') == 'true'))
			return '1'
		except:
			return '1'


	def clearCacheAll(self):
		control.hide()
		yes = control.yesnoDialog(control.lang(32077), '', '')
		if not yes:
			return
		try:
			from resources.lib.modules import cache
			cache.cache_clear_all()
			control.notification(title='default', message='All Cache Successfully Cleared!', icon='default', sound=(control.setting('notification.sound') == 'true'))
		except:
			log_utils.error()
			pass


	def clearCacheProviders(self):
		control.hide()
		yes = control.yesnoDialog(control.lang(32056), '', '')
		if not yes:
			return
		try:
			from resources.lib.modules import cache
			cache.cache_clear_providers()
			control.notification(title='default', message='Provider Cache Successfully Cleared!', icon='default', sound=(control.setting('notification.sound') == 'true'))
		except:
			log_utils.error()
			pass


	def clearCacheMeta(self):
		control.hide()
		yes = control.yesnoDialog(control.lang(32076), '', '')
		if not yes:
			return
		try:
			from resources.lib.modules import cache
			cache.cache_clear_meta()
			control.notification(title='default', message='Metadata Cache Successfully Cleared!', icon='default', sound=(control.setting('notification.sound') == 'true'))
		except:
			log_utils.error()
			pass


	def clearCache(self):
		control.hide()
		yes = control.yesnoDialog(control.lang(32056), '', '')
		if not yes:
			return
		try:
			from resources.lib.modules import cache
			cache.cache_clear()
			control.notification(title='default', message='Cache Successfully Cleared!', icon='default', sound=(control.setting('notification.sound') == 'true'))
		except:
			log_utils.error()
			pass


	def clearCacheSearch(self):
		control.hide()
		yes = control.yesnoDialog(control.lang(32056), '', '')
		if not yes:
			return
		try:
			from resources.lib.modules import cache
			cache.cache_clear_search()
			control.notification(title='default', message='Search History Successfully Cleared!', icon='default', sound=(control.setting('notification.sound') == 'true'))
		except:
			log_utils.error()
			pass


	def clearCacheSearchPhrase(self, table, name):
		control.hide()
		yes = control.yesnoDialog(control.lang(32056), '', '')
		if not yes:
			return
		try:
			from resources.lib.modules import cache
			cache.cache_clear_SearchPhrase(table, name)
			control.notification(title='default', message='Search Phrase Successfully Cleared!', icon='default', sound=(control.setting('notification.sound') == 'true'))
		except:
			log_utils.error()
			pass


	def clearBookmarks(self):
		control.hide()
		yes = control.yesnoDialog(control.lang(32056), '', '')
		if not yes:
			return
		try:
			from resources.lib.modules import cache
			cache.cache_clear_bookmarks()
			control.notification(title='default', message='Bookmarks Successfully Cleared!', icon='default', sound=(control.setting('notification.sound') == 'true'))
		except:
			log_utils.error()
			pass


	def clearBookmark(self, name, year):
		control.hide()
		yes = control.yesnoDialog(control.lang(32056), '', '')
		if not yes:
			return
		try:
			from resources.lib.modules import cache
			cache.cache_clear_bookmark(name, year)
			control.notification(title=name, message='Bookmark Successfully Cleared!', icon='default', sound=(control.setting('notification.sound') == 'true'))
		except:
			log_utils.error()
			pass


	def addDirectoryItem(self, name, query, thumb, icon, context=None, queue=False, isAction=True, isFolder=True, isPlayable=False, isSearch=False, table=''):
		sysaddon = sys.argv[0]
		syshandle = int(sys.argv[1])
		try:
			if type(name) is str or type(name) is unicode:
				name = str(name)
			if type(name) is int:
				name = control.lang(name)
		except:
			log_utils.error()

		url = '%s?action=%s' % (sysaddon, query) if isAction else query
		thumb = control.joinPath(artPath, thumb) if artPath else icon
		if not icon.startswith('Default'):
			icon = control.joinPath(artPath, icon)
		cm = []
		queueMenu = control.lang(32065)
		if queue:
			cm.append((queueMenu, 'RunPlugin(%s?action=playlist_QueueItem)' % sysaddon))
		if context:
			cm.append((control.lang(context[0]), 'RunPlugin(%s?action=%s)' % (sysaddon, context[1])))
		if isSearch:
			try:
				from urllib import quote_plus
			except:
				from urllib.parse import quote_plus
			cm.append(('Clear Search Phrase', 'RunPlugin(%s?action=cache_clearSearchPhrase&source=%s&name=%s)' % (sysaddon, table, quote_plus(name))))
		cm.append(('[COLOR red]Venom Settings[/COLOR]', 'RunPlugin(%s?action=openSettings)' % sysaddon))
		item = control.item(label=name)
		item.addContextMenuItems(cm)
		if isPlayable:
			item.setProperty('IsPlayable', 'true')
		else:
			item.setProperty('IsPlayable', 'false')
		item.setArt({'icon': icon, 'poster': thumb, 'thumb': thumb, 'fanart': control.addonFanart(), 'banner': thumb})
		control.addItem(handle=syshandle, url=url, listitem=item, isFolder= isFolder)


	def endDirectory(self):
		syshandle = int(sys.argv[1])
		control.content(syshandle, 'addons')
		control.directory(syshandle, cacheToDisc=True)