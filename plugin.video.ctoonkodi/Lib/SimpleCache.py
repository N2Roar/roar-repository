# -*- coding: utf-8 -*-
import json
from time import time

import xbmc
import xbmcvfs
from xbmcgui import getCurrentWindowId, Window
import xbmcaddon


# A simple JSON and window property cache, specialized for XBMC video add-ons.

# Think of it like a way to save an add-on "session" onto disk. The intent is to make loading faster
# (loading from disk rather than web requests) and to spare the web sources from redundant requests.
# But also being economical with disk reads and writes, using as few as absolutely possible.

class SimpleCache():

    '''
    Cache version log:
    1: CTOONKodi 0.3.9
    '''

    # Cache version, for future extension. Used with properties saved to disk.
    CACHE_VERSION = 1

    LIFETIME_THREE_DAYS = 72 # 3 days, in hours.
    LIFETIME_FIVE_DAYS = 120 # 5 days.
    LIFETIME_ONE_WEEK = 168 # 7 days.
    LIFETIME_FOREVER = 0 # Never expires (see _loadFileCacheHelper())

    CACHE_PATH_DIR = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile')).decode('utf-8') + 'cache/'

    # Property name pointing to a Python 'set()' of property names.
    # This is used to quickly tell if a property exists or not by checking its name in the set,
    # rather than retrieving a property that could be a huge JSON blob just to see that it exists.
    PROPERTY_DISK_CACHE_NAMES = 'scache.prop.names'

    # Property name pointing to a comma-separated list of dirty disk-enabled properties that need saving.
    # This list is converted to a set when read and used for quick testing.
    PROPERTY_DIRTY_NAMES = 'scache.prop.dirty'


    def __init__(self):
        # Initialised at every directory change in Kodi <= 17.6
        self.diskCacheNames = None
        self.dirtyNames = None
        self.window = Window(getCurrentWindowId())


    def setCacheProperty(self, propName, data, saveToDisk, lifetime=72):
        '''
        Creates a persistent XBMC window memory property.
        :param propName: Name/Identifier the property should have, used to retrieve it later.
        Needs to be file-system friendly, and cannot have commas in the name.
        :param data: Data to store in the property, needs to be JSON-serializable.
        :param saveToDisk: Boolean if this property should be saved to a JSON cache file on
        disk to be loaded on later sessions. Best used for big collections of web-requested data.
        :param lifetime: When saving to disk, 'lifetime' specifies how many hours since its
        creation that the property should exist on disk, before being erased. Defaults to 72
        hours (3 days). Setting it as '0' (zero) will make it last forever.
        '''
        if saveToDisk:
            # A disk-enabled property.
            self._pushCacheProperty(propName, data, lifetime, self._getEpochHours())
            self._addDiskCacheName(propName) # Used to quickly tell if a property is in memory or not.
            self._addDirtyName(propName) # Used by saveCacheIfDirty().
        else:
            # A memory-only property. Other fields (lifetime, epoch etc.) are not needed.
            self.window.setProperty(propName, json.dumps(data))


    def setCacheProperties(self, properties, saveToDisk):
        '''
        Convenience function to create several properties at once.
        :param properties: For disk-enabled properties (saveToDisk=True), it's an iterable where
        each entry should be a tuple, list or other indexable object of this format:
        ((str)PROPERTY_NAME, (anything)PROPERTY_DATA, (int)LIFETIME_HOURS)
        Otherwise (with saveToDisk=False), 'properties' is an iterable of (name, data) pairs.

        The 'PROPERTY_DATA' field should be JSON-serializable.
        '''
        if saveToDisk:
            self._ensureDiskCacheNames()
            self._ensureDirtyNames()
            for pEntry in properties:
                name, data, lifetime = pEntry
                self._pushCacheProperty(propName, data, lifetime, self._getEpochHours())
                self.diskCacheNames.add(name)
                self.dirtyNames.add(name) # These properties are being created \ updated and need saving.
            self._flushDiskCacheNames()
            self._flushDirtyNames()
        else:
            for name, data in properties:
                self.window.setProperty(name, json.dumps(data)) # Memory-only properties.


    def getCacheProperty(self, propName, readFromDisk):
        '''
        Tries to return the JSON-loaded data from a window memory property.
        For the pure property string use the setRaw(...)\getRaw(...) functions instead.
        :param propName: Name of the property to retrieve.
        :param readFromDisk: Used with properties that might be saved on disk (it tries to load
        from memory first though).
        :returns: The property data, if it exists, or None.
        '''
        if readFromDisk:
            # A disk-enabled property.
            self._ensureDiskCacheNames()
            if propName in self.diskCacheNames:
                propRaw = self.window.getProperty(propName)
                return json.loads(propRaw)[0] if propRaw else None
            else:
                # Disk-enabled property isn't in memory yet, try to load it to memory from its file.
                fileProp = self._tryLoadCacheProperty(propName)
                if fileProp:
                    propName, data, lifetime, epoch = fileProp
                    self._pushCacheProperty(propName, data, lifetime, epoch)
                    self.diskCacheNames.add(propName)
                    self._flushDiskCacheNames()
                    return data
                else:
                    return None
        else:
            # A memory-only property, points directly to data.
            propRaw = self.window.getProperty(propName)
            return json.loads(propRaw) if propRaw else None


    def getCacheProperties(self, propNames, readFromDisk):
        '''
        Retrieves a **generator** to more than one property data at once.
        The data is guaranteed to come in the same order as the provided names.
        '''
        if readFromDisk:
            loadedFromFile = False
            self._ensureDiskCacheNames()

            for propName in propNames:
                if propName in self.diskCacheNames:
                    propRaw = self.window.getProperty(propName)
                    yield json.loads(propRaw)[0] if propRaw else None
                else:
                    fileProp = self._tryLoadCacheProperty(propName)
                    if fileProp:
                        propName, data, lifetime, epoch = fileProp[0]
                        self._pushCacheProperty(propName, data, lifetime, epoch)
                        self.diskCacheNames.add(propName)
                        loadedFromFile = True
                        yield data

            if loadedFromFile:
                self._flushDiskCacheNames()
        else:
            for propName in propNames:
                propRaw = self.window.getProperty(propName)
                yield json.loads(propRaw) if propRaw else None # There's just a data field in memory-only properties.


    def clearCacheProperty(self, propName, readFromDisk):
        '''
        Removes a property from memory. The next time the cache is saved, this property
        won't be included and therefore forgotten.
        '''
        self.window.clearProperty(propName)
        if readFromDisk:
            self._ensureDiskCacheNames()
            self.diskCacheNames.discard(propName)
            self._flushDiskCacheNames()


    def setRawProperty(self, propName, data):
        '''
        Convenience function to set a window memory property that doesn't
        need JSON serialization or saving to disk.
        Used for unimportant memory-only properties that should persist between add-on
        directories.
        :param propName: The name of the property used to identify the data, later used
        to retrieve it.
        :param rawData: String data, stored as it is.
        '''
        self.window.setProperty(propName, data)


    def getRawProperty(self, propName):
        '''
        Retrieves a direct window property by name.
        '''
        return self.window.getProperty(propName)


    def clearRawProperty(self, propName):
        '''
        Clears a direct window property by name.
        To clear a property that was created with setCacheProperty()
        use clearCacheProperty() instead.
        '''
        return self.window.clearProperty(propName)


    def saveCacheIfDirty(self):
        dirtyNamesRaw = self.window.getProperty(self.PROPERTY_DIRTY_NAMES)
        if dirtyNamesRaw:
            for propName in dirtyNamesRaw.split(','):
                self._saveCacheProperty(propName)
            self.window.setProperty(self.PROPERTY_DIRTY_NAMES, '') # "Clears" the dirty names set.


    def clearCacheFiles(self):
        dirPaths, filePaths = xbmcvfs.listdir(self.CACHE_PATH_DIR)
        for filePath in filePaths:
            self._writeBlankCacheFile(self.CACHE_PATH_DIR + filePath)
        # Overwrite the 'diskCacheNames' set with an empty one.
        # All disk-enabled properties will be forgotten.
        self.diskCacheNames = set()
        self._flushDiskCacheNames()

        return len(filePaths) > 0 # 'True' if one or more cache files were cleared / reset.


    def _ensureDiskCacheNames(self):
        if not self.diskCacheNames:
            self.diskCacheNames = self._stringToSet(self.window.getProperty(self.PROPERTY_DISK_CACHE_NAMES))


    def _addDiskCacheName(self, propName):
        self._ensureDiskCacheNames()
        self.diskCacheNames.add(propName)
        self._flushDiskCacheNames()


    def _flushDiskCacheNames(self):
        '''
        Internal. This needs to be used **every time** after setting one or more properties, to make sure
        the latest disk cache names set is stored in its window memory property.
        Assumes 'self.diskCacheNames' is a valid Python object.
        '''
        self.window.setProperty(self.PROPERTY_DISK_CACHE_NAMES, self._setToString(self.diskCacheNames))


    def _ensureDirtyNames(self):
        if not self.dirtyNames:
            self.dirtyNames = self._stringToSet(self.window.getProperty(self.PROPERTY_DIRTY_NAMES))


    def _addDirtyName(self, propName):
        '''
        Adds a property name to the set of 'dirty disk-enabled properties'.
        Being in this set means the property will be saved to disk whenever
        saveCacheIfDirty() is called.
        '''
        self._ensureDirtyNames()
        self.dirtyNames.add(propName)
        self._flushDirtyNames()


    def _flushDirtyNames(self):
        self.window.setProperty(self.PROPERTY_DIRTY_NAMES, self._setToString(self.dirtyNames))


    def _tryLoadCacheProperty(self, propName):
        '''
        Tries to load the cache file for the named property.
        Assumes 'self.diskCacheNames' exists.
        If a cache file doesn't exist for a property, a blank cache file is created.
        :returns: A tuple of property entries, each entry is a tuple of fields
        (propName, data, lifetime, epoch).
        '''
        currentEpoch = self._getEpochHours()
        fullPath = self.CACHE_PATH_DIR + propName + '.json'
        try:
            if xbmcvfs.exists(fullPath):            
                file = xbmcvfs.File(fullPath)
                data = file.read()
                file.close()

                if data and data != 'null':
                    fileProp = json.loads(data)                                        
                    
                    # Version restriction.
                    version = fileProp['version']
                    if version >= self.CACHE_VERSION:
                        lifetime = fileProp['lifetime']
                        epoch = fileProp['epoch']
                        # Lifetime restriction. See if the property lasts forever or if
                        # the elapsed time since its creation epoch is bigger than its lifetime.
                        if lifetime == 0 or lifetime >= abs(currentEpoch - epoch):
                           return (fileProp['propName'], fileProp['data'], lifetime, epoch)
            else:
                # Initialize a blank cache file.
                xbmcvfs.mkdir(self.CACHE_PATH_DIR)
                self._writeBlankCacheFile(fullPath)
        except:
            pass
        return None # Fall-through.


    def _pushCacheProperty(self, propName, data, lifetime, epoch):
        '''
        Internal.
        Stores data in a persistent XBMC window memory property.
        '''
        self.window.setProperty(propName, json.dumps((data, lifetime, epoch)))


    def _saveCacheProperty(self, propName):
        '''
        Internal.
        Saves a specific dirty, disk-enabled property to disk.
        Assumes the destination folder already exists.
        Assumes 'self.diskCacheNames' has already been refreshed \ updated.
        '''
        propRaw = self.window.getProperty(propName)
        if propRaw:
            # Base structure as in _pushCacheProperty(), with the cache version added.
            data, lifetime, epoch = json.loads(propRaw)
            file = xbmcvfs.File(self.CACHE_PATH_DIR + propName + '.json', 'w')
            file.write(
                json.dumps(
                    {
                        'version': self.CACHE_VERSION,
                        'propName': propName,
                        'lifetime': lifetime,
                        'epoch': epoch,
                        'data': data
                    }
                )
            )
            file.close()


    def _writeBlankCacheFile(self, fullPath):
        '''Assumes the directory to the file exists.'''
        file = xbmcvfs.File(fullPath, 'w')
        file.write('null')
        file.close()


    def _setToString(self, setObject):
        return ','.join(element for element in setObject)


    def _stringToSet(self, text):
        return set(text.split(',')) if text else set()


    def _getEpochHours(self):
        '''
        Internal. Gets the current UNIX epoch time in hours.
        '''
        return int(time() // 3600.0)


simpleCache = SimpleCache()
