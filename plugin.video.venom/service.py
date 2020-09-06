# -*- coding: utf-8 -*-

"""
	Venom
"""

import threading
import xbmc

from resources.lib.modules import control
from resources.lib.modules import log_utils
from resources.lib.modules import trakt

window = control.window

class CheckSettingsFile():
	def run(self):
		try:
			profile_dir = xbmc.translatePath('special://profile/addon_data/plugin.video.venom/')
			if not control.existsPath(profile_dir):
				success = control.makeDirs(profile_dir)
				if success:
					xbmc.log('%s : created successfully' % profile_dir, 2)
			else:
				xbmc.log('%s : already exists' % profile_dir, 2)
			settings_xml = control.joinPath(profile_dir, 'settings.xml')
			if not control.existsPath(settings_xml):
				control.setSetting('clear.all.cache', '')
				xbmc.log('%s : created successfully' % settings_xml, 2)
			else:
				xbmc.log('%s : already exists' % settings_xml, 2)
			return
		except:
			import traceback
			traceback.print_exc()
			pass


class SettingsMonitor(xbmc.Monitor):
	def __init__ (self):
		xbmc.Monitor.__init__(self)
		xbmc.log('[ plugin.video.venom ] Settings Monitor Service Starting...', 2)

	def onSettingsChanged(self):
		window.clearProperty('venom_settings')
		xbmc.sleep(50)
		refreshed = control.make_settings_dict()


class ReuseLanguageInvokerCheck:
	def run(self):
		if control.getKodiVersion() < 18:
			return
		try:
			import xml.etree.ElementTree as ET
			addon_dir = control.transPath(control.addon('plugin.video.venom').getAddonInfo('path'))
			addon_xml = control.joinPath(addon_dir, 'addon.xml')
			tree = ET.parse(addon_xml)
			root = tree.getroot()
			current_addon_setting = control.addon('plugin.video.venom').getSetting('reuse.languageinvoker')
			if current_addon_setting == '':
				return
			try:
				current_xml_setting = [str(i.text) for i in root.iter('reuselanguageinvoker')][0]
			except:
				return
			if current_xml_setting == current_addon_setting:
				return
			if not control.yesnoDialog('[B]Reuse Language Invoker[/B] SETTING/XML mismatch.\nRestore correct status(RECOMMENDED)?', '', ''):
				return
			for item in root.iter('reuselanguageinvoker'):
				item.text = current_addon_setting
				hash_start = control.gen_file_hash(addon_xml)
				tree.write(addon_xml)
				hash_end = control.gen_file_hash(addon_xml)
				if hash_start != hash_end:
					control.okDialog('Kodi must close and be restarted for the change to take effect.')
				else:
					control.okDialog('Venom', 'Error setting correct value.')
			return
		except:
			log_utils.error()
			pass


class AddonCheckUpdate:
	def run(self):
		try:
			if control.setting('general.checkAddonUpdates') == 'false':
				return
			import re
			import requests
			repo_xml = requests.get('https://raw.githubusercontent.com/123Venom/zips/master/addons.xml')
			if not repo_xml.status_code == 200:
				log_utils.log('Could not connect to repo XML, status: %s' % repo_xml.status_code, log_utils.LOGNOTICE)
				return
			repo_version = re.findall(r'<addon id=\"plugin.video.venom\".+version=\"(\d*.\d*.\d*)\"', repo_xml.text)[0]
			local_version = control.getVenomVersion()
			if control.check_version_numbers(local_version, repo_version):
				while control.condVisibility('Library.IsScanningVideo'):
					control.sleep(10000)
				log_utils.log('A newer version of Venom is available. Installed Version: v%s, Repo Version: v%s' % (local_version, repo_version), log_utils.LOGNOTICE)
				control.notification(title = 'default', message = control.lang(35523) % repo_version, icon = 'default', time=5000, sound=False)
		except:
			log_utils.error()
			pass


class SyncTraktLibrary:
	def run(self):
		control.execute('RunPlugin(plugin://%s)' % 'plugin.video.venom/?action=library_tvshowsToLibrarySilent&url=traktcollection')
		control.execute('RunPlugin(plugin://%s)' % 'plugin.video.venom/?action=library_moviesToLibrarySilent&url=traktcollection')


class SyncTraktWatched:
	def run(self):
		control.execute('RunPlugin(plugin://%s)' % 'plugin.video.venom/?action=cachesyncTVShows&timeout=720')
		control.execute('RunPlugin(plugin://%s)' % 'plugin.video.venom/?action=cachesyncMovies&timeout=720')
		# if control.setting('trakt.general.notifications') == 'true':
			# control.notification(title='default', message='Trakt Watched Status Sync Complete', icon='default', time=1, sound=False)

xbmc.log('[ plugin.video.venom ] service started', xbmc.LOGNOTICE)
CheckSettingsFile().run()
ReuseLanguageInvokerCheck().run()

try:
	AddonVersion = control.addon('plugin.video.venom').getAddonInfo('version')
	RepoVersion = control.addon('repository.venom').getAddonInfo('version')
	log_utils.log('###################   Venom   ##################', log_utils.LOGNOTICE)
	log_utils.log('#####   CURRENT Venom VERSIONS REPORT   #####', log_utils.LOGNOTICE)
	log_utils.log('########   Venom PLUGIN VERSION: %s   ########' % str(AddonVersion), log_utils.LOGNOTICE)
	log_utils.log('#####   Venom REPOSITORY VERSION: %s   #######' % str(RepoVersion), log_utils.LOGNOTICE)
	log_utils.log('############################################', log_utils.LOGNOTICE)
except:
	log_utils.log('############################# Venom ############################', log_utils.LOGNOTICE)
	log_utils.log('################# CURRENT Venom VERSIONS REPORT ################', log_utils.LOGNOTICE)
	log_utils.log('# ERROR GETTING Venom VERSION - Missing Repo of failed Install #', log_utils.LOGNOTICE)
	log_utils.log('################################################################', log_utils.LOGNOTICE)


traktCredentials = trakt.getTraktCredentialsInfo()
# check on adding while loop here with xbmc.Monitor().abortRequested() vs. inside the service function
control.execute('RunPlugin(plugin://%s)' % control.get_plugin_url({'action': 'library_service'}))

if control.setting('general.checkAddonUpdates') == 'true':
	AddonCheckUpdate().run()
	xbmc.log('[ plugin.video.venom ] Addon update check complete', xbmc.LOGNOTICE)

if traktCredentials is True:
	SyncTraktWatched().run()
	xbmc.log('[ plugin.video.venom ] Trakt watched status sync complete', xbmc.LOGNOTICE)

if control.setting('autoTraktOnStart') == 'true':
	SyncTraktLibrary().run()
	xbmc.log('[ plugin.video.venom ] Trakt Library sync complete', xbmc.LOGNOTICE)

if int(control.setting('schedTraktTime')) > 0:
	log_utils.log('###############################################################', log_utils.LOGNOTICE)
	log_utils.log('#################### STARTING TRAKT SCHEDULING ################', log_utils.LOGNOTICE)
	log_utils.log('#################### SCHEDULED TIME FRAME '+ control.setting('schedTraktTime')  + ' HOURS ###############', log_utils.LOGNOTICE)
	timeout = 3600 * int(control.setting('schedTraktTime'))
	schedTrakt = threading.Timer(timeout, SyncTraktLibrary().run())
	schedTrakt.start()
	xbmc.log('[ plugin.video.venom ] Trakt Scheduled Library sync complete', xbmc.LOGNOTICE)


settings_monitor = SettingsMonitor()
settings_monitor.waitForAbort()
xbmc.log('[ plugin.video.venom ] service stopped', xbmc.LOGNOTICE)