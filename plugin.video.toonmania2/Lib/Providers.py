# -*- coding: utf-8 -*-
import re

from Lib.RequestHelper import requestHelper


# Internal dictionary of "mostly" supported providers, each key is a provider name, each value is a
# set of variant names for each provider. All these variants come up in the URLs...
_SUPPORTED_PROVIDERS = {
    'VIDEOZOO.ME': set(('videozoo.me', 'videozoome', 'videozoo')),
    'PLAY44.NET': set(('play44.net', 'play44net', 'play44')),
    'EASYVIDEO.ME': set(('easyvideo.me', 'easyvideome', 'easyvideo')),
    'PLAYBB.ME': set(('playbb.me', 'playbbme', 'playbb')),
    'PLAYPANDA.NET': set(('playpanda.net', 'playpandanet', 'playpanda')),
    'VIDEOWING.ME': set(('videowing.me', 'videowingme', 'videowing'))
}
# Resolving not available for these right now, they need to be researched on how to solve:
# 'cheesestream.com', '4vid.me', 'video66.org', 'videobug.net', 'videofun.me', 'vidzur.com'.


def getEpisodeProviders(api, episodeID):
    '''
    :returns: A dict where each key is a provider name and each value is a list of
    lists of stream URLs from that same provider.
    
    Usually each provider list has a single stream list, but in some rare cases there's more than
    one set of streams for the same provider.
    '''
    requestHelper.setAPISource(api)
    requestHelper.delayBegin()
    jsonData = requestHelper.routeGET('/GetVideos/' + episodeID)
    requestHelper.delayEnd(1000)

    if not jsonData:
        return None

    if isinstance(jsonData[0], dict):
        # Special-case for animeplus, URLs might come inside one dictionary each provider.
        providerURLs = (providerURL['url'] for providerURL in jsonData)
    elif isinstance(jsonData[0], list):
        # Or the JSON data is a list of lists (sometimes w/ mixed providers in the same list...).
        providerURLs = (url for urlList in jsonData for url in urlList)
    else:
        providerURLs = jsonData # A list of single providers?

    # Assume the video parts of the same provider will be in order (eg. easyvideo part 1, easyvideo part 2 , 3 etc.).

    providers = { } # Parent dict of providers, this is what's returned.
    lastURLs = [ ]
    lastProvider = ''

    for url in providerURLs:
        # Try to get the provider name from the URL to see if we support resolving it.
        if url.startswith('http://'):
            tempURL = url.replace('http://', '')
        elif url.startswith('https://'):
            tempURL = url.replace('https://', '')

        providerName = next(
            (
                key
                for word in tempURL.split('.')
                for key in _SUPPORTED_PROVIDERS.iterkeys() if word in _SUPPORTED_PROVIDERS[key]
            ),
            None
        )
        if not providerName:
            continue # It's not a supported provider (or we failed finding its name).

        # Accummulate consecutive URLs from the same provider in a list, until the provider name changes.
        if providerName != lastProvider:
            if lastURLs: # Store the list in the dict, if it has any items.
                if lastProvider in providers:
                    providers[lastProvider].append(lastURLs) # In case of non-consecutive lists of the same provider.
                else:
                    providers[lastProvider] = [ lastURLs ]
                lastURLs = [ ]
            lastProvider = providerName

        lastURLs.append(url)

    # Flatten the 'providers' dict with a new key for each URL-list of the same provider.
    # providers[videozoo] = [[...], [...], [...]] becomes providers[videozoo][...], providers[videozoo2][...], etc.
    allProviders = {
        (providerName if index == 1 else providerName + ' (' + str(index) + ')'): urlList
        for providerName in providers.iterkeys()
        for index, urlList in enumerate(providers[providerName], 1)        
    }
    return allProviders if allProviders else None


def resolveProviderURL(providerURL):
    '''
    Tries to resolve a provider URL into a stream.
    '''
    try:
        temp = None
        requestHelper.delayBegin()
        r = requestHelper.GET(providerURL)
        if r.ok:
            html = r.text
            if 'var video_links' in html:
                # Try the generic videozoo \ play44 resolve first:
                temp = re.findall(r'''var video_links.*?['"]link['"]\s*?:\s*?['"](.*?)['"]''', html, re.DOTALL)
            else:
                # Try variants (found sometimes in Playpanda.net etc.):
                temp = re.findall(r'''{\s*?url\s*?:\s*?['"](.*?)['"]''', html, re.DOTALL)
                if not temp:
                    temp = re.findall(r'''file\s*?:\s*?['"](.*?)['"]''', html, re.DOTALL)
            requestHelper.delayEnd(1000) # Sleep this thread a little before the next request, if necessary.
        if temp:
            return temp[0].replace(r'\/', r'/') # Unescape any potential escaped JS slashes.
    except:
        pass

    return None