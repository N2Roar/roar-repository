# -*- coding: utf-8 -*-
import re
import sys
from math import ceil
from itertools import chain, islice

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin

from Lib import parse_qsl, urlencode, DICT_ITER_ITEMS, DICT_ITER_KEYS, UNICODE
from Lib.Providers import getEpisodeProviders, resolveProviderURL
from Lib.SimpleCache import simpleCache as cache
from Lib.SimpleTrakt import SimpleTrakt as trakt
from Lib.RequestHelper import requestHelper
from Lib.CatalogHelper import catalogHelper
#from Lib.SimpleTVDB import tvdb # Unused. Potentially get per-episode thumbnails and descriptions in the future.

# Addon user settings. See also viewSettings() and reloadSettings().
ADDON = xbmcaddon.Addon()
ADDON_SETTINGS = dict()

# Dict to help translate 'layout_type_[name]' settings values into 'Container.SetViewMode()' values.
# These names and numbers were taken from the Estuary skin XML files:
# https://github.com/xbmc/xbmc/tree/master/addons/skin.estuary/xml
ADDON_VIEW_MODES = {
    'Wall' : '500',
    'Banner': '501',
    'List' : '50',
    'Poster' : '51',
    'Shift' : '53',
    'InfoWall' : '54',
    'WideList' : '55'
}


def viewMenu(params):
    '''
    Directory for the main add-on menu.
    '''
    cache.saveCacheIfDirty()

    def _menuItem(view, title, isFolder):
        return (buildURL({'view': view}), xbmcgui.ListItem(title), isFolder)

    listItems = (
        _menuItem('ANIMETOON_MENU', '[B][COLOR orange]Cartoons & Dubbed Anime[/COLOR][/B]', True),
        _menuItem('ANIMEPLUS_MENU', '[B][COLOR orange]Subbed Anime[/COLOR][/B]', True),
        _menuItem('SETTINGS', '[B][COLOR lavender]Settings[/COLOR][/B]', False)
    )
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), listItems)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def viewSettings(params):
    '''
    View that pops-up the add-on settings dialog, for convenience.
    '''
    ADDON.openSettings() # Modal dialog, so the program won't continue from this point until user closes\confirms it.
    reloadSettings() # So right after it is a good time to update the globals.


def viewClearCache(params):
    if cache.clearCacheFiles():
        dialog = xbmcgui.Dialog()
        dialog.notification('Toonmania2', 'Cache file cleared', xbmcgui.NOTIFICATION_INFO, 3500, True)

    # Close the settings dialog when it was opened from within this add-on.
    if 'toonmania2' in xbmc.getInfoLabel('Container.PluginName'):
        xbmc.executebuiltin('Dialog.Close(all)')


def viewAnimetoonMenu(params):
    '''
    Directory for the Animetoon website.
    '''
    cache.saveCacheIfDirty()

    def _animetoonItem(view, color, title, route):
        item = xbmcgui.ListItem('[B][COLOR %s]%s[/COLOR][/B]' % (color, title))
        item.setInfo( 'video', {'title': title, 'plot': title})
        return (buildURL({'view': view, 'api': requestHelper.API_ANIMETOON, 'route': route}), item, True)

    listItems = (
        _animetoonItem('CATALOG_MENU', 'lavender', 'Latest Updates', '/GetUpdates/'),
        _animetoonItem('CATALOG_MENU', 'darkorange', 'New Movies', '/GetNewMovies'),
        _animetoonItem('CATALOG_MENU', 'darkorange', 'All Movies', '/GetAllMovies'),
        _animetoonItem('CATALOG_MENU', 'darkorange', 'Popular Movies', '/GetPopularMovies'),
        _animetoonItem('CATALOG_MENU', 'lightsalmon', 'New Cartoons', '/GetNewCartoon'),
        _animetoonItem('CATALOG_MENU', 'lightsalmon', 'All Cartoons', '/GetAllCartoon'),
        _animetoonItem('CATALOG_MENU', 'lightsalmon', 'Popular Cartoons', '/GetPopularCartoon'),
        _animetoonItem('CATALOG_MENU', 'orange', 'New Dubbed Anime', '/GetNewDubbed'),
        _animetoonItem('CATALOG_MENU', 'orange', 'All Dubbed Anime', '/GetAllDubbed'),
        _animetoonItem('CATALOG_MENU', 'orange', 'Popular Dubbed Anime', '/GetPopularDubbed'),
        _animetoonItem('SEARCH_MENU', 'lavender', 'Search', '')
    )
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), listItems)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def viewAnimeplusMenu(params):
    '''
    Directory for the Animeplus website.
    '''
    def _animeplusItem(view, color, title, route):
        item = xbmcgui.ListItem('[B][COLOR %s]%s[/COLOR][/B]' % (color, title))
        item.setInfo( 'video', {'title': title, 'plot': title})
        return (buildURL({'view': view, 'api': requestHelper.API_ANIMEPLUS, 'route': route}), item, True)

    cache.saveCacheIfDirty()

    listItems = (
        _animeplusItem('CATALOG_MENU', 'lavender', 'Latest Updates', '/GetUpdates/'),
        _animeplusItem('CATALOG_MENU', 'lightsalmon', 'New Anime Movies', '/GetNewMovies'),
        _animeplusItem('CATALOG_MENU', 'lightsalmon', 'All Anime Movies', '/GetAllMovies'),
        _animeplusItem('CATALOG_MENU', 'lightsalmon', 'Popular Anime Movies', '/GetPopularMovies'),
        _animeplusItem('CATALOG_MENU', 'orange', 'New Subbed Anime', '/GetNewShows'),
        _animeplusItem('CATALOG_MENU', 'orange', 'All Subbed Anime', '/GetAllShows'),
        _animeplusItem('CATALOG_MENU', 'orange', 'Popular Subbed Anime', '/GetPopularShows'),
        _animeplusItem('SEARCH_MENU', 'lavender', 'Search', '')
    )
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), listItems)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def _viewSearchResults(params, text):
    '''
    Sub directory as an intermediary step before showing the search results catalog.
    This lets you favourite your search results so you can come back to them later.
    '''
    searchData = requestHelper.nameSearchEntries(params['api'], text) # Does the actual web requests.
    if searchData:
        # Make an item leading to the the 'ALL' catalog section instead of the main catalog menu, because
        # the name search results are usually fewer.
        params.update(
            {
                'view': 'CATALOG_SECTION',
                'section': 'ALL',
                'page': '0',
                'route': '_searchResults',
                'searchData': repr(searchData)
            }
        )

        # See if the user wants a favouritable search results item.
        if isSettingTrue('show_search_parent'):
            cache.saveCacheIfDirty()
            from string import capwords
            item = xbmcgui.ListItem('[COLOR orange][B]' + capwords(text) + '[/B][/COLOR] Search Results')
            item.setArt({'icon': 'DefaultFolder.png', 'thumb': 'DefaultFolder.png'})
            xbmcplugin.addDirectoryItem(int(sys.argv[1]), buildURL(params), item, True)
        else:
            # Show the results right now.
            viewCatalogSection(params)
            return
    else:
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), '', xbmcgui.ListItem('No Items Found'), False)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

    # Use the same layout settings as the main catalog menu.
    useCatalogLayout, layoutType = ADDON_SETTINGS['layoutCatalog']
    if useCatalogLayout:
        xbmc.executebuiltin('Container.SetViewMode(' + layoutType + ')')


def viewSearchMenu(params):
    '''
    Directory for a menu that lists search options.
    Used by both APIs.
    '''
    def _modalKeyboard(heading):
        kb = xbmc.Keyboard('', heading)
        kb.doModal()
        return kb.getText() if kb.isConfirmed() else None

    if params.get('route', None) == '_inputSearch':
        if params.get('query', '') != '':
            text = params.get('query')
        else:
            text = _modalKeyboard('Search by Name')
        if text:
            _viewSearchResults(params, text) # Sub directory that executes the search and shows results.
            return
        else:
            # User typed nothing or cancelled the keyboard.
            return # Returning like this w/o finishing the directory causes a log error, but it's the best UX imo.

    listItems = (
        (
            buildURL({'view': 'SEARCH_MENU', 'api': params['api'], 'route': '_inputSearch'}),
            xbmcgui.ListItem('[COLOR lavender][B]Search by Name[/B][/COLOR]'),
            True
        ),
        (
            buildURL({'view': 'SEARCH_GENRE', 'api': params['api'], 'route': '/GetGenres/'}),
            xbmcgui.ListItem('[COLOR lavender][B]Search by Genre[/B][/COLOR]'),
            True
        ),
        (
            buildURL({'view': 'TRAKT_MENU', 'api': params['api']}),
            xbmcgui.ListItem('[COLOR lavender][B]Search by Trakt List[/B][/COLOR]'),
            True
        )
    )
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), listItems)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def viewSearchGenre(params):
    '''
    Directory for a sub menu that lists the available genres to filter items by.
    The genre list is cached memory-only to last a Kodi session. This is done because
    if you hit "Back" Kodi would reload this directory and do a redundant web
    request...
    '''
    xbmcplugin.setContent(int(sys.argv[1]), 'tvshows') # Optional, influences the skin layout.

    api = params['api']
    route = params['route']

    if api == requestHelper.API_ANIMETOON:
        _PROPERTY_GENRE_NAMES = 'tmania2.prop.toonGenres'
    else:
        _PROPERTY_GENRE_NAMES = 'tmania2.prop.plusGenres'

    genreList = cache.getCacheProperty(_PROPERTY_GENRE_NAMES, readFromDisk = True)
    if not genreList:
        # The data from the '/GetGenres/' route is a dict with a list of genre names like "Action",
        # "Comedy" etc., but it also has some weird texts in the list probably from data entry errors.
        requestHelper.setAPISource(api)
        requestHelper.delayBegin()
        genreList = requestHelper.routeGET(route).get('genres', [ ])
        requestHelper.delayEnd()
        # Store the current API genres in a disk-persistent property with 1 week of lifetime.
        cache.setCacheProperty(_PROPERTY_GENRE_NAMES, genreList, saveToDisk = True, lifetime = cache.LIFETIME_ONE_WEEK)

    listItems = (
        (
            buildURL({'view': 'CATALOG_MENU', 'api': api, 'route': route, 'genreName': genreName}),
            xbmcgui.ListItem(genreName),
            True
        )
        for genreName in genreList
    )
    xbmcplugin.addDirectoryItems(int(sys.argv[1]), tuple(listItems))
    xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc = False)

    useCatalogLayout, layoutType = ADDON_SETTINGS['layoutCatalog']
    if useCatalogLayout:
        xbmc.executebuiltin('Container.SetViewMode(' + layoutType + ')')


def viewTraktMenu(params):
    '''
    Simple menu for accessing Trakt lists.
    '''
    if trakt.getInstance().ensureAuthorized(ADDON):

        def _traktMenuItems():
            icon = ADDON.getAddonInfo('icon')
            for list in trakt.getInstance().getUserLists(ADDON):
                item = xbmcgui.ListItem(list['name'])
                item.setArt({'icon': icon, 'thumb': icon, 'poster': icon})
                item.setInfo('video', {'title': list['name'], 'plot': list['description']})
                yield (
                    buildURL({'view': 'TRAKT_LIST', 'api': params['api'], 'traktList': str(list['ids']['trakt'])}),
                    item,
                    True
                )

        xbmcplugin.addDirectoryItems(int(sys.argv[1]), tuple(_traktMenuItems()))
        xbmcplugin.endOfDirectory(int(sys.argv[1])) # Only finished the directory if the user is authorized.


def viewTraktList(params):
    '''
    Lists the items of a specific Trakt user list.
    '''
    if trakt.getInstance().ensureAuthorized(ADDON):

        def _traktListItems():
            for itemName in sorted(trakt.getInstance().getListItems(params['traktList'], ADDON)):
                yield (
                    buildURL({'view': 'TRAKT_ITEM', 'api': params['api'], 'itemName': itemName}),
                    xbmcgui.ListItem(itemName),
                    True
                )

        xbmcplugin.addDirectoryItems(int(sys.argv[1]), tuple(_traktListItems()))
    xbmcplugin.endOfDirectory(int(sys.argv[1]))


def viewTraktItem(params):
    '''
    Searches for an item from a Trakt list.
    Same flow as manually searching, but uses the item name as query.
    '''
    _viewSearchResults(params, params['itemName'])


def viewClearTrakt(params):
    if 'toonmania2' in xbmc.getInfoLabel('Container.PluginName'):
        xbmc.executebuiltin('Dialog.Close(all)')

    # Kinda buggy behavior.
    # Need to wait a bit and recreate the xbmcaddon.Addon() reference, otherwise the settings
    # don't seem to be changed.
    # See https://forum.kodi.tv/showthread.php?tid=290353&pid=2425543#pid2425543.
    global ADDON
    xbmc.sleep(500)
    if trakt.clearTokens(ADDON):
        dialog = xbmcgui.Dialog()
        dialog.notification('Toonmania2', 'Trakt tokens cleared', xbmcgui.NOTIFICATION_INFO, 3500, False)

    ADDON = xbmcaddon.Addon()


def viewCatalogMenu(params):
    '''
    Directory for the catalog main menu, showing sections #, A, B, C, D, E... etc.
    The content of the catalog varies depending on the API and route the user chose.
    Empty sections are hidden.
    '''
    xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')

    catalog = catalogHelper.getCatalog(params)

    api = params['api']
    route = params['route']

    listItems = tuple(
        (
            buildURL({'view': 'CATALOG_SECTION', 'api': api, 'route': route, 'section': sectionKey, 'page': '0'}),
            xbmcgui.ListItem(sectionKey),
            True
        )
        for sectionKey in sorted(DICT_ITER_KEYS(catalog)) if len(catalog[sectionKey]) > 0
    )

    if len(listItems):
        sectionAll = ( # If the catalog has any items at all, add an "ALL" pseudo-section.
            buildURL({'view': 'CATALOG_SECTION', 'api': api, 'route': route, 'section': 'ALL', 'page': '0'}),
            xbmcgui.ListItem('All'),
            True
        )
        xbmcplugin.addDirectoryItems(int(sys.argv[1]), (sectionAll,) + listItems)
    else:
        xbmcplugin.addDirectoryItem(int(sys.argv[1]), '', xbmcgui.ListItem('No Items Found'), False)
    xbmcplugin.endOfDirectory(int(sys.argv[1]))

    # Custom layout settings.
    useCatalogLayout, layoutType = ADDON_SETTINGS['layoutCatalog']
    if useCatalogLayout:
        xbmc.executebuiltin('Container.SetViewMode(' + layoutType + ')')


def viewCatalogSection(params):
    '''
    Directory for listing items from a specific section of the catalog
    (section "C" for example, for C-titled entries).
    '''
    xbmcplugin.setContent(int(sys.argv[1]), 'tvshows')
    
    cache.saveCacheIfDirty()

    catalog = catalogHelper.getCatalog(params)
    showThumbs = isSettingTrue('show_thumbnails')
    sectionKey = params['section']

    def _catalogSectionItems(iterable):
        api = params['api']
        requestHelper.setAPISource(api) # Sets the right image thumb URL.

        for entry in iterable:
            # entry = (id, name, description, genres, dateReleased), see CatalogHelper.makeCatalogEntry() for more info.
            item = xbmcgui.ListItem(entry[1])
            thumb = requestHelper.makeThumbURL(entry[0]) if showThumbs else ''
            date = entry[4] if entry[4] else ''
            setupListItem(item, entry[1], entry[1], False, 0, 0, entry[3], thumb = thumb, plot = entry[2], date = date)
            yield (
                buildURL(
                    {
                        'view': 'LIST_EPISODES',
                        'api': api,
                        'id': entry[0],
                        'genres': ','.join(entry[3]) if entry[3] else '',
                        'thumb': thumb,
                        'plot': entry[2],
                        'date': date
                    }
                ),
                item,
                True
            )

            
            
    if showThumbs:
        # Display items in pages so the thumbs are loaded in chunks to not overburden the source website.
        page = int(params['page']) # Zero-based index.
        pageSize = int(ADDON.getSetting('page_size')) # Page size = number of items per catalog section page.
        start = page * pageSize
        stop = start + pageSize

        if sectionKey == 'ALL':
            # Create pages for the pseudo-section "ALL":
            # Flatten all sections into an iterable, which is then islice'd to get the current directory page.
            flatSections = chain.from_iterable(catalog[sectionKey] for sectionKey in sorted(DICT_ITER_KEYS(catalog)))
            itemsIterable = (entry for entry in islice(flatSections, start, stop))
            totalSectionPages = int(ceil(sum(len(section) for section in catalog.itervalues()) / float(pageSize)))
        else:
            # Do an islice of a specific section.
            itemsIterable = (entry for entry in islice(catalog[sectionKey], start, stop))
            totalSectionPages = int(ceil(len(catalog[sectionKey]) / float(pageSize))) # The 'float' is for Python 2.

        page += 1
        if totalSectionPages > 1 and page < totalSectionPages:
            params.update({'page':str(page)})
            nextPage = (buildURL(params), xbmcgui.ListItem('Next Page ('+str(page+1)+'/'+str(totalSectionPages)+')'), True)
            xbmcplugin.addDirectoryItems(int(sys.argv[1]), tuple(_catalogSectionItems(itemsIterable)) + (nextPage,))
        else:
            xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
            xbmcplugin.addDirectoryItems(int(sys.argv[1]), tuple(_catalogSectionItems(itemsIterable)))
    else:
        if sectionKey == 'ALL':
            itemsIterable = (
                entry for entry in chain.from_iterable(catalog[sectionKey] for sectionKey in sorted(DICT_ITER_KEYS(catalog)))
            )
        else:
            itemsIterable = (entry for entry in catalog[sectionKey])
        xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)
        xbmcplugin.addDirectoryItems(int(sys.argv[1]), tuple(_catalogSectionItems(itemsIterable)))

    xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc = False)

    # Custom layout.
    useShowsLayout, layoutType = ADDON_SETTINGS['layoutShows']
    if useShowsLayout:
        xbmc.executebuiltin('Container.SetViewMode(' + layoutType + ')')


def _makeEpisodeItems(api, episodes, showTitle, showGenres, showThumb, showPlot, showDate):
    '''
    Converts a list of JSON episode entries into a list of playable xbmcgui.ListItem
    with their 'view' url parameter set to 'RESOLVE'.
    This function is used only by viewListEpisodes().

    :param episodes: List of JSON episodes from the '/GetDetails/' routes of the APIs.
    :param p(...): Generic parameters from the parent show \ movie, inherited by the episodes.
    '''
    playlist = getPlaylist()

    for episodeEntry in episodes:
        #episode = dict( id=str, name=str, date=str='yyyy-MM-dd (...)' )
        name = episodeEntry['name']
        item = xbmcgui.ListItem(name)
        season, episode = getTitleInfo(name)
        # While the parent show\movie data uses 'released' as key for date value (value is 'yyyy-MM-dd'),
        # episode data uses 'date' as key for date value (value is 'yyyy-MM-dd hh:mm:ss').
        # The slice [:10] gets the length of 'yyyy-MM-dd'.
        episodeDate = episodeEntry['date'][ : 10] if 'date' in episodeEntry else showDate
        tempShowTitle = showTitle if showTitle else name # Try the show title first, fallback to episode name if empty.
        setupListItem(item, tempShowTitle, name, True, season, episode, showGenres, showThumb, showPlot, episodeDate)
        url = buildURL(
            {
                'view': 'RESOLVE',
                'api': api,
                'episodeID': episodeEntry['id'],
                'showTitle': showTitle,
                'name': name,
                'season': str(season),
                'episode': str(episode),
                'genres': ','.join(showGenres),
                'thumb': showThumb,
                'plot': showPlot,
                'date': episodeDate
            }
        )
        playlist.add(url, item)
        yield (url, item, False)


def _makeEpisodePartItems(episodeEntry, providers, showTitle, showGenres, showThumb, showPlot, showDate):
    '''
    Similar logic to _makeEpisodeItems(), but it works on just one item with multiple streams.
    This will make one (repeated) xbmc.ListItem for the several parts, each part points to a stream.
    '''
    playlist = getPlaylist()
    addedFirstProvider = False

    episodeName = episodeEntry['name']
    season, episode = getTitleInfo(episodeName)
    episodeDate = episodeEntry['date'][ : 10] if 'date' in episodeEntry else showDate

    for providerName, providerURLs in DICT_ITER_ITEMS(providers):
        for partIndex, providerURL in enumerate(providerURLs, 1):
            partName = '[B]%s[/B] | %s | [B]PART %i[/B]' % (providerName, episodeName, partIndex)
            item = xbmcgui.ListItem(partName)
            setupListItem(item, showTitle, partName, True, season, episode, showGenres, showThumb, showPlot, episodeDate)
            url = buildURL(
                {
                    'view': 'RESOLVE',
                    'showTitle': showTitle,
                    'name': partName, # Part name is later set as the item label used to play it.
                    'season': str(season),
                    'episode': str(episode),
                    'genres': ','.join(showGenres),
                    'thumb': showThumb,
                    'plot': showPlot,
                    'date': episodeDate,
                    'providerURL': providerURL
                }
            )
            if not addedFirstProvider:
                playlist.add(url, item)

            yield (url, item, False)

        addedFirstProvider = True


def viewListEpisodes(params):
    '''
    Directory for the list of episodes from a show.
    This is the last directory before playing a video.
    Pages aren't necessary in here even if the thumbnails setting is on, because
    for now all episodes use the same thumb and plot, inherited from the show.
    '''
    xbmcplugin.setContent(int(sys.argv[1]), 'episodes')

    # Sort episode list by labels. In some rare cases the episode date is set wrong,
    # so Kodi lists them out of order.
    xbmcplugin.addSortMethod(int(sys.argv[1]), xbmcplugin.SORT_METHOD_LABEL_IGNORE_THE)

    api = params['api']
    jsonData = None

    # Cache (memory-only) the episode list of the show, as the user might watch more than one in sequence.
    _PROPERTY_LAST_SHOW_DETAILS = 'tmania2.prop.lastShow'
    lastShowDetails = cache.getCacheProperty(_PROPERTY_LAST_SHOW_DETAILS, readFromDisk=False)
    showKey = params['id'] + api
    if lastShowDetails and showKey in lastShowDetails:
        jsonData = lastShowDetails[showKey] # Use the show ID + API name as the unique identifier.
    if not jsonData:
        requestHelper.setAPISource(api)
        requestHelper.delayBegin()
        jsonData = requestHelper.routeGET('/GetDetails/' + params['id'])
        if jsonData:
            cache.setCacheProperty(_PROPERTY_LAST_SHOW_DETAILS, {showKey: jsonData}, saveToDisk=False)
        requestHelper.delayEnd()

    # Genres, thumb and plot are taken from the parent show \ movie.
    # But the date of the parent show \ movie will only be used if the individual episode doesn't have a date itself.
    showTitle = jsonData.get('name', '')
    showGenres = params.get('genres', '').split(',')
    showThumb = params.get('thumb', '') # Might be empty in case 'show_thumbnails' setting is off.
    showPlot = params['plot']
    showDate = params.get('date', '')

    # If the JSON data for this show has more than one episode, list all the episodes as usual.
    if len(jsonData['episode']) > 1:
        xbmcplugin.addDirectoryItems(
            int(sys.argv[1]),
            tuple(_makeEpisodeItems(api, jsonData['episode'], showTitle, showGenres, showThumb, showPlot, showDate))
        )
    else:
        # For a single episode, this is probably a movie, OVA or special (considered as a "1 episode show").
        # Try to get the direct stream links to see if it's a movie (which are always multi-part).
        episodeEntry = jsonData['episode'][0]
        episodeProviders = None

        # Cache (memory-only) this request, as it might be for a multi part video (a movie)
        # where the user would go back and forth a lot on this view to watch all the movie parts.
        _PROPERTY_LAST_EPISODE_DETAILS = 'tmania2.prop.lastEpisode'
        lastEpisodeDetails = cache.getCacheProperty(_PROPERTY_LAST_EPISODE_DETAILS, readFromDisk=False)
        episodeKey = episodeEntry['id'] + api
        if lastEpisodeDetails and episodeKey in lastEpisodeDetails:
            episodeProviders = lastEpisodeDetails[episodeKey]
        else:
            episodeProviders = getEpisodeProviders(api, episodeEntry['id'])
            if episodeProviders:
                cache.setCacheProperty(_PROPERTY_LAST_EPISODE_DETAILS, {episodeKey: episodeProviders}, saveToDisk=False)

        if episodeProviders:
            if len(next(episodeProviders.itervalues())) > 1: # If it's a multi-video-part media.
                xbmcplugin.addDirectoryItems(
                    int(sys.argv[1]),
                    tuple(
                        _makeEpisodePartItems(
                            episodeEntry, episodeProviders, showTitle, showGenres, showThumb, showPlot, showDate
                        )
                    )
                )
            else:
                # The item doesn't have multiple video parts. List the single item as usual and send its providers
                # as a URL parameter so they don't have to be retrieved again.
                dirItem = next(_makeEpisodeItems(api, (episodeEntry,), showTitle, showGenres, showThumb, showPlot, showDate))
                newUrl = dirItem[0] + '&' + urlencode({'providers': str(episodeProviders)})
                xbmcplugin.addDirectoryItem(int(sys.argv[1]), newUrl, dirItem[1], False)
        else:
            logStreamError(params['api'], api, episodeEntry['id'])

    xbmcplugin.endOfDirectory(int(sys.argv[1]), cacheToDisc = False)

    # Custom layout.
    useEpisodeLayout, layoutType = ADDON_SETTINGS['layoutEpisodes']
    if useEpisodeLayout:
        xbmc.executebuiltin('Container.SetViewMode(' + layoutType + ')')


def viewResolve(params):
    '''
    Resolves and plays the chosen episode, based on the API and ID supplied in 'params'.
    '''
    cache.saveCacheIfDirty() # Save the cache, only if necessary, before watching a video.

    stream = None

    if 'stream' in params:
        # BACKWARDS COMPATIBILITY: Toonmania2 0.4.4.
        # If the stream is already included in the parameters, no need to retrieve it in here again.
        stream = params['stream']
    elif 'providerURL' in params:
        stream = resolveProviderURL(params['providerURL'])
    else:
        providers = None
        if 'providers' in params:
            # Dictionary of providers and their **unresolved** URLs, used with autoplay off.
            from ast import literal_eval
            providers = literal_eval(params['providers'])
        else:
            providers = getEpisodeProviders(params['api'], params['episodeID'])

        if providers:
            if isSettingTrue('autoplay'):
                from random import choice
                randomKey = choice(tuple(DICT_ITER_KEYS(providers)))
                stream = resolveProviderURL(providers[randomKey][0])
            else:
                index = xbmcgui.Dialog().select('Select Provider', tuple(name for name in DICT_ITER_KEYS(providers)))
                if index >= 0:
                    chosenKey = next(key for keyIndex, key in enumerate(DICT_ITER_KEYS(providers)) if keyIndex == index)
                    stream = resolveProviderURL(providers[chosenKey][0])
                else:
                    # User cancelled the 'Select Provider' dialog.
                    xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, xbmcgui.ListItem('None'))
                    return

    if stream:
        item = xbmcgui.ListItem(params['name'])
        setupListItem(
            item,
            params['showTitle'],
            params['name'],
            True,
            int(params['season']),
            int(params['episode']),
            params.get('genres', '').split(','),
            params.get('thumb', ''),
            params['plot'],
            params.get('date', '')
        )
        item.setPath(stream)
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), True, item)
    else:
        logStreamError(params['api'], params['showTitle'], params['episodeID'])
        xbmcplugin.setResolvedUrl(int(sys.argv[1]), False, xbmcgui.ListItem('None'))


def getPlaylist():
    playlist = xbmc.PlayList(xbmc.PLAYLIST_VIDEO)
    playlist.clear()
    return playlist


def reloadSettings():
    '''
    Loads some global settings. Other settings are used sparingly, only when needed.
    '''
    global ADDON_SETTINGS
    # Layout settings, each category is a key to a (bool, layoutType) value, eg: 'layoutShows': (True, '55')
    for element in ('catalog', 'shows', 'episodes'):
        ADDON_SETTINGS['layout' + element.capitalize()] = (
            ADDON.getSetting('layout_use_' + element) == 'true',
            ADDON_VIEW_MODES.get(ADDON.getSetting('layout_type_' + element), '55')
        )


def isSettingTrue(settingName):
    return ADDON.getSetting(settingName) == 'true'


def getTitleInfo(title):
    '''
    Helper function to extract season and episode values based on the title string.
    It expects a pattern such as "[Show name] Season 2 Episode 5 [episode title]".
    '''
    season = episode = 0
    titleWords = title.lower().split()
    for index, word in enumerate(titleWords):
        if word == 'season':
            try:
                season = int(titleWords[index+1])
            except ValueError:
                pass
        elif word == 'episode':
            try:
                episode = int(titleWords[index+1])
                if not season:
                    season = 1 # Season may be omitted in the title.
                break # The word 'Episode' is always put after the season and show title in the link strings.
            except ValueError:
                season = episode = 0 # Malformed \ typo'ed strings caused this?
        #else:
            # Accumulate only the name words in here, if needed.
    return (season, episode)


def setupListItem(item, showTitle, title, isPlayable, season, episode, genres, thumb = '', plot = '', date = ''):
    '''
    Helper function to fill in an xbmcgui.ListItem item with metadata info, supplied in the parameters.
    'genres' might be empty or None.
    '''
    if isPlayable:
        # Allows the checkmark to be placed on watched episodes, as well as some context menu options.
        item.setProperty('IsPlayable', 'true')

    if thumb:
        item.setArt({'icon': thumb, 'thumb': thumb, 'poster': thumb})

    # All items are set with 'episode' mediatype even if they aren't, as it looks better w/ the skin layout.
    itemInfo = {
        'mediatype': 'episode' if isPlayable else 'tvshow',
        'tvshowtitle': showTitle,
        'title': title,
        'plot': plot,
        'genre': genres if genres else '',
        'premiered': date, # According to the docs, 'premiered' is what makes Kodi display a date.
        'aired': date,
        'year': date.split('-')[0] if date else ''
    }
    if episode:
        itemInfo.update({'season': season, 'episode': episode})
    item.setInfo('video', itemInfo)


def logStreamError(api, showID, episodeID):
    dialog = xbmcgui.Dialog()
    dialog.notification('Toonmania2', 'No streams found', xbmcgui.NOTIFICATION_INFO, 3000, True)
    xbmc.log('Toonmania2 | No streams for API:%s SHOW:%s EPISODE:%s' % (api, showID, episodeID), xbmc.LOGWARNING)


def buildURL(query):
    '''
    Helper function to build a Kodi xbmcgui.ListItem URL.
    :param query: Dictionary of url parameters to put in the URL.
    :returns: A formatted URL string.
    '''
    return (sys.argv[0] + '?' + urlencode({k: v.encode('utf-8') if isinstance(v, UNICODE)
                                           else UNICODE(v, errors='ignore').encode('utf-8')
                                           for k, v in DICT_ITER_ITEMS(query)}))


# Main dictionary of add-on directories (aka views or screens).
VIEW_FUNCS = {
    'MENU': viewMenu,
    'ANIMETOON_MENU': viewAnimetoonMenu,
    'ANIMEPLUS_MENU': viewAnimeplusMenu,
    'SETTINGS': viewSettings,

    'CATALOG_MENU': viewCatalogMenu,
    'CATALOG_SECTION': viewCatalogSection,
    'SEARCH_MENU': viewSearchMenu,
    'SEARCH_GENRE': viewSearchGenre,
    'TRAKT_MENU': viewTraktMenu,
    'TRAKT_LIST': viewTraktList,
    'TRAKT_ITEM': viewTraktItem,

    'CLEAR_CACHE': viewClearCache,
    'CLEAR_TRAKT': viewClearTrakt,
    'LIST_EPISODES': viewListEpisodes,
    'RESOLVE': viewResolve
}


# Global scope, initialises ADDON_SETTINGS.
reloadSettings()


def main():
    '''
    Main add-on routing function, it selects and shows an add-on directory.
    Uses the global VIEW_FUNCS dictionary.
    '''
    params = dict(pair for pair in parse_qsl(sys.argv[2][1:], keep_blank_values=True))
    VIEW_FUNCS[params.get('view', 'MENU')](params)