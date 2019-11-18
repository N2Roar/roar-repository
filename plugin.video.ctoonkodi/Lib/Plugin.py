# -*- coding: utf-8 -*-
import sys
import json
import requests
from urllib import urlencode
from urlparse import parse_qs
from ast import literal_eval

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

#from Lib.SimpleTVDB import simpleTVDB as tvdb
from Lib.SimpleCache import simpleCache as cache


ADDON_VERSION = '0.3.9'


# Changelog:
#   0.3.9:
#       - Refactored code.
#       - Added disk and memory caching.
#       - Added plugin settings (autoplay, clear cache).
#
#   0.3.1:
#       - Minor fixes.
#
#   0.3.0:
#       - Added support for the ctoon web API.
#       - Code cleanup and improvement.
#
#   0.2.0:
#       - Initial release.


BASEURL = 'https://ctoon.party'

USER_AGENT = 'CTOONKodi/' + ADDON_VERSION + ' (JSON API; +https://github.com/doko-desuka/plugin.video.ctoonkodi)'

ADDON = xbmcaddon.Addon()
ADDON_SETTINGS = dict()

PROPERTY_SHOWS = 'ctoonkodi.prop.shows'
PROPERTY_SEASONS_TEMPLATE = 'ctoonkodi.prop.seasons_' # Used with the 'short_name' of each show.

#===================================================================================

def viewShows(params):
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes') # Estuary skin has better layout for this than for 'tvshows' content.

    cache.saveCacheIfDirty() # Try saving the cache on the main menu, if necessary.

    showsData = getShowsProperty()
    if showsData:

        def _viewShowsItems():
            for showData in showsData:
                thumb = BASEURL + showData['cover'] if showData['cover'] else ''
                showName = showData['name']
                imdbURL = showData['links']['imdb']
                showIMDB = imdbURL[imdbURL.rfind('/')+1 : ] # Show IMDB ID ('tt#######'), useful for getting metadata.
                showPlot = showData['description']

                item = xbmcgui.ListItem(showName)
                if thumb:
                    item.setArt({'icon': thumb, 'thumb': thumb, 'poster': thumb, 'fanart': thumb})
                # 'episode' mediatype looks better on Estuary than 'tvshow'.
                item.setInfo('video', {'tvshowtitle': showName, 'plot': showPlot, 'mediatype': 'episode'})
                yield (
                    buildURL(
                        {
                            'view': 'SEASONS',
                            'route': showData['short_name'],
                            'show': showName,
                            'plot': showPlot if showPlot else '',
                            'thumb': thumb
                        }
                    ),
                    item,
                    True
                )
            # Yield the settings item as well, after the loop.
            settingsItem = xbmcgui.ListItem('Settings')
            settingsItem.setInfo('video', {'plot': 'Change the add-on settings.'})
            _settingsIcon = ADDON.getAddonInfo('path') + '/resources/media/IconSettings.png'
            settingsItem.setArt({key: _settingsIcon for key in ('icon', 'thumb', 'poster', 'fanart')})
            yield((buildURL({'view':'SETTINGS'}), settingsItem, False))

        xbmcplugin.addDirectoryItems(int(sys.argv[1]), tuple(_viewShowsItems()))

    xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=False)


def viewSeasons(params):
    xbmcplugin.setContent(int(sys.argv[1]), 'seasons')

    route = params['route']

    seasonsData = getSeasonsProperty(route)
    if seasonsData:

        def _viewSeasonsItems():
            showName = params['show']
            showPlot = params.get('plot', '')
            thumb = params['thumb']
            # Sort seasons and put the 'Extra' and 'Movie' seasons at the end of the list.
            orderedKeys = sorted(seasonsData.iterkeys(), key = lambda k: k if k.lower().startswith('season') else 'z')
            for seasonKey in orderedKeys:
                item = xbmcgui.ListItem(seasonKey)
                item.setArt({'thumb': thumb, 'poster': thumb})
                seasonNumber = seasonsData[seasonKey][0]['season'] # Use the first episode to get the season number.
                seasonNumber = int(seasonNumber) if seasonNumber and seasonNumber.isdigit() else 0
                item.setInfo(
                    'video', {'tvshowtitle': showName, 'plot': showPlot, 'season': seasonNumber, 'mediatype': 'season'}
                )
                yield (
                    buildURL(
                        {
                            'view': 'EPISODES',
                            'route': route,
                            'season': ','.join((seasonKey, str(seasonNumber))),
                            'show': showName,
                            'plot': showPlot,
                            'thumb': thumb
                        }
                    ),
                    item,
                    True
                )

        xbmcplugin.addDirectoryItems(int(sys.argv[1]), tuple(_viewSeasonsItems()))

    xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc=False)


def viewEpisodes(params):
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')

    route = params['route']

    seasonsData = getSeasonsProperty(route)
    if seasonsData:

        def _viewEpisodesItems():
            showName = params['show']
            showPlot = params['plot']
            thumb = params['thumb']
            seasonKey, seasonNumber = params['season'].split(',')
            seasonNumber = int(seasonNumber)
            # Handle media type for each season type: "Season (...)", "Movie" and "Extra".
            mediaType = 'episode' if 'Season' in seasonKey else 'movie' if 'Movie' in seasonKey else 'video'
            dateLength = len('yyyy-mm-dd')

            for episodeData in seasonsData[seasonKey]:
                episodeTitle = episodeData['title']
                if seasonNumber:
                    label = episodeData['sxe']['short'] + ' | ' + episodeTitle
                else:
                    label = seasonKey + ' | ' + episodeTitle
                # Get episode number. Handles single episodes names ('8') and double episode names ('20_21').
                episodeNumbers = episodeData['episode'].split('_')
                episodeDate = episodeData['published_date'][:dateLength]

                item = xbmcgui.ListItem(label)
                item.setArt({'icon': thumb, 'thumb': thumb, 'poster': thumb})
                # Infolabels to pass on to the viewMedia() function and to allow users to favourite individual
                # episodes.
                infoLabels = {
                    'tvshowtitle': showName,
                    'title': episodeTitle,
                    'plot': showPlot,
                    'season': seasonNumber,
                    'episode': episodeNumbers[0],
                    'aired': episodeDate,
                    'premiered': episodeDate, # According to the docs 'premiered' is what makes Kodi display a date.
                    'year': int(episodeDate.split('-')[0]),
                    'mediatype': mediaType
                }
                item.setInfo('video', infoLabels)
                item.setProperty('IsPlayable', 'true') # Allows the checkmark to be placed on watched episodes.
                yield (
                    buildURL(
                        {
                            'view': 'MEDIA',
                            'route': route + '/' + str(episodeData['id']),
                            'label': label,
                            'thumb': thumb,
                            'infoLabels': str(infoLabels)
                        }
                    ),
                    item,
                    False
                )

        xbmcplugin.addDirectoryItems(int(sys.argv[1]), tuple(_viewEpisodesItems()))

    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def viewMedia(params):
    cache.saveCacheIfDirty() # Try saving the cache before playing an episode, if necessary.

    data = ctoonGET(params['route'])
    episodeData = data['episode']

    # Sorted pairs of video size ("1080", "720", "480" etc.) and stream URL.
    streamItems = sorted(
        ((int(item[0]), BASEURL + item[1]) for item in episodeData['files']['webm'].iteritems()),
        key = lambda m: m[0],
        reverse = True # Sorts from biggest quality to lowest quality.
    )
    # Recreate the item with the same infolabels, otherwise Kodi overwrites the item that was selected from the list.
    item = xbmcgui.ListItem(params['label'])
    thumb = params['thumb']
    item.setArt({'icon': thumb, 'thumb': thumb, 'poster': thumb})
    item.setInfo('video', literal_eval(params['infoLabels']))
    item.setMimeType('video/webm')
    item.setProperty('IsPlayable', 'true')

    if ADDON_SETTINGS['autoplay']:
        # Find the exact quality the user wants, or the next smaller quality.
        desiredQuality = int(ADDON_SETTINGS['autoplay'])
        for streamQuality, streamURL in streamItems:
            if streamQuality <= desiredQuality:
                item.setPath(streamURL)
                xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
                return
    else:
        # Display a dialog for selection.
        index = xbmcgui.Dialog().select('Select Quality', tuple(str(sItem[0]) for sItem in streamItems), useDetails=True)
        if index >= 0:
            item.setPath(streamItems[index][1])
            xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
            return

            '''
            An alternative playing method, to be used if something else needs to be done afterwards
            like auto-loading subtitles etc. (such a thing can't be done with 'setResolvedUrl()'):
            xbmc.Player().play(url=streamURL, listitem=item)
            '''

    # Fall-through: failed to resolve.
    xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, item)


def viewSettings(params):
    '''
    View that shows the add-on settings dialog.
    '''
    ADDON.openSettings() # Modal dialog, so the plugin won't continue from this point until user closes\confirms it.
    reloadSettings() # So right after that is a good time to update the globals.


def viewClearCache(params):
    if cache.clearCacheFiles():
        notification('Cache files cleared', 3000, False)
    # Close the settings dialog when it was opened from within this add-on.
    if 'ctoonkodi' in xbmc.getInfoLabel('Container.PluginName'):
        xbmc.executebuiltin('Dialog.Close(all)')


#==================================================================================	=


def buildURL(query):
    '''
    Helper function to build a Kodi xbmcgui.ListItem URL.
    :param query: Dictionary of url parameters to put in the URL.
    :returns: A formatted and urlencoded URL string.
    '''
    return (sys.argv[0] + '?' + urlencode({k: v.encode('utf-8') if isinstance(v, unicode)
                                           else unicode(v, errors='ignore').encode('utf-8')
                                           for k, v in query.iteritems()}))


def reloadSettings():
    global ADDON_SETTINGS
    autoplay = ADDON.getSetting('autoplay')
    ADDON_SETTINGS['autoplay'] = int(autoplay) if autoplay != 'Disabled' else 0


def notification(message, delay=3000, useSound=True):
    xbmcgui.Dialog().notification('CTOON Kodi', message, xbmcgui.NOTIFICATION_INFO, delay, useSound)


def ctoonGET(route = ''):
    try:
        r = requests.get(BASEURL + '/api/' + route, headers={'User-Agent': USER_AGENT}, timeout=10)
        if r.ok:
            return r.json()
        else:
            notification('Could not connect to CTOON')
    except requests.exceptions.Timeout:
        notification('Request to CTOON timed out')
    return None # Fall-through.


def getShowsProperty():
    showsData = cache.getCacheProperty(PROPERTY_SHOWS, readFromDisk=True)
    if not showsData:
        showsData = ctoonGET()
        if showsData:
            # Create a disk-enabled property, lifetime of five days.
            cache.setCacheProperty(PROPERTY_SHOWS, showsData, saveToDisk=True, lifetime=cache.LIFETIME_FIVE_DAYS)
    return showsData


def getSeasonsProperty(route):
    propName = PROPERTY_SEASONS_TEMPLATE + route
    seasonsData = cache.getCacheProperty(propName, readFromDisk=True)
    if not seasonsData:
        temp = ctoonGET(route)
        if temp and 'seasons' in temp:
            seasonsData = temp['seasons']
            cache.setCacheProperty(propName, seasonsData, saveToDisk=True, lifetime=cache.LIFETIME_FIVE_DAYS)
    return seasonsData


#===================================================================================


VIEWS_DICT = {
    'SHOWS': viewShows, # View all shows.
    'SEASONS': viewSeasons, # View all seasons of a show.
    'EPISODES': viewEpisodes, # View all episodes of a season.

    'MEDIA': viewMedia, # View all media URLs of an episode \ autoplay.

    'SETTINGS': viewSettings, # Settings dialog.
    'CLEAR_CACHE': viewClearCache # Clear the cache file.
}


# Global scope, initialises the ADDON_SETTINGS dict.
reloadSettings()


def main():
    params = {key: value[0] for key, value in parse_qs(sys.argv[2][1:], keep_blank_values=True).iteritems()}
    view = VIEWS_DICT[params.get('view', 'SHOWS')](params)