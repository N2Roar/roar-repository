# -*- coding: utf-8 -*-
import json
from string import ascii_uppercase
from datetime import datetime
from itertools import chain

from Lib.SimpleCache import simpleCache as cache
from Lib.RequestHelper import requestHelper


class CatalogHelper():

    # Persistent memory properties used to hold the last API and the last route (the website "area" being
    # displayed) used to build the catalog of items. Used to tell if a new catalog needs to be built.
    PROPERTY_CATALOG_API = 'toonmania2.catalogAPI'
    PROPERTY_CATALOG_ROUTE = 'toonmania2.catalogRoute'
    # Property name for the catalog of items itself. See catalogFromIterable() for more info.
    PROPERTY_CATALOG = 'toonmania2.catalog'

    LETTERS_SET = set(ascii_uppercase) # Used in the catalogFromIterable() function.


    def __init__(self):
        '''
        Initialises a dict member to map API routes to catalog iterable creation functions.
        This dict is used in self.getCatalog().
        '''
        self.catalogFunctions = {
            '/GetAllMovies': self.allRouteCatalog, # Dubbed movies from animetoon / subbed movies from animeplus.
            '/GetAllCartoon': self.allRouteCatalog, # Cartoons from animetoon.
            '/GetAllDubbed': self.allRouteCatalog, # Dubbed anime from animetoon.
            '/GetAllShows': self.allRouteCatalog, # Subbed anime from animeplus.
            '/GetUpdates/': self.latestUpdatesCatalog,
            '/GetGenres/': self.genreSearchCatalog,
            '_searchResults': self.searchResultsCatalog,
            # Otherwise defaults to the 'genericCatalog' function.
        }


    def getCatalog(self, params):
        '''
        Retrieves the catalog from a persistent window property between different add-on
        states, or recreates the catalog if needed.

        The catalog is a dictionary of lists of entries, used to store data between add-on states to make xbmcgui.ListItems:
        {
            (1. Sections, as in alphabet sections for list items: #, A, B, C, D, E, F etc., each section holds a tuple of items.)
            A: (
                item, item, item, ...    (2. Items, each item is a tuple with the format seen in makeCatalogEntry().)
            )
            B: (...)
            C: (...)
        }
        '''
        def _buildCatalog():
            catalog = self.catalogFunctions.get(params['route'], self.genericCatalog)(params)
            cache.setCacheProperty(self.PROPERTY_CATALOG, catalog, saveToDisk = False)
            return catalog

        # If these properties are empty (like when coming in from a favourites menu), or if a different
        # route (website area) or a different API was stored in this property, then reload it.
        lastAPI = cache.getRawProperty(self.PROPERTY_CATALOG_API)
        lastRoute = cache.getRawProperty(self.PROPERTY_CATALOG_ROUTE)
        if (
            params['api'] != lastAPI
            or params['route'] != lastRoute
            or 'genreName' in params # Special-case for the genre search, same api\route but 'genreName' changes.
            or 'query' in params    # Special-case for the name search, same api\route but 'query' changes.
            or 'searchData' in params # Special-case for search results, we might be coming in from Kodi Favourites.
        ):
            cache.setRawProperty(self.PROPERTY_CATALOG_API, params['api'])
            cache.setRawProperty(self.PROPERTY_CATALOG_ROUTE, params['route'])
            catalog = _buildCatalog()
        else:
            catalog = cache.getCacheProperty(self.PROPERTY_CATALOG, readFromDisk = False)
            if not catalog:
                catalog = _buildCatalog()
        return catalog


    def makeCatalogEntry(self, entry):
        '''
        Grabs the relevant data we care from a parent JSON entry (show\movie).
        :returns: A tuple of the format (id, name, description, [genres], released)
        '''
        return (
            entry['id'],
            entry['name'].strip(),
            entry['description'].strip() if entry['description'] else '',# Might be empty or None.
            entry['genres'], # Might be an empty list.
            entry.get('released', None)
        )


    def getEmptyCatalog(self):
        return {key: [ ] for key in ascii_uppercase + '#'}


    def catalogFromIterable(self, iterable):
        '''
        Splits items from an iterable into an alphabetised catalog.
        Each item in the iterable is a tuple: (id, name, description, genres, released)
        ID, name and description are str, genres is a str list.
        Description and genres list might be empty.
        '''
        catalog = self.getEmptyCatalog()
        for item in iterable:
            itemKey = item[1][0].upper()
            catalog[itemKey if itemKey in self.LETTERS_SET else '#'].append(item)
        return catalog


    def genericCatalog(self, params):
        '''
        Returns a catalog for either the '/GetNew(...)' or '/GetPopular(...)' routes.
        These routes are cached memory-only, so they last one Kodi session. Closing and
        reopening Kodi will make a new web request for fresh data.
        '''
        api = params['api']
        route = params['route']

        # Get the corresponding '/GetAll(...)' route with the data that will be needed.
        allRoute = route.replace('New', 'All') if '/GetNew' in route else route.replace('Popular', 'All')

        genericIDs = cache.getCacheProperty(api+route, readFromDisk = False)
        if not genericIDs:
            requestHelper.setAPISource(api)
            requestHelper.delayBegin()
            jsonData = requestHelper.routeGET(route)
            if jsonData:
                genericIDs = tuple(entry['id'] for entry in jsonData)
                cache.setCacheProperty(api+route, genericIDs, saveToDisk = False)
            requestHelper.delayEnd(500)

        if genericIDs:
            # Load all the main routes of the API (they are disk-cached), to compare IDs with.
            allData = self._getMainRoutesData(api, allRoute)
            idDict = {item[0]: item for item in chain.from_iterable(allData)}
            return self.catalogFromIterable(idDict[entryID] for entryID in genericIDs if entryID in idDict)
        else:
            return self.getEmptyCatalog()


    def allRouteCatalog(self, params):
        '''
        Returns a catalog for one of the main '/GetAll(...)' routes.
        '''
        api = params['api']
        route = params['route']

        propName = cache.diskFriendlyPropName(api + route)

        jsonData = cache.getCacheProperty(propName, readFromDisk = True)
        if not jsonData:
            requestHelper.setAPISource(api)
            requestHelper.delayBegin()
            jsonData = requestHelper.routeGET(route)
            if jsonData:
                cache.setCacheProperty(propName, jsonData, saveToDisk = True) # Defaults to 3 days cache lifetime.
            requestHelper.delayEnd(500)

        if jsonData:
            return self.catalogFromIterable(self.makeCatalogEntry(entry) for entry in jsonData)
        else:
            return self.getEmptyCatalog()


    def latestUpdatesCatalog(self, params):
        '''
        Returns a catalog for the Latest Updates category.
        This route is cached memory-only to make sure it's always fresh.
        This memory cache lasts one Kodi session. Closing Kodi and reopening it
        will do a new web request.
        '''
        api = params['api']

        if api == requestHelper.API_ANIMETOON:
            _PROPERTY_LAST_UPDATES = 'tmania2.prop.toonUpdates'
        else:
            _PROPERTY_LAST_UPDATES = 'tmania2.prop.plusUpdates'

        # Memory-only cache of the latest updates IDs.
        latestIDs = cache.getCacheProperty(_PROPERTY_LAST_UPDATES, readFromDisk = False)
        if not latestIDs:
            requestHelper.setAPISource(api)
            requestHelper.delayBegin()
            jsonData = requestHelper.routeGET(params['route'])
            if jsonData:
                latestIDs = tuple(entry['id'] for entry in jsonData.get('updates', [ ]))
                cache.setCacheProperty(_PROPERTY_LAST_UPDATES, latestIDs, saveToDisk = False)
            requestHelper.delayEnd(1000)

        if latestIDs:
            # Latest Updates needs all items of the current API loaded, to compare IDs with.
            # Make a dictionary to map item IDs to the items themselves.
            allData = self._getMainRoutesData(api)
            idDict = {item[0]: item for item in chain.from_iterable(allData)}
            # Find the entries based on their IDs from the latest updates list.
            return self.catalogFromIterable(idDict[entryID] for entryID in latestIDs if entryID in idDict)
        else:
            return self.getEmptyCatalog()


    def searchResultsCatalog(self, params):
        '''
        Gerates a catalog from show\movie IDs from a name search.
        '''
        from ast import literal_eval
        searchData = literal_eval(params.get('searchData', 'None'))
        if searchData:
            return self.catalogFromIterable(
                self.makeCatalogEntry(
                    {'id': resultItem[0], 'name': resultItem[1], 'description': resultItem[2], 'genres':[]}
                )
                for resultItem in searchData
            )
        else:
            return self.getEmptyCatalog()


    def genreSearchCatalog(self, params):
        '''
        Gerates a catalog from a genre search, the genre query in params['genreName'].
        '''
        genreName = params['genreName']
        # A genre search needs all of the items of the current API loaded, to compare genres with.
        allData = self._getMainRoutesData(params['api'])
        # Inclusion test for 'genreName'.
        return self.catalogFromIterable(
            entry for entry in chain.from_iterable(allData) if genreName in entry[3]
        )


    def _getMainRoutesData(self, api, customRoute=None):
        '''
        Loads all the main routes from one of the APIs to be used in the "filtering" catalog functions, like
        the latestUpdatesCatalog, genreSearchCatalog etc. that need all the items loaded at once.
        :returns: A dict of the '/GetAll(...)' routes of the API, each route key holds a list of catalog entries.
        '''
        requestHelper.setAPISource(api)
        if customRoute:
            routeAlls = (customRoute,)
        else:
            if api == requestHelper.API_ANIMETOON:
                routeAlls = ('/GetAllCartoon', '/GetAllMovies', '/GetAllDubbed') # Animetoon 'All' routes.
            else:
                routeAlls = ('/GetAllMovies', '/GetAllShows') # Animeplus 'All' routes.

        routesData = [ ]
        newProperties = [ ]
        for route in routeAlls:
            # Try to get the cached property first.
            jsonData = cache.getCacheProperty(
                cache.diskFriendlyPropName(api + route), readFromDisk = True
            )
            if not jsonData:
                requestHelper.delayBegin()
                jsonData = requestHelper.routeGET(route)
                if jsonData:
                    newProperties.append(
                        (cache.diskFriendlyPropName(api + route), jsonData, cache.LIFETIME_THREE_DAYS)
                    )
                requestHelper.delayEnd(1000) # Always delay between requests so we don't abuse the source.
            routesData.append(tuple(self.makeCatalogEntry(entry) for entry in jsonData))

        if newProperties:
            cache.setCacheProperties(newProperties, saveToDisk=True)

        return routesData


catalogHelper = CatalogHelper()
