# -*- coding: utf-8 -*-
import sys
import requests
from urllib import urlencode, quote_plus
from urlparse import parse_qsl

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

from Lib.SimpleCache import cache

# Disable urllib3's "InsecureRequestWarning: Unverified HTTPS request is being made" warnings.
requests.packages.urllib3.disable_warnings(
    requests.packages.urllib3.exceptions.InsecureRequestWarning
)

# Changelog:
#   0.3.10:
#       - Added support for episodes thumbnail and subtitles (see settings).
#       - Adapt to API changes.
#       - Code cleanup and refactor (remember to update your Kodi favorites).
#
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

ADDON_VERSION = '0.3.10'
USER_AGENT = 'CTOONKodi/' + ADDON_VERSION + ' (JSON API; +https://github.com/doko-desuka/plugin.video.ctoonkodi)'
USER_AGENT_KODI = '|User-Agent=' + quote_plus(USER_AGENT) # Custom header(s) for Kodi to use when fetching stuff.

PLUGIN_ID = int(sys.argv[1])
PLUGIN_URL = sys.argv[0]

ADDON = xbmcaddon.Addon()

# TVDB api key exclusively for CTOON Kodi, for future use (e.g. getting episode plots etc.).
#TVDB_API_KEY = '0HVVMAMIQQNCTWV7'

PROPERTY_SHOWS = 'ctoonkodi.shows'
PROPERTY_SEASONS_TEMPLATE = 'ctoonkodi.seasons_' # Incomplete value, used on actionSeasonsMenu().


# =====================================================================================


def actionShowsMenu(params):
    # Estuary skin has better layout for this than for 'tvshows' content.
    xbmcplugin.setContent(PLUGIN_ID, 'episodes')

    cache.saveCacheIfDirty() # Try saving the cache on the main menu, if necessary.

    showsData = getCacheProperty(PROPERTY_SHOWS, route='')
    if showsData:
        def _showsItemsGen():
            for showData in showsData:
                showThumb = showData['cover']+USER_AGENT_KODI if showData['cover'] else ''
                showName = showData['name']
                # imdbURL = showData['links']['imdb']
                # showIMDB = imdbURL[imdbURL.rfind('/') + 1:]  # Show IMDB ID ('tt#######'), useful for getting metadata.
                showPlot = showData['description']

                # Make a main menu item.
                # The 'episode' mediatype looks better on Estuary than 'tvshow'.
                item = makeListItem(
                    showName,
                    {'tvshowtitle': showName, 'plot': showPlot, 'mediatype': 'episode'},
                    showThumb
                )
                item.setArt({'fanart': showThumb}) # Additional art setup for main menu items, purely cosmetic.
                yield (
                    buildURL(
                        {
                            'action': 'actionSeasonsMenu',
                            'route': showData['short_name'],
                            'show': showName,
                            'plot': showPlot if showPlot else '',
                            'showThumb': showThumb
                        }
                    ),
                    item,
                    True
                )
            # Yield the settings item as well, after the loop.
            settingsItem = makeListItem(
                'Settings', {'plot': 'Change the add-on settings.'}, 'DefaultAddonService.png'
            )
            yield((buildURL({'action': 'actionSettingsScreen'}), settingsItem, False))

        xbmcplugin.addDirectoryItems(PLUGIN_ID, tuple(_showsItemsGen()))
    xbmcplugin.endOfDirectory(PLUGIN_ID, cacheToDisc=False)


def actionSeasonsMenu(params):
    xbmcplugin.setContent(PLUGIN_ID, 'seasons')
    route = params['route']

    # Retrieve and cache the seasons data from the full show data.
    seasonsData = getCacheProperty(PROPERTY_SEASONS_TEMPLATE + route, route, customKey='seasons')
    if seasonsData:
        def _seasonsItemsGen():
            showName = params['show']
            showPlot = params.get('plot', '')
            showThumb = params['showThumb']
            # Sort seasons and put the 'Extra' and 'Movie' seasons at the end of the list.
            orderedKeys = sorted(seasonsData.iterkeys(), key=lambda k: k if 'season' in k.lower() else 'z')
            for seasonKey in orderedKeys:
                # Use the first episode to get the season number.
                seasonNumber = seasonsData[seasonKey][0]['season']
                seasonNumber = int(seasonNumber) if seasonNumber and seasonNumber.isdigit() else 0
                item = makeListItem(
                    seasonKey,
                    {
                        'tvshowtitle': showName,
                        'plot': showPlot,
                        'season': seasonNumber,
                        'mediatype': 'season'
                    },
                    showThumb
                )
                yield (
                    buildURL(
                        {
                            'action': 'actionEpisodesMenu',
                            'route': route,
                            'season': seasonKey + '|' + str(seasonNumber),
                            'show': showName,
                            'showThumb': showThumb
                        }
                    ),
                    item,
                    True
                )

        xbmcplugin.addDirectoryItems(PLUGIN_ID, tuple(_seasonsItemsGen()))
    xbmcplugin.endOfDirectory(PLUGIN_ID, cacheToDisc=False)


def actionEpisodesMenu(params):
    xbmcplugin.setContent(PLUGIN_ID, 'episodes')
    route = params['route']

    seasonsData = getCacheProperty(PROPERTY_SEASONS_TEMPLATE + route, route) # Cache contains the seasons data.
    if seasonsData:
        def _episodesItemsGen():
            showName = params['show']
            showThumb = params['showThumb']
            seasonKey, seasonNumber = params['season'].split('|')
            seasonNumber = int(seasonNumber)
            # Handle media type for each season type: "Season (...)", "Movie" and "Extra".
            mediaType = 'episode' if 'Season' in seasonKey else 'movie' if 'Movie' in seasonKey else 'video'
            showThumbnails = (ADDON.getSetting('thumbnails') == 'true')
            useSubtitlesContextMenu = (ADDON.getSetting('subtitles') == 'Disabled')

            for episodeData in seasonsData[seasonKey]:
                episodeTitle = episodeData['title']
                if seasonNumber:
                    label = episodeData['sxe']['short'] + ' | ' + episodeTitle
                else:
                    label = seasonKey + ' | ' + episodeTitle
                # Get episode number. Handles single episodes names ('8') and double episode names ('20_21').
                episodeNumbers = episodeData['episode'].split('_')
                episodeDate = episodeData['published_date'][:10] # 10 = len('yyyy-mm-dd')

                if episodeData['thumbnail'] and showThumbnails:
                    episodeThumb = episodeData['thumbnail']+USER_AGENT_KODI
                else:
                    episodeThumb = showThumb

                item = makeListItem(
                    label,
                    {
                        'tvshowtitle': showName,
                        'title': episodeTitle,
                        'season': seasonNumber,
                        'episode': episodeNumbers[0],
                        'aired': episodeDate,
                        'premiered': episodeDate, # According to the docs 'premiered' is what makes Kodi display a date.
                        'year': int(episodeDate.split('-')[0]),
                        'mediatype': mediaType
                    },
                    episodeThumb
                )
                item.setProperty('IsPlayable', 'true') # Allows the checkmark to be placed on watched episodes.
                itemURL = buildURL(
                    {
                        'action': 'actionPlay',
                        'route': route + '/' + str(episodeData['id']),
                        'label': label,
                        'date': episodeDate,
                        'mediaType': mediaType
                    }
                )
                if useSubtitlesContextMenu:
                    item.addContextMenuItems(
                        [('Play with Subtitles', 'PlayMedia(' + itemURL + '&forceSubtitles)')]
                    )
                yield (itemURL, item, False)

        xbmcplugin.addDirectoryItems(PLUGIN_ID, tuple(_episodesItemsGen()))
    xbmcplugin.endOfDirectory(PLUGIN_ID)


def actionPlay(params):
    cache.saveCacheIfDirty() # Try saving the cache before playing an episode, if necessary.

    data = ctoonGET(params['route'])
    episodeData = data['episode']

    # Sort stream data in pairs of integer video size (1080, 720, 480 etc.) and URL string.
    streamItems = sorted(
        ((int(quality), url) for quality, url in episodeData['files']['webm'].iteritems()),
        key = lambda m: m[0],
        reverse = True # Sort from biggest quality to lowest quality.
    )

    # Recreate the item with the exact same infolabels, or Kodi replaces the item in the list after playback stops.
    item = makeListItem(
        params['label'],
        {
            'tvshowtitle': xbmc.getInfoLabel('ListItem.TVShowTitle'),
            'title': xbmc.getInfoLabel('ListItem.Title'),
            'season': xbmc.getInfoLabel('ListItem.Season'),
            'episode': xbmc.getInfoLabel('ListItem.Episode'), #int(xbmc.getInfoLabel('ListItem.Episode')),
            'aired': params['date'], # Using a parameter to avoid having to parse the 'dd/mm/yyyy' InfoLabel.
            'premiered': params['date'],
            'year': xbmc.getInfoLabel('ListItem.Year'),
            'mediatype': params['mediaType']
        }
    )
    item.setMimeType('video/webm')
    item.setContentLookup(False) # Avoids Kodi's MIME-type request.

    streamURL = None
    if ADDON.getSetting('autoplay') != 'Disabled':
        # Find the exact quality the user wants, or the next smaller quality.
        desiredResolution = int(autoplaySetting[:-1]) # Strip the 'p' from the quality name.
        for resolution, url in streamItems:
            if resolution <= desiredResolution:
                streamURL = url
                break
    else:
        # Display a dialog for selection. Order the qualities according to the setting.
        qualityOrder = {
            quality: index
            for index, quality in enumerate(ADDON.getSetting('qualityOrder').replace(' ', '').split(','))
        }
        sortedQualityItems = sorted(
            (xbmcgui.ListItem(str(item[0])+'p', item[1]) for item in streamItems),
            key = lambda m: qualityOrder.get(m.getLabel(), 1)
        )
        index = xbmcgui.Dialog().select('Select Quality', sortedQualityItems, useDetails=True)
        if index >= 0:
            streamURL = sortedQualityItems[index].getLabel2()

    if streamURL:
        # Load subtitles if available.
        if ADDON.getSetting('subtitles') != 'Disabled' or 'forceSubtitles' in params:
            if episodeData['files']['subtitles']:
                subsList = sorted(
                    (xbmcgui.ListItem(name.upper(), url) for name, url in episodeData['files']['subtitles'].iteritems()),
                    key = lambda m: 0 if 'EN' in m.getLabel() else 1 # Order EN (English) before all others.
                )
                index = xbmcgui.Dialog().select(
                    'Load subtitles?', subsList + [xbmcgui.ListItem('None', "(Don't use subtitles)")], useDetails=True
                )
                if index < len(subsList):
                    if index != -1:
                        item.setSubtitles([subsList[index].getLabel2() + USER_AGENT_KODI])
                    else:
                        streamURL = None # Cancel playback if the subtitle dialog is cancelled.
                else:
                    pass # User chose "None", play but with no subtitles.                    
            elif 'forceSubtitles' in params:
                # Show a notification to the user because he came in from the context menu.
                xbmc.sleep(1000)
                notification('No subtitles found', delay=2000, useSound=False)

    if streamURL:
        item.setPath(streamURL + USER_AGENT_KODI) # Set the User-Agent header when Kodi is streaming.
        xbmcplugin.setResolvedUrl(PLUGIN_ID, True, item)
    else:
        xbmcplugin.setResolvedUrl(PLUGIN_ID, False, xbmcgui.ListItem())


def actionSettingsScreen(params):
    # View that shows the add-on settings dialog.
    # 'openSettings()' is a modal dialog, so the plugin won't continue from here until the user closes\confirms it.
    xbmcaddon.Addon().openSettings()


def actionClearCache(params):
    if cache.clearCacheFiles():
        notification('Cache files cleared', 3000, False)
    # Close the settings dialog when it was opened from within this add-on.
    if 'ctoonkodi' in xbmc.getInfoLabel('Container.PluginName'):
        xbmc.executebuiltin('Dialog.Close(all)')


def buildURL(query):
    # Helper function to build a Kodi xbmcgui.ListItem URL string.
    # query -> A dictionary of parameters to put in the item URL.
    return (PLUGIN_URL + '?' + urlencode({k: v.encode('utf-8') if isinstance(v, unicode)
                                           else unicode(v, errors='ignore').encode('utf-8')
                                           for k, v in query.iteritems()}))


def makeListItem(label, videoMetadata=None, thumb=None):
    item = xbmcgui.ListItem(label)
    if videoMetadata:
        item.setInfo('video', videoMetadata)
    if thumb:
        item.setArt({'icon': thumb, 'thumb': thumb, 'poster': thumb})
    return item


def notification(message, delay=3000, useSound=True):
    xbmcgui.Dialog().notification('CTOON Kodi', message, xbmcgui.NOTIFICATION_INFO, delay, useSound)
    return None


def ctoonGET(route=''):
    try:
        r = requests.get(
            'https://ctoon.party/api/1.1/' + route, headers={'User-Agent': USER_AGENT}, timeout=10, verify=False
        )
        return r.json() if r.ok else notification('Could not connect to CTOON')
    except requests.exceptions.Timeout:
        return notification('Request to CTOON timed out')
    except:
        return notification('Web request failed')


def getCacheProperty(propertyName, route, customKey=None):
    data = cache.getCacheProperty(propertyName, readFromDisk=True)
    if not data:
        data = ctoonGET(route)
        if data:
            if customKey:
                data = data[customKey] # Filter the data by key, if needed.
            # Create a disk-enabled property, lifetime of one day.
            cache.setCacheProperty(propertyName, data, saveToDisk=True, lifetime=24)
    return data


def main():
    params = dict(parse_qsl(sys.argv[2][1:], keep_blank_values=True))
    globals()[params.get('action', 'actionShowsMenu')](params) # Call the action function, defaults to actionShowsMenu().
