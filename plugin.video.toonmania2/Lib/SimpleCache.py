# -*- coding: utf-8 -*-
import json
from os import sep as osSeparator
from time import time

import xbmc
import xbmcvfs
from xbmcgui import getCurrentWindowId, Window
import xbmcaddon


# A simple JSON and window property cache, specialized for XBMC video add-ons.

# Think of it like a way to save an add-on "session" onto disk. The intent is to make loading faster
# (loading from disk rather than web requests) and to spare the scraped sources from redundant requests.
# But also being economical with disk reads and writes, using as few as absolutely possible.

class SimpleCache():

    '''
    Cache version log:
    3: Toonmania2 0.4.2
        In this cache version we're using separate cache files for each route the user visited.
        This way uses less memory because we only need to load the routes that the user wants to
        go to, not one huge file that has everything, with what the user wants or doesn't want.
    '''
    # Cache version, for future extension. Used with properties saved to disk.
    CACHE_VERSION = 3

    LIFETIME_THREE_DAYS = 72 # 3 days, in hours.
    LIFETIME_FIVE_DAYS = 120 # 5 days.
    LIFETIME_ONE_WEEK = 168 # 7 days.
    LIFETIME_FOREVER = 0 # Never expires.

    # Path to .../kodi/userdata/addons_data/plugin.video.toonmania2/cache/ -> where the JSON cache files will be.
    CACHE_PATH_DIR = xbmc.translatePath(xbmcaddon.Addon().getAddonInfo('profile')).decode('utf-8') + 'cache' + osSeparator

    # Property name pointing to a Python 'set()' of property names.
    # This is used to quickly tell if a property exists or not by checking its name in the set,
    # rather than retrieving a property that could be a huge JSON blob just to see that it exists.
    PROPERTY_DISK_NAMES_SET = 'scache.prop.names'


    # Property name pointing to a comma-separated list of dirty disk-enabled properties that need saving.
    # This list is converted to a set when read and used for quick testing.
    PROPERTY_DIRTY_NAMES_SET = 'scache.prop.dirty'


    def __init__(self):
        '''
        Initialised at every directory change in Kodi <= 17.6.
        '''
        self.window = Window(getCurrentWindowId())
        self.diskNamesSet = None
        self.dirtyNamesSet = None


    def setCacheProperty(self, propName, data, saveToDisk, lifetime=72):
        '''
        Creates a persistent XBMC window memory property.
        :param propName: Name/Identifier the property should have, used to retrieve it later.
        Needs to be file-system friendly, and ** cannot have commas in the name. **
        :param data: Data to store in the property, needs to be JSON-serializable.
        :param saveToDisk: Boolean if this property should be saved to a JSON cache file on
        disk to be loaded on later sessions. Best used for big collections of web-requested data.
        :param lifetime: When saving to disk, 'lifetime' specifies how many hours since its
        creation that the property should have on disk, before being erased. Defaults to 72
        hours (3 days). Setting it as '0' (zero) will make it last forever.
        '''
        if saveToDisk:
            # Create the window memory property.
            self._storeCacheProperty(propName, data, lifetime, self._getEpochHours())

            # Store the name of this disk-enabled property in a set to quickly tell
            # that it's already in memory and doesn't need to be loaded from disk.
            self._ensureDiskNamesSet()
            self.diskNamesSet.add(propName)
            self._storeMemorySet(self.PROPERTY_DISK_NAMES_SET, self.diskNamesSet)

            # Add the name of this new property to a set used by saveCacheIfDirty()
            # to tell which disk-enabled properties need saving to disk.
            self._ensureDirtyNamesSet()
            self.dirtyNamesSet.add(propName)
            self._storeMemorySet(self.PROPERTY_DIRTY_NAMES_SET, self.dirtyNamesSet)
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

        The PROPERTY_NAME values should not have commas.
        The 'PROPERTY_DATA' or 'data' fields should be JSON-serializable.
        '''
        if saveToDisk:
            self._ensureDiskNamesSet()
            self._ensureDirtyNamesSet()

            for pEntry in properties:
                propName, data, lifetime = pEntry
                self._storeCacheProperty(propName, data, lifetime, self._getEpochHours())
                self.diskNamesSet.add(propName)
                self.dirtyNamesSet.add(propName) # These properties are being created \ updated and need saving.

            self._storeMemorySet(self.PROPERTY_DISK_NAMES_SET, self.diskNamesSet)
            self._storeMemorySet(self.PROPERTY_DIRTY_NAMES_SET, self.dirtyNamesSet)
        else:
            for propName, data in properties:
                self.window.setProperty(propName, json.dumps(data)) # Memory-only properties.


    def getCacheProperty(self, propName, readFromDisk):
        '''
        Tries to return the data from a window memory property.
        For the pure property string use the setRaw(...)\getRaw(...) functions instead.
        :param propName: Name of the property to retrieve.
        :param readFromDisk: Used with properties that might be saved on disk. It tries to load
        from memory first though, then if it's not in memory we load from its file, if it exists.
        :returns: The property data, if it exists, or None.
        '''
        if readFromDisk:
            # A disk-enabled property.
            # If it's already in the disk names set then it was either added manually or
            # already loaded from disk into memory.
            self._ensureDiskNamesSet()
            if propName in self.diskNamesSet:
                propRaw = self.window.getProperty(propName)
                return json.loads(propRaw)[0] if propRaw else None # Data is always the first JSON field.
            else:
                # Disk-enabled property isn't in memory yet, try to read it from its file.
                fullPath = self.CACHE_PATH_DIR + propName + '.json'
                fileProp = self._tryLoadCacheProperty(fullPath)
                if fileProp:
                    propName, data, lifetime, epoch = fileProp
                    self._storeCacheProperty(propName, data, lifetime, epoch)
                    self.diskNamesSet.add(propName)
                    self._storeMemorySet(self.PROPERTY_DISK_NAMES_SET, self.diskNamesSet)
                    return data
                else:
                    return None
        else:
            propRaw = self.window.getProperty(propName)
            return json.loads(propRaw) if propRaw else None


    def getCacheProperties(self, propNames, readFromDisk):
        '''
        Retrieves a **generator** to more than one property data at once.
        The data is guaranteed to come in the same order as the provided names.
        '''
        if readFromDisk:
            self._ensureDiskNamesSet()
            anyLoadedFromFile = False

            for propName in propNames:
                if propName in self.diskNamesSet:
                    propRaw = self.window.getProperty(propName)
                    yield json.loads(propRaw)[0] if propRaw else None
                else:
                    fullPath = self.CACHE_PATH_DIR + propName + '.json'
                    fileProp = self._tryLoadCacheProperty(fullPath)
                    if fileProp:
                        propName, data, lifetime, epoch = fileProp
                        self._storeCacheProperty(propName, data, lifetime, epoch)
                        self.diskNamesSet.add(propName)
                        anyLoadedFromFile = True
                        yield data

            if anyLoadedFromFile:
                self._storeMemorySet(self.PROPERTY_DISK_NAMES_SET, self.diskNamesSet)
        else:
            for propName in propNames:
                propRaw = self.window.getProperty(propName)
                yield json.loads(propRaw) if propRaw else None


    '''def clearCacheProperty(self, propName, readFromDisk):
        #
        # Removes a property from memory. The next time the cache is saved, this property
        # won't be included and therefore forgotten.
        #
        self.window.clearProperty(propName)
        if readFromDisk:
            # Direct way to remove the property name from the comma-separated property name list.
            diskNamesRaw = self.window.getProperty(self.PROPERTY_DISK_NAMES_SET)
            self.window.setProperty(
                self.PROPERTY_DISK_NAMES_SET, diskNamesRaw.replace(propName, '').replace(',,', ',').strip(', ')
            )
            dirtyNamesRaw = self.window.getProperty(self.PROPERTY_DIRTY_NAMES_SET)
            self.window.setProperty(
                self.PROPERTY_DIRTY_NAMES_SET, dirtyNamesRaw.replace(propName, '').replace(',,', ',').strip(', ')
            )'''


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


    '''def clearRawProperty(self, propName):
        #
        # Clears a direct window property by name.
        # To clear a property that was created with setCacheProperty()
        # use clearCacheProperty() instead.
        #
        return self.window.clearProperty(propName)'''


    def diskFriendlyPropName(self, name):
        '''
        Cleans a name to be harddisk-friendly, as the cache file will have the same
        name of the property plus the '.json' extension.
        '''
        return name.replace('/', '_')


    def saveCacheIfDirty(self):
        '''
        Saves the disk-enabled properties that are dirty to their own files.
        '''
        # Optimised way to check if anything needs saving. Most of the time
        # 'dirtyNamesRaw' will be an empty string, easy to check for truthness.
        dirtyNamesRaw = self.window.getProperty(self.PROPERTY_DIRTY_NAMES_SET)
        if dirtyNamesRaw:
            if not xbmcvfs.exists(self.CACHE_PATH_DIR):
                xbmcvfs.mkdir(self.CACHE_PATH_DIR)

            for propName in dirtyNamesRaw.split(','):
                self._saveCacheProperty(propName)

            # Reset the dirty names set and its window property.
            self.dirtyNamesSet = set()
            self.window.setProperty(self.PROPERTY_DIRTY_NAMES_SET, '')


    def clearCacheFiles(self):
        dirPaths, filePaths = xbmcvfs.listdir(self.CACHE_PATH_DIR)
        for filePath in filePaths:
            self._writeBlankCacheFile(self.CACHE_PATH_DIR + filePath)
        # Clear the disk names set. All disk-enabled properties will be forgotten.
        self.window.setProperty(self.PROPERTY_DISK_NAMES_SET, '')
        self.diskNamesSet = set()
        return len(filePaths) > 0 # Return True if at least one file was cleared.


    def _ensureDiskNamesSet(self):
        '''
        For Kodi <= 17.6, used to initialise this class member in case it's invalid.
        But this function is only called when this member is needed.
        '''
        if self.diskNamesSet == None:
            self.diskNamesSet = self._stringToSet(self.window.getProperty(self.PROPERTY_DISK_NAMES_SET))


    def _ensureDirtyNamesSet(self):
        if self.dirtyNamesSet == None:
            self.dirtyNamesSet = self._stringToSet(self.window.getProperty(self.PROPERTY_DIRTY_NAMES_SET))


    def _storeMemorySet(self, setPropName, setObject):
        self.window.setProperty(setPropName, self._setToString(setObject))



    def _writeBlankCacheFile(self, fullPath):
        '''
        Initializes a blank cache file.
        '''
        file = xbmcvfs.File(fullPath, 'w')
        file.write('null') # JSON equivalent to None.
        file.close()


    def _tryLoadCacheProperty(self, fullPath):
        '''
        Tries to load the cache file for the named property.
        :returns: A tuple of property entries, each entry is a tuple of fields
        (propName, data, lifetime, epoch).
        '''
        currentEpoch = self._getEpochHours()
        if xbmcvfs.exists(fullPath):
            try:
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
                        # its age is now bigger than its lifetime.
                        if lifetime == 0 or lifetime >= abs(currentEpoch - epoch):
                           return (fileProp['propName'], fileProp['data'], lifetime, epoch)
            except:
                return None
        else:
            return None


    def _storeCacheProperty(self, propName, data, lifetime, epoch):
        '''
        Stores data in a persistent XBMC window memory property.
        '''
        self.window.setProperty(propName, json.dumps((data, lifetime, epoch)))


    def _saveCacheProperty(self, propName):
        '''
        Saves a specific dirty, disk-enabled property to disk.
        Assumes the destination folder already exists.
        '''
        propRaw = self.window.getProperty(propName)
        if propRaw:
            # Base structure as in _storeCacheProperty(), with the cache version added.
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


    def _setToString(self, setObject):
        return ','.join(element for element in setObject)


    def _stringToSet(self, text):
        return set(text.split(',')) if text else set() # The IF is to get a truly empty set, else it'd hold an empty string.


    def _getEpochHours(self):
        '''
        Internal. Gets the current UNIX epoch time in hours.
        '''
        return int(time() // 3600.0)


simpleCache = SimpleCache()
