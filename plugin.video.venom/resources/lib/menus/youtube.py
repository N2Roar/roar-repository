# -*- coding: utf-8 -*-


from resources.lib.modules import log_utils
from resources.lib.modules import control
from resources.lib.modules import youtube
from resources.lib.modules import youtube_menu

import os,sys,re,datetime,urlparse

thishandle = int(sys.argv[1])

# initializes as Kids Corner, functions can override based on action and subid.
class yt_index:
    def __init__(self):
        self.action = 'kidscorner'
        self.base_url = 'aHR0cDovL3Qyay1yZXBvc2l0b3J5Lm1sL0lUL0lUL3htbHMveW91dHViZS8='.decode('base64')
        self.mainmenu = 'JXNrbm1haW4ueG1s'.decode('base64') % (self.base_url)
        self.submenu = 'JXMvJXMueG1s'.decode('base64')
        self.default_icon  = 'JXMvaWNvbnMvaWNvbi5wbmc='.decode('base64')
        # self.default_icon  = control.addonIcon()
        self.default_fanart = 'aHR0cDovL3Qyay1yZXBvc2l0b3J5Lm1sL1QySy9yZXBvc2l0b3J5LlQySy9wbHVnaW4udmlkZW8uaXQvZmFuYXJ0LmpwZw=='.decode('base64')
        # self.default_fanart = control.addonFanart()

    def init_vars(self, action):
        try:
            if action == 'fitness':
                self.action   = 'fitness'
                self.base_url = 'aHR0cDovL3Qyay1yZXBvc2l0b3J5Lm1sL0lUL0lUL3Rlc3QlMjB4bWwlMjBmaWxlcy94bWxzL2ZpdG5lc3N6b25lLw=='.decode('base64')
                self.mainmenu = 'JXNmem1haW4ueG1s'.decode('base64') % (self.base_url)
            elif action == 'youtube':
                self.action   = 'youtube'
                self.base_url = 'aHR0cDovL3Qyay1yZXBvc2l0b3J5Lm1sL0lUL0lUL3htbHMveW91dHViZS8='.decode('base64')
                self.mainmenu = 'JXN5dG1haW4ueG1s'.decode('base64') % (self.base_url)
            elif action == 'legends':
                self.action   = 'legends'
                self.base_url = 'aHR0cDovL3Qyay1yZXBvc2l0b3J5Lm1sL0lUL0lUL3Rlc3QlMjB4bWwlMjBmaWxlcy94bWxzL2xlZ2VuZHMvbWVudS8='.decode('base64')
                self.mainmenu = 'JXNpaG1haW4ueG1s'.decode('base64') % (self.base_url)
            elif action == 'moviesyt':
                self.action   = 'moviesyt'
                self.base_url = 'aHR0cDovL20zdS54eXovbXRiL3l0bW92aWVzLw=='.decode('base64')
                self.mainmenu = 'JXNtb3ZpZXMucGhw'.decode('base64') % (self.base_url)
            elif action == 'kings':
                self.action   = 'kings'
                self.base_url = 'aHR0cDovL20zdS54eXovbXRiL3l0bW92aWVzLw=='.decode('base64')
                self.mainmenu = 'JXNraW5ncy5waHA='.decode('base64') % (self.base_url)
            elif action == 'kungfu':
                self.action   = 'kungfu'
                self.base_url = 'aHR0cDovL20zdS54eXovbXRiL3l0bW92aWVzLw=='.decode('base64')
                self.mainmenu = 'JXNrdW5nZnUucGhw'.decode('base64') % (self.base_url)
            elif action == 'urban':
                self.action   = 'urban'
                self.base_url = 'aHR0cDovL20zdS54eXovbXRiL3l0bW92aWVzLw=='.decode('base64')
                self.mainmenu = 'JXN1cmJhbi5waHA='.decode('base64') % (self.base_url)
            elif action == 'scifi':
                self.action   = 'scifi'
                self.base_url = 'aHR0cDovL20zdS54eXovbXRiL3l0bW92aWVzLw=='.decode('base64')
                self.mainmenu = 'JXNzY2lmaS50eHQ='.decode('base64') % (self.base_url)
            elif action == 'tvReviews':
                self.action   = 'tvReviews'
                self.base_url = 'aHR0cDovL3Qyay1yZXBvc2l0b3J5Lm1sL0lUL0lUL21lbnUv'.decode('base64')
                self.mainmenu = 'JXN0ZWxldmlzaW9uLnhtbA=='.decode('base64') % (self.base_url)
            elif action == 'movieReviews':
                self.action   = 'movieReviews'
                self.base_url = 'aHR0cDovL3Qyay1yZXBvc2l0b3J5Lm1sL0lUL0lUL21lbnUv'.decode('base64')
                self.mainmenu = 'JXNtb3ZpZXMueG1s'.decode('base64') % (self.base_url)
            self.submenu = self.submenu % (self.base_url, '%s')
            self.default_icon = self.default_icon % (self.base_url)
            self.default_fanart = self.default_fanart % (self.base_url)
        except:
            pass

    def root(self, action):
        try:
            self.init_vars(action)
            menuItems = youtube_menu.youtube_menu().processMenuFile(self.mainmenu)
            for name,section,searchid,subid,playlistid,channelid,videoid,iconimage,fanart,description in menuItems:
                if subid != 'false': # Means this item points to a submenu
                    youtube_menu.youtube_menu().addMenuItem(name, self.action, subid, iconimage, fanart, description, True)
                elif searchid != 'false': # Means this is a search term
                    youtube_menu.youtube_menu().addSearchItem(name, searchid, iconimage, fanart)
                elif videoid != 'false': # Means this is a video id entry
                    youtube_menu.youtube_menu().addVideoItem(name, videoid, iconimage, fanart)
                elif channelid != 'false': # Means this is a channel id entry
                    youtube_menu.youtube_menu().addChannelItem(name, channelid, iconimage, fanart)
                elif playlistid != 'false': # Means this is a playlist id entry
                    youtube_menu.youtube_menu().addPlaylistItem(name, playlistid, iconimage, fanart)
                elif section != 'false': # Means this is a section placeholder/info line
                    youtube_menu.youtube_menu().addSectionItem(name, self.default_icon, self.default_fanart)
            self.endDirectory()
        except:
            pass

    def get(self, action, subid):
        try:
            self.init_vars(action)
            thisMenuFile = self.submenu % (subid)
            menuItems = youtube_menu.youtube_menu().processMenuFile(thisMenuFile)
            for name,section,searchid,subid,playlistid,channelid,videoid,iconimage,fanart,description in menuItems:
                if subid != 'false': # Means this item points to a submenu
                    youtube_menu.youtube_menu().addMenuItem(name, self.action, subid, iconimage, fanart, description, True)
                elif searchid != 'false': # Means this is a search term
                    youtube_menu.youtube_menu().addSearchItem(name, searchid, iconimage, fanart)
                elif videoid != 'false': # Means this is a video id entry
                    youtube_menu.youtube_menu().addVideoItem(name, videoid, iconimage, fanart)
                elif channelid != 'false': # Means this is a channel id entry
                    youtube_menu.youtube_menu().addChannelItem(name, channelid, iconimage, fanart)
                elif playlistid != 'false': # Means this is a playlist id entry
                    youtube_menu.youtube_menu().addPlaylistItem(name, playlistid, iconimage, fanart)
                elif section != 'false': # Means this is a section placeholder/info line
                    youtube_menu.youtube_menu().addSectionItem(name, self.default_icon, self.default_fanart)
            self.endDirectory()
        except:
            pass

    def endDirectory(self):
        control.directory(thishandle, cacheToDisc=True)
