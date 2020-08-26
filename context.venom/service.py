# -*- coding: utf-8 -*-

import xbmc
import xbmcaddon

properties = [
	'context.venom.settings',
	'context.venom.traktManager',
	'context.venom.clearProviders',
	'context.venom.clearBookmark',
	'context.venom.rescrape',
	'context.venom.playFromHere',
	'context.venom.autoPlay',
	'context.venom.sourceSelect',
	'context.venom.findSimilar',
	'context.venom.browseSeries',
	'context.venom.browseEpisodes',]


class PropertiesUpdater(xbmc.Monitor):
	def __init__(self):
		for id in properties:
			if xbmcaddon.Addon().getSetting(id) == 'true':
				xbmc.executebuiltin('SetProperty({0},true,home)'.format(id))
				xbmc.log('Context menu item enabled: {0}'.format(id),xbmc.LOGNOTICE)

	def onSettingsChanged(self):
		for id in properties:
			if xbmcaddon.Addon().getSetting(id) == 'true':
				xbmc.executebuiltin('SetProperty({0},true,home)'.format(id))
				xbmc.log('Context menu item enabled: {0}'.format(id),xbmc.LOGNOTICE)
			else:
				xbmc.executebuiltin('ClearProperty({0},home)'.format(id))
				xbmc.log('Context menu item disabled: {0}'.format(id),xbmc.LOGNOTICE)

# start monitoring settings changes events
xbmc.log('Context.Venom: service started', xbmc.LOGNOTICE)
properties_monitor = PropertiesUpdater()

# wait until abort is requested
properties_monitor.waitForAbort()
xbmc.log('Context.Venom: service stopped',xbmc.LOGNOTICE)
