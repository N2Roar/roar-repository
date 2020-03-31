# -*- coding: utf-8 -*-
import re
import sys
import json
import requests

try:
    # Python 2.7
    from urlparse import parse_qsl
    from urllib import quote_plus, quote, urlencode
except ImportError:
    # Python 3+
    from urllib.parse import parse_qsl, quote, quote_plus, urlencode

import xbmc
import xbmcgui
import xbmcaddon
import xbmcplugin


PLUGIN_ID = int(sys.argv[1])
PLUGIN_URL = sys.argv[0]

PROPERTY_SESSION_TOKEN = 'wsbeta.token'

PROPERTY_MEDIA_PATH = 'wsbeta.epsPath'
PROPERTY_MEDIA_DATA = 'wsbeta.epsData'

ADDON = xbmcaddon.Addon()
ADDON_ICON = ADDON.getAddonInfo('icon')


class WSBetaSession(requests.Session):
    API_URL = 'https://www.wonderfulsubs.com/api/v2/'

    _session = None

    @classmethod
    def instance(cls):
        if not cls._session:
            cls._session = WSBetaSession()
        return cls._session


    def __init__(self, *args, **kwargs):
        super(WSBetaSession, self).__init__(*args, **kwargs)
        self.headers.update(
            {
                'User-Agent': 'Mozilla/5.0 (compatible; WSBeta/0.1.0; +https://github.com/doko-desuka/plugin.video.wsbeta)',
                'Accept': 'application/json, text/*',
                'Accept-Language': 'en-US,en;q=0.5',
                'Content-Type': 'application/json; charset=utf-8',
                'Origin': self.API_URL[:-1],
                'Referer': self.API_URL
            }
        )


    def setToken(self, token):
        self.headers['Authorization'] = 'Bearer ' + token


    def clearToken(self):
        self.headers.pop('Authorization', None)


    def request(self, method, url, *args, **kwargs):
        kwargs['timeout'] = 15 # Global timeout in seconds.
        return super(WSBetaSession, self).request(method, url, *args, **kwargs)


    def api(self, path, *args, **kwargs):
        func = self.post if ('json' in kwargs or 'data' in kwargs) else self.get
        url = path if path.startswith('http') else self.API_URL + path

        r = func(url, *args, **kwargs)

        # Silently handle expired / invalid token responses.
        if r.status_code == 403:
            token = refreshUserToken(notify=False, askSettings=False)
            if token:
                self.setToken(token)
                setRawWindowProperty(PROPERTY_SESSION_TOKEN, token)
            else:
                clearWindowProperty(PROPERTY_SESSION_TOKEN)
            # Call the same method again (no guarantee that it will actually work).
            r = func(url, *args, **kwargs)

        return r


    def solveMediaRedirect(self, url, headers):
        # Use HEAD requests to fulfill possible 302 redirections.
        # Returns the final HEAD response.
        while True:
            try:
                mediaHead = self.head(url, headers=headers)
                if 'Location' in mediaHead.headers:
                    url = mediaHead.headers['Location'] # Change the URL to the redirected location.
                else:
                    mediaHead.raise_for_status()
                    return mediaHead # Return the response.
            except:
                return None # Return nothing on failure.


    def parseHLSQualities(self, url, **kwargs):
        r = self.get(url, **kwargs)
        if r.ok:
            # Early exit if it already points to the segments (as it's not a playlist file).
            if b'#EXTINF:' in r.content:
                return [('', r.url)]
            url = r.url
            urlPath = url.rsplit('/', 1)[0] + '/'
            domain = '/'.join(url.split('/', 3)[:3]) # It's actually scheme + authority = "https://site.com"
            return [
                (
                    quality,
                    (
                        # Output a full path to the stream.
                        # Need to check if it's a full path, relative path or file/appended path.
                        stream if stream.startswith('http') else
                        (domain+stream if stream.startswith('/') else urlPath+stream)
                    )
                )
                for quality, stream in re.findall('''RESOLUTION=([^,\n]+).*?(?:\n|URI=")([^'"\n]+)''', r.text)
            ]
        else:
            return None


    @staticmethod
    def desktopMediaHeaders():
        return {
            'User-Agent': 'Mozilla/5.0 (Windows NT 6.3; Win64; x64; rv:72.0) Gecko/20100101 Firefox/72.0',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.5'
        }


    @staticmethod
    def kodiMediaHeaders():
        # Headers for Kodi to use when playing streams.
        desktopHeaders = WSBetaSession.desktopMediaHeaders()
        return '|' + '&'.join(key + '=' + quote_plus(desktopHeaders[key]) for key in desktopHeaders)


SESSION = WSBetaSession.instance()


def requireAccount(func):
    # Decorator for most functions, tries to get a user token if credentials are present in add-on settings.
    # Otherwise, tells user to check settings to learn about having an account.
    # Even though it's not necessary to use a token for the all / popular / latest / random API routes,
    # there's no point in letting the user proceed without a token because they won't be able to watch
    # any episodes / movies later anyway, not without one.
    def wrapper(*args, **kwargs):
        token = getRawWindowProperty(PROPERTY_SESSION_TOKEN)
        if not token:
            token = refreshUserToken(notify=True, askSettings=True)
            if token:
                setRawWindowProperty(PROPERTY_SESSION_TOKEN, token)

        if token:
            SESSION.setToken(token) # Always set the token, as on Kodi 17.6 the Session is always recreated per screen.
            func(*args, **kwargs) # Proceed with the original function.
    return wrapper


def actionMainMenu(params):
    def _makeLastWatchedTuple():
        # Returns a 1-tuple to be prepended to the main menu items.
        if (ADDON.getSetting('lastwatched.use') == 'true'):
            data = ADDON.getSetting('lastwatched.data')
            try:
                label, path, mediaIndex = data.split('\n')
                label = label.replace('[B]', '').replace('[/B]', '')
                return (
                    simpleFolderItem(
                        '[COLOR lavender][B]Last Watched:[/B][/COLOR] [I]'+label+'[/I]',
                        {'action': 'actionEpisodesDir', 'path': path, 'mediaIndex': mediaIndex}
                    ),
                )
            except:
                return (
                    ('', xbmcgui.ListItem('[COLOR lavender][B]Last Watched:[/B][/COLOR] (Empty)'), False),
                )
        else:
            return ( )
       
    xbmcplugin.addDirectoryItems(
        PLUGIN_ID,
        _makeLastWatchedTuple() + (
            simpleFolderItem(
                'Latest', {'action': 'actionListDir', 'path': 'media/latest?index=0&count=25'}, 'orange'
            ),
            simpleFolderItem(
                'Popular', {'action': 'actionListDir', 'path': 'media/popular?index=0&count=25'}, 'orange'
            ),
            simpleFolderItem(
                'Random', {'action': 'actionListDir', 'path': 'media/random?index=0&count=25'}, 'orange'
            ),
            simpleFolderItem('A - Z', {'action': 'actionAZMenu'}, 'orange'),
            simpleFolderItem('Genres', {'action': 'actionGenreSearchMenu'}, 'khaki'),
            simpleFolderItem('Search', {'action': 'actionNameSearchMenu'}, 'khaki'),
            simpleFolderItem('Settings', {'action': 'actionShowSettings'}, 'khaki')
        )
    )
    xbmcplugin.endOfDirectory(PLUGIN_ID)


@requireAccount
def actionListDir(params):
    r = SESSION.api(params['path'])
    if r.ok:

        def _listItemsGen(jsonData):
            showThumbs = (ADDON.getSetting('showThumbs') == 'true')

            for entry in jsonData['series']:
                title = entry['title']
                if entry['is_subbed']:
                    languages = ' (Sub, Dub)' if entry['is_dubbed'] else ' (Sub)'
                elif entry['is_dubbed']:
                    languages = ' (Dub)'
                else:
                    languages = ''
                item = xbmcgui.ListItem('[B]' + title + '[/B]' + languages)
                plot = entry['description'] if entry.get('description', None) else ''
                item.setInfo('video', {'mediatype': 'tvshow', 'title': title, 'plot': plot})
                if showThumbs and 'kitsu_id' in entry:
                    #thumb = defaultPosterTall(entry['poster_tall']) # See the comments in getThumbnailURL().
                    thumb = getThumbnailURL(entry['kitsu_id'])
                    item.setArt({'thumb': thumb, 'poster': thumb})
                else:
                    thumb = ''
                yield (
                    buildURL(
                        {
                            'action': 'actionMediaDir',
                            'path': 'media/series?series=' + entry['url'].split('watch/', 1)[1],
                            'thumb': thumb
                        }
                    ),
                    item,
                    True
                )

            if 'next_page' in jsonData:
                if 'index=' in params['path']:
                    index = int(params['path'].split('index=', 1)[1].split('&', 1)[0])
                else:
                    index = 0
                # The count value used throughout WSBeta is 25.
                totalPages = (jsonData['total_results'] // 25) + (jsonData['total_results'] % 25 > 0)
                yield (
                    buildURL({'action': 'actionListDir', 'path': jsonData['next_page']}),
                    xbmcgui.ListItem('[B]Next Page (%i/%i)[/B]' % ((index // 25) + 1, totalPages)),
                    True
                )

        #xbmcplugin.setContent(PLUGIN_ID, 'tvshows') # Optional. The default skin layout looks fine.
        xbmcplugin.addDirectoryItems(PLUGIN_ID, tuple(_listItemsGen(r.json()['json'])))
        xbmcplugin.endOfDirectory(PLUGIN_ID)
    else:
        xbmcgui.Dialog().notification(
            'WSBeta (API)', 'Unable to get directory, check your web connection', ADDON_ICON, 3000, False
        )
        xbmcDebug('Request failed:', params)
        return


@requireAccount
def actionAZMenu(params):
    xbmcplugin.addDirectoryItems(
        PLUGIN_ID,
        (
            [
                simpleFolderItem(
                    'All', {'action': 'actionListDir', 'path': 'media/all?index=0&count=25'}, 'lavender'
                ),
                simpleFolderItem(
                    '#', {'action': 'actionListDir', 'path': 'media/all?index=0&count=25&letter=none'}, 'lavender'
                )
            ]
            + [
                simpleFolderItem(
                    c, {'action': 'actionListDir', 'path': 'media/all?index=0&count=25&letter=' + c}, 'lavender'
                )
                for c in 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
            ]
        )
    )
    xbmcplugin.endOfDirectory(PLUGIN_ID)


@requireAccount
def actionMediaDir(params):
    # A "media" directory is a collection of items, usually a season with episodes. In some cases it's also
    # a list of related OVA episodes, or even a single-item list (with a movie).
    jsonData = ensureJSONData(params['path'])
    if jsonData:

        def _mediaItemsGen(data):
            showThumbs = (ADDON.getSetting('showThumbs') == 'true')
            defaultThumb = params['thumb']
            artDict = {'thumb': defaultThumb, 'poster': defaultThumb}

            defaultPlot = data['description'] if data.get('description', None) else ''

            for index, entry in enumerate(data['seasons']['ws']['media']):
                item = xbmcgui.ListItem(formattedMediaLabel(entry))
                
                if showThumbs and defaultThumb:
                    item.setArt(artDict)
                item.setInfo(
                    'video',
                    {
                        'title': entry['title'] if entry.get('title', None) else 'Extras',
                        'plot': entry['description'] if entry.get('description', None) else defaultPlot
                    }
                )
                yield (
                    buildURL(
                        {'action': 'actionEpisodesDir', 'path': params['path'], 'mediaIndex': index, 'thumb': defaultThumb}
                    ),
                    item,
                    True
                )

        xbmcplugin.addDirectoryItems(PLUGIN_ID, tuple(_mediaItemsGen(jsonData)))
        xbmcplugin.endOfDirectory(PLUGIN_ID)


@requireAccount
def actionEpisodesDir(params):
    # List all "episodes" from a media collection.
    path = params['path']
    jsonData = ensureJSONData(path)
    if jsonData and 'mediaIndex' in params:
        allMedia = jsonData['seasons']['ws']['media']
        mediaIndex = int(params['mediaIndex'])
        mediaThumb = params.get('thumb', '')

        # Safety check in case we're coming in from a Kodi Favourites item that points to media
        # that doesn't exist anymore after some change from their server.
        if mediaIndex >= len(allMedia):
            return
        media = allMedia[mediaIndex]

        totalEpisodes = len(media['episodes'])
        if totalEpisodes <= 100:
            params['page'] = '0'

        # This function outputs different items depending on whether the user already chose a page.
        # We separate 100 episodes per page so that slow devices don't freeze when trying to list them.

        if 'page' in params:
            # Output an episode list, starting from a certain page.

            def _episodeItemsGen(media, page, defaultThumb):
                mediaTitle = media['title'] if media.get('title', None) else ''
                mediaPlot = media['description'] if media.get('description', None) else ''
                mediaType = 'episode' if (media.get('type', None) and (media['type'] != 'episodes')) else 'video'

                showEpisodeThumbs = (ADDON.getSetting('showEpisodeThumbs') == 'true')
                if showEpisodeThumbs:
                    thumbHeaders = getThumbnailHeaders()
                    artDict = {'thumb': None, 'poster': None}

                # It's slightly faster to change a preexisting dictionary than creating a new one on each item.
                actionDict = {
                    'action': 'actionPlay',
                    'path': path,
                    'mediaIndex': mediaIndex,
                    'episodeIndex': None
                }

                zFillAmount = 3 if totalEpisodes >= 100 else 2

                for episodeIndex, entry in enumerate(media['episodes'][page*100:(page+1)*100], page*100):
                    title = entry['title'] if entry.get('title', '') else '' # Account for empty titles, if there's any?
                    
                    item = xbmcgui.ListItem(formattedItemLabel(entry, zFillAmount))
                    infoDict = {
                        'mediatype': mediaType,
                        'tvshowtitle': mediaTitle,
                        'title': title,
                        'plot': entry['description'] if entry.get('description', None) else ''
                    }
                    if entry.get('episode_number', None) != None: # Avoid considering 0 as false.
                        infoDict['episode'] = entry['episode_number'] # This value is already an integer.
                    item.setInfo('video', infoDict)
                    item.setProperty('IsPlayable', 'true') # Allows the checkmark to be placed on watched episodes.

                    if showEpisodeThumbs:
                        thumb = entry['thumbnail'][0]['source'] + thumbHeaders if entry.get('thumbnail', None) else defaultThumb
                        artDict['thumb'] = thumb
                        artDict['poster'] = thumb
                        item.setArt(artDict)

                    actionDict['episodeIndex'] = episodeIndex
                    yield (buildURL(actionDict), item, False)

            items = list(_episodeItemsGen(media, int(params['page']), mediaThumb))

        else:
            # Output a list of pages.
            showThumbs = (ADDON.getSetting('showThumbs') == 'true')
            items = [
                (
                    buildURL(
                        {
                            'action': 'actionEpisodesDir',
                            'path': path,
                            'mediaIndex': mediaIndex,
                            'page': page,
                            'thumb': mediaThumb
                        }
                    ),
                    xbmcgui.ListItem(
                        'Episodes %i-%i' % (page*100+1, min((page+1)*100, totalEpisodes)),
                        thumbnailImage = mediaThumb if showThumbs else ''
                    ),
                    True
                )
                for page in range(0, (totalEpisodes // 100) + (totalEpisodes % 100 > 0))
            ]

        if ADDON.getSetting('reverseEpisodes') == 'true':
            items.reverse() # Maybe this could be done in a smarter way, without having to recreate the entire list.

        xbmcplugin.addDirectoryItems(PLUGIN_ID, items)
        xbmcplugin.endOfDirectory(PLUGIN_ID)


@requireAccount
def actionNameSearchMenu(params):
    history = ADDON.getSetting('searchHistory').split('\n') # Non-UI setting, it's just a big string.

    newSearchItem = (buildURL({'action': 'actionNameSearchExecute'}), xbmcgui.ListItem('[B]New search...[/B]'), True)

    # A .split() on a blank string creates a list with a blank string inside, so test if the first item is valid.
    if history[0]:
        historyItems = tuple(
            (
                buildURL({'query': query, 'action': 'actionNameSearchExecute'}),
                xbmcgui.ListItem('[B]' + query + '[/B]'),
                True
            )
            for query in history
        )
        clearHistoryItem = (
            buildURL({'action': 'actionSearchHistoryClear'}), xbmcgui.ListItem('[B]Clear History...[/B]'), False
        )
        xbmcplugin.addDirectoryItems(PLUGIN_ID, (newSearchItem,) + historyItems + (clearHistoryItem,))
    else:
        xbmcplugin.addDirectoryItem(PLUGIN_ID, *newSearchItem)
    xbmcplugin.endOfDirectory(PLUGIN_ID)


def actionNameSearchExecute(params):
    def _modalKeyboard(heading):
        kb = xbmc.Keyboard('', heading)
        kb.doModal()
        return kb.getText() if kb.isConfirmed() else ''

    # Support external query calls, like from OpenMeta.
    if 'query' not in params:
        query = _modalKeyboard('Search')
    else:
        query = params['query']

    if query:
        # Handle the add-on search history.
        previousHistory = ADDON.getSetting('searchHistory')
        if previousHistory:
            previousHistory = previousHistory.split('\n')
            if query not in previousHistory:
                # Limit search history to 32 items.
                if len(previousHistory) == 32:
                    previousHistory.pop()
                previousHistory.insert(0, query)
                ADDON.setSetting('searchHistory', '\n'.join(previousHistory))
            else:
                pass # No need to add it again to the history, if it's already there.
        else:
            ADDON.setSetting('searchHistory', query)

        # Do an actual search with the API by calling the directory function directly.
        params['path'] = 'media/search?index=0&count=25&q=' + quote(query)
        actionListDir(params)


def actionSearchHistoryClear(params):
    dialog = xbmcgui.Dialog()
    if dialog.yesno('Clear Search History', 'Are you sure?'):
        ADDON.setSetting('searchHistory', '')
        dialog.notification('WSBeta', 'Search history cleared', ADDON_ICON, 3000, False)
        # Show the search menu afterwards.
        xbmc.executebuiltin('Container.Update(' + PLUGIN_URL + '?action=actionNameSearchMenu,replace)')


@requireAccount
def actionGenreSearchMenu(params):
    xbmcplugin.addDirectoryItems(
        PLUGIN_ID,
        [
            simpleFolderItem(
                genre, {'action': 'actionListDir', 'path': 'media/search?index=0&count=25&q=' + genre}, 'lavender'
            )
            for genre in (
                # Names taken from their genre search page.
                'Action', 'Adventure', 'Cars', 'Comedy', 'Dementia', 'Demons', 'Drama', 'Ecchi', 'Fantasy',
                'Game', 'Harem', 'Historical', 'Horror', 'Josei', 'Kids', 'Magic', 'Martial Arts', 'Mecha','Military',
                'Music', 'Mystery', 'Parody', 'Police', 'Psychological', 'Romance', 'Samurai', 'School', 'Sci-Fi',
                'Seinen', 'Shoujo', 'Shoujo Ai', 'Shounen', 'Shounen Ai', 'Slice of Life', 'Space', 'Sports',
                'Super Power', 'Supernatural', 'Thriller', 'Vampire', 'Yaoi', 'Yuri'
            )
        ]
    )
    xbmcplugin.endOfDirectory(PLUGIN_ID)


def actionShowSettings(params):
    # Modal dialog, so the program won't continue from this point until user closes\confirms it.
    ADDON.openSettings()


def actionAccountAbout(params):
    xbmcgui.Dialog().ok(
        'WSBeta',
        'You need a free WonderfulSubs account to watch videos.\nCreate one on ' \
        '[B]https://beta.wonderfulsubs.com/signup[/B]\nand then put your username and password in the add-on settings.'
    )


def actionAccountLogout(params):
    if xbmcgui.Dialog().yesno(
        'WSBeta',
        'This will clear the username and password in the add-on settings, making the add-on forget them.\nProceed?'
    ):
        # Clear the add-on credential settings.
        ADDON.setSetting('username', '')
        ADDON.setSetting('password', '')

        # Clear any memory references to the token.
        SESSION.headers.pop('Authorization', None)
        clearWindowProperty(PROPERTY_SESSION_TOKEN)

        xbmcgui.Dialog().notification(
            'WSBeta', 'Username and password cleared', ADDON_ICON, 3000, False
        )
    
    
def actionAdaptiveSettings(params):
    addon = getInputStreamAdaptive()
    if addon:
        addon.openSettings()


def actionAdaptiveEnable(params):
    try:
        # Enable InputStream Adaptive.
        # Based on inputstreamhelper (https://github.com/emilsvennesson/script.module.inputstreamhelper/).
        rpcQuery = (
            '{"jsonrpc": "2.0", "id": "1", "method": "Addons.SetAddonEnabled", "params": {"addonid":' \
            '"inputstream.adaptive", "enabled": true}}'
        )
        xbmc.executeJSONRPC(rpcQuery)
        
        # Wait a bit, for slow devices.
        xbmc.sleep(1000)        
        xbmcgui.Dialog().notification(
            'WSBeta', 'InputStream Adaptive enabled', ADDON_ICON, 2000, False
        )
        xbmcaddon.Addon('inputstream.adaptive') # This call will raise an exception if the add-on is not available.
        ADDON.openSettings()
    except:
        xbmcgui.Dialog().notification(
            'WSBeta', "Failed. Try to enable InputStream Adaptive manually", xbmcgui.NOTIFICATION_WARNING, 3000, False
        )


@requireAccount
def actionPlay(params):
    path = params['path']    
    jsonData = ensureJSONData(path)
    if not jsonData or ('mediaIndex' not in params or 'episodeIndex' not in params):
        return
        
    media = jsonData['seasons']['ws']['media'][int(params['mediaIndex'])]
    episode = media['episodes'][int(params['episodeIndex'])]
    
    # Store some data to be used for making the "Last Watched" main menu item.
    ADDON.setSetting(
        'lastwatched.data',
        formattedMediaLabel(media, showLength=False) + '\n' + path + '\n' + params['mediaIndex']
    )

    # Choose a provider for the episode / video.

    if 'sources' in episode and episode['sources']:
        itemList = [
            xbmcgui.ListItem(
                '%s (%s)' % (source['source'].upper(), source['language']),
                (source['retrieve_url'][0] if isinstance(source['retrieve_url'], list) else source['retrieve_url'])
            )
            for source in episode['sources']
        ]
        if len(itemList) > 1:
            selectedIndex = xbmcgui.Dialog().select('Select Provider', itemList)
            providerName = itemList[selectedIndex].getLabel()
            if selectedIndex != -1:
                code = itemList[selectedIndex].getLabel2()
            else:
                return
        else:
            code = itemList[0] # Single provider / source.
    elif 'retrieve_url' in episode:
        providerName = '(Unknown)'
        code = episode['retrieve_url'][0]
    else:
        xbmcgui.Dialog().notification('WSBeta (API)', 'No providers available', ADDON_ICON, 3000, False)
        return

    # Request and pick a stream from that provider with the API.

    r = SESSION.api('media/stream?code=' + code)
    if r.ok:
        data = r.json()
        if data['status'] != 200:
            xbmcgui.Dialog().notification(
                'WSBeta (API)', 'No streams available', ADDON_ICON, 3000, False)
            return

        itemList = [xbmcgui.ListItem(source['label'], source['src']) for source in data['urls'][::-1]]
        if len(itemList) > 1:
            selectedIndex = xbmcgui.Dialog().select(
                'Select Stream',
                itemList,
                useDetails=True
            )
            if selectedIndex > -1:
                stream = itemList[selectedIndex].getLabel2()
            else:
                return
        else:
            stream = data['urls'][0]['src']
    else:
        xbmcgui.Dialog().notification('WSBeta (API)', 'Unable to request streams', ADDON_ICON, 3000, False)
        return

    headers = SESSION.desktopMediaHeaders()

    # Try to un-redirect the chosen media URL.
    mediaHead = SESSION.solveMediaRedirect(stream, headers)
    if not mediaHead:
        xbmcgui.Dialog().notification('WSBeta', 'Source failed to play: ' + providerName)
        return
    contentType = mediaHead.headers['Content-Type'].lower()

    # Final resolve step: picking an HLS quality or using InputStream Adaptive.

    videoItem = xbmcgui.ListItem()
    videoItem.setMimeType(contentType)
    videoItem.setContentLookup(False)    

    if ADDON.getSetting('adaptive.use') == 'true':
        # (Try to) Use InputStream Adaptive for playback.        
        if (
            getInputStreamAdaptive()
            and ('dash+xml' in contentType or 'x-mpegurl' in contentType or 'vnd.apple.mpegurl' in contentType)
        ):
            videoItem.setProperty('inputstreamaddon', 'inputstream.adaptive')
            videoItem.setProperty('inputstream.adaptive.manifest_type', 'mpd' if 'dash+xml' in contentType else 'hls')
        stream = mediaHead.url
    else:
        # Use standard Kodi playback (but try to give a choice of which HLS quality to choose, if possible).
        if contentType == 'application/x-mpegurl' or contentType == 'application/vnd.apple.mpegurl':
            qualityList = SESSION.parseHLSQualities(mediaHead.url, headers=headers)
            if qualityList:
                if len(qualityList) > 1:
                    # Sort based on personal taste, with 480p as the first item.
                    qualityList = sorted(qualityList, key=lambda x: -1 if 'x480' in x[0] else 0)
                    itemList = [xbmcgui.ListItem(*qualityData) for qualityData in qualityList]
                    selectedIndex = xbmcgui.Dialog().select('Select Stream Quality', itemList, useDetails=True)
                    if selectedIndex != -1:
                        stream = itemList[selectedIndex].getLabel2()
                    else:
                        return
                else:
                    stream = qualityList[0][1] # Only 1 quality in the playlist.
            else:
                return
        else:
            # TODO: add support for other formats / embedded video players.
            stream = mediaHead.url

    title = episode['title'] if episode.get('title', None) else ''
    videoItem.setLabel(
        formattedItemLabel(episode, zFillAmount=(3 if len(media['episodes']) >= 100 else 2))
    )
    videoItem.setInfo(
        'video',
        {
            'mediatype': 'episode' if media.get('type', None) and media['type'] == 'episodes' else 'video',
            'tvshowtitle': media['title'] if media.get('title', None) else '',
            'title': title,
            'plot': episode['description'] if episode.get('description', None) else ''
        }
    )
    videoItem.setPath(stream + SESSION.kodiMediaHeaders())

    #xbmc.Player().play(listitem=videoItem) # Alternative play method, lets you extend the Player class with your own.
    xbmcplugin.setResolvedUrl(PLUGIN_ID, True, videoItem)


def getInputStreamAdaptive():
    try:
        addon = xbmcaddon.Addon('inputstream.adaptive') # Will raise an exception if not installed / disabled.
        return addon
    except:
        return None


def buildURL(query):
    return (PLUGIN_URL + '?' + urlencode(query))


def xbmcDebug(*args):
    xbmc.log('WSBETA > ' + ' '.join((val if isinstance(val, str) else repr(val)) for val in args), xbmc.LOGWARNING)


def simpleFolderItem(title, data, color=None):
    label = ('[B][COLOR ' + color + ']' + title + '[/COLOR][/B]') if color else title
    item = xbmcgui.ListItem(label)
    item.setArt({'poster': ADDON_ICON})
    item.setInfo('video', {'title': title, 'plot': title})
    return (buildURL(data), item, True)


def formattedMediaLabel(entry, showLength=True):
    # Format a nice label for media (season) folders.    
    title = entry['title'] if entry.get('title', None) else 'Extras'
    label = '[B]'+title+'[/B]'
    
    if entry.get('type', None) == 'episodes':
        if 'min_season' in entry and 'max_season' in entry:
            label += ' (Seasons %i-%i)' % (entry['min_season'], entry['max_season'])
        else:
            label += ' (Episodes)'                        
            
    if showLength and entry.get('episodes', None):
        label += ' (%i item%s)' % (len(entry['episodes']), '' if len(entry['episodes']) == 1 else 's')
    
    return label
        

def formattedItemLabel(entry, zFillAmount):
    # Format a nice label for episode / ova / movie items.
    if entry.get('episode_number', None) != None: # Avoid considering 0 as false.
        return str(entry['episode_number']).zfill(zFillAmount) + ' - ' + entry.get('title', '')
    elif entry.get('ova_number', None) != None:
        return str(entry['ova_number']).zfill(zFillAmount) + ' - ' + entry.get('title', '')
    else:
        return entry.get('title', '')


def defaultPosterTall(posterTallData):
    if not posterTallData:
        return ''
    # Try to get the second image of poster_tall lists, it's one step above "tiny".
    return (posterTallData[1] if len(posterTallData) > 0 else posterTallData[0])['source']


def ensureJSONData(path):
    # See if the media data is already in memory, so no need to request it again.
    if path == getRawWindowProperty(PROPERTY_MEDIA_PATH):
        jsonData = getWindowProperty(PROPERTY_MEDIA_DATA)
    else:
        r = SESSION.api(path)
        try:
            r.raise_for_status()
            temp = r.json()
            if temp['status'] != 200:
                raise
            jsonData = temp['json']
            setRawWindowProperty(PROPERTY_MEDIA_PATH, path)
            setWindowProperty(PROPERTY_MEDIA_DATA, jsonData)
        except:
            clearProperty(PROPERTY_MEDIA_PATH)
            clearProperty(PROPERTY_MEDIA_DATA)
            xbmcgui.Dialog().notification(
                'WSBeta (API)', 'Unabled to get series media', ADDON_ICON, 3000, True
            )
            xbmcDebug('Media fail:', path)
            return None
    return jsonData


def refreshUserToken(notify, askSettings):
    username = ADDON.getSetting('username')
    password = ADDON.getSetting('password')
    if username and password:
        r = SESSION.api('users/login', json={'username': username, 'password': password})
        if r.ok:
            try:
                data = r.json()

                # Unused at the moment, user ID that lets you add items to account favorites etc.
                #id = data['data']['_id']

                return data['token']
            except:
                if notify:
                    xbmcgui.Dialog().notification(
                        'WSBeta (API)', 'Unable to find user token', ADDON_ICON, 3000, True
                    )
                return None
        else:
            if notify:
                xbmcgui.Dialog().notification(
                    'WSBeta (API)', 'Unable to request user token', ADDON_ICON, 3000, True
                )
            return None
    else:
        if askSettings and xbmcgui.Dialog().yesno(
            'WSBeta',
            'Please add your account login credentials in the add-on settings.',
            yeslabel = 'Settings...',
            nolabel = 'Cancel'
        ):
            # Open the add-on settings in a modal dialog (script pauses until user closes the window).
            ADDON.openSettings()
            # After this point the user has closed the dialog.
            # Try to refresh the token again with one recursion and no further popups.
            return refreshUserToken(notify=True, askSettings=False)
    return None


def getWindowProperty(prop):
    window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
    data = window.getProperty(prop)
    return json.loads(data) if data else None


def setWindowProperty(prop, data):
    window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
    temp = json.dumps(data)
    window.setProperty(prop, temp)


def clearWindowProperty(prop):
    window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
    window.clearProperty(prop)


def testWindowProperty(prop):
    window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
    return window.getProperty(prop) != ''


def getRawWindowProperty(prop):
    window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
    return window.getProperty(prop)


def setRawWindowProperty(prop, data):
    window = xbmcgui.Window(xbmcgui.getCurrentWindowId())
    window.setProperty(prop, data)


def getThumbnailURL(kitsuID):
    # Complete thumbnail URL for ListItem's.
    # Includes headers to spoof a desktop browser, to not reveal that it's coming from Kodi (since it's a constant
    # value, it can be precomputed as the quote_plus-encoded User-Agent + Accept headers from Firefox).

    # We use Kitsu images because the default WonderfulSubs thumbnails fail to be loaded by Kodi because Kodi
    # expects the Content-Length header in the HEAD request it sends before GETting the thumbnail, and some
    # of the thumbnail providers that the API uses don't include that header, making Kodi refuse to load the image.
    return 'https://media.kitsu.io/anime/poster_images/' + str(kitsuID) + '/small.jpg|User-Agent=Mozilla%2F5.0+%28' \
    'Windows+NT+6.3%3B+Win64%3B+x64%3B+rv%3A72.0%29+Gecko%2F20100101+Firefox%2F72.0&Accept=image%2Fwebp%2C%2A%2F%2A'


def getThumbnailHeaders():
    # Thumbnail HTTP headers to spoof a desktop browser, to not reveal that it's coming from Kodi.
    return '|User-Agent=Mozilla%2F5.0+%28Windows+NT+6.3%3B+Win64%3B+x64%3B+rv%3A72.0%29+Gecko%2F20100101+Firefox%2F72.0' \
    '&Accept=image%2Fwebp%2C%2A%2F%2A'


def main():
    # Main add-on routing function, calls a certain action (function).
    # The 'action' parameter is the direct name of the function.
    params = dict(parse_qsl(sys.argv[2][1:], keep_blank_values=True))
    globals()[params.get('action', 'actionMainMenu')](params) # Defaults to actionMainMenu().
