# -*- coding: utf-8 -*-

'''
	Venom Add-on
'''

import re
import requests
from sys import argv

try:
	from urllib import quote_plus, urlencode, unquote
except:
	from urllib.parse import quote_plus, urlencode, unquote

from resources.lib.modules import control
from resources.lib.modules import log_utils
from resources.lib.modules.source_utils import supported_video_extensions

try:
	token = control.addon('script.module.resolveurl').getSetting('PremiumizeMeResolver_token')
except:
	token = ''
	pass

FormatDateTime = '%y%d%m%I%M%f'
CLIENT_ID = '522962560' # used to auth
BaseUrl = 'https://www.premiumize.me/api'
folder_list = '%s/folder/list' % BaseUrl
folder_rename = '%s/folder/rename' % BaseUrl
folder_delete = '%s/folder/delete' % BaseUrl
item_details = '%s/item/details' % BaseUrl
item_delete = '%s/item/delete' % BaseUrl
item_rename = '%s/item/rename' % BaseUrl
transfer_create = '%s/transfer/create' % BaseUrl
transfer_directdl = '%s/transfer/directdl' % BaseUrl
transfer_list = '%s/transfer/list' % BaseUrl
transfer_clear_finished = '%s/transfer/clearfinished' % BaseUrl
transfer_delete = '%s/transfer/delete' % BaseUrl
account_info = '%s/account/info' % BaseUrl
cache_check = '%s/cache/check' % BaseUrl
list_services_path = '%s/services/list' % BaseUrl
pm_icon = control.joinPath(control.artPath(), 'premiumize.png')
addonFanart = control.addonFanart()


class Premiumize:
	def __init__(self):
		self.hosts = []
		self.patterns = []
		self.headers = {'User-Agent': 'Venom for Kodi', 'Authorization': 'Bearer %s' % token}


	def _get(self, url):
		try:
			response = requests.get(url, headers=self.headers, timeout=15).json()
			if 'status' in response:
				if response.get('status') == 'success':
					return response
				if response.get('status') == 'error':
					control.notification(title='default', message=response.get('message'), icon='default')
		except:
			log_utils.error()
			pass
		return None


	def _post(self, url, data={}):
		try:
			response = requests.post(url, data, headers=self.headers, timeout=15).json()
			if 'status' in response:
				if response.get('status') == 'success':
					return response
				if response.get('status') == 'error':
					control.notification(title='default', message=response.get('message'), icon='default')
		except:
			log_utils.error()
			pass
		return None


	def auth(self):
		data = {'client_id': CLIENT_ID, 'response_type': 'device_code'}
		token = requests.post('https://www.premiumize.me/token', data=data, timeout=15).json()
		expiry = float(token['expires_in'])
		token_ttl = token['expires_in']
		poll_again = True
		success = False
		progressDialog = control.progressDialog
		progressDialog.create(control.lang(40054),
								line1=control.lang(32513) % token['verification_uri'],
								line2=control.lang(32514) % token['user_code'])
		progressDialog.update(0)

		while poll_again and not token_ttl <= 0 and not progressDialog.iscanceled():
			poll_again, success = self.poll_token(token['device_code'])
			progress_percent = 100 - int((float((expiry - token_ttl) / expiry) * 100))
			progressDialog.update(progress_percent)
			control.sleep(token['interval'] * 1000)
			token_ttl -= int(token['interval'])
		progressDialog.close()
		if success:
			control.notification(title='default', message=40052, icon=pm_icon)


	def poll_token(self, device_code):
		data = {'client_id': CLIENT_ID, 'code': device_code, 'grant_type': 'device_code'}
		token = requests.post('https://www.premiumize.me/token', data=data, timeout=15).json()
		if 'error' in token:
			if token['error'] == "access_denied":
				return False, False
			return True, False
		control.addon('script.module.resolveurl').setSetting('PremiumizeMeResolver_token', token['access_token'])
		self.headers = {'User-Agent': 'Venom for Kodi', 'Authorization': 'Bearer %s' % token['access_token']}
		control.addon('script.module.resolveurl').setSetting('PremiumizeMeResolver_auth', 'true')
		return False, True


	def get_acount_info(self):
		try:
			accountInfo = self._get(account_info)
			return accountInfo
		except:
			log_utils.error()
			pass
		return None


	def acount_info_to_dialog(self):
		from datetime import datetime
		import math
		try:
			accountInfo = self.get_acount_info()
			expires = datetime.strptime(str(accountInfo['premium_until']), FormatDateTime)
			days_remaining = (expires - datetime.today()).days
			expires = expires.strftime('%Y-%m-%d')
			points_used = int(math.floor(float(accountInfo['space_used']) / 1073741824.0))
			space_used = float(int(accountInfo['space_used']))/1073741824
			percentage_used = str(round(float(accountInfo['limit_used']) * 100.0, 1))
			items = []
			items += [control.lang(40040) %  accountInfo['customer_id']]
			items += [control.lang(40041) % expires]
			items += [control.lang(40042) % days_remaining]
			items += [control.lang(40043) % points_used]
			items += [control.lang(40044) % space_used]
			items += [control.lang(40045) % percentage_used]
			return control.selectDialog(items, 'Premiumize')
		except:
			log_utils.error()
			pass
		return


	def get_media_url(self, host, media_id, cached_only=False):
		torrent = False
		cached = self.check_cache_item(media_id)
		media_id_lc = media_id.lower()
		if cached:
			log_utils.log('Premiumize.me: %s is readily available to stream' % media_id, __name__, log_utils.LOGDEBUG)
			if media_id_lc.endswith('.torrent') or media_id_lc.startswith('magnet:'):
				torrent = True
		elif media_id_lc.endswith('.torrent') or media_id_lc.startswith('magnet:'):
			if control.addon('script.module.resolveurl').getSetting('PremiumizeMeResolver_cached_only') or cached_only:
				raise Exception('Premiumize.me: Cached torrents only allowed to be initiated')
			torrent = True
			log_utils.log('Premiumize.me: initiating transfer to cloud for %s' % media_id, __name__, log_utils.LOGDEBUG)
			self.create_transfer(media_id)
		link = self.__direct_dl(media_id, torrent=torrent)
		if link:
			log_utils.log('Premiumize.me: Resolved to %s' % link, __name__, log_utils.LOGDEBUG)
			return link + self.append_headers(self.headers)
		raise ResolverError('Link Not Found')


	def append_headers(self, headers):
		return '|%s' % '&'.join(['%s=%s' % (key, quote_plus(headers[key])) for key in headers])


	def get_all_hosters(self):
		try:
			response = self._get(list_services_path)
			if not response:
				return None
			aliases = response.get('aliases', {})
			patterns = response.get('regexpatterns', {})

			tldlist = []
			for tlds in aliases.values():
				for tld in tlds:
					tldlist.append(tld)
			if self.get_setting('torrents') == 'true':
				tldlist.extend([u'torrent', u'magnet'])
			regex_list = []
			for regexes in patterns.values():
				for regex in regexes:
					try:
						regex_list.append(re.compile(regex))
					except:
						log_utils.log('Throwing out bad Premiumize regex: %s' % regex, __name__, log_utils.LOGDEBUG)
			log_utils.log('Premiumize.me patterns: %s regex: (%d) hosts: %s' % (patterns, len(regex_list), tldlist), __name__, log_utils.LOGDEBUG)
			return tldlist, regex_list
		except Exception as e:
			log_utils.log('Error getting Premiumize hosts: %s' % e, __name__, log_utils.LOGDEBUG)
		return [], []


	def valid_url(self, url, host):
		if url and self.get_setting('torrents') == 'true':
			url_lc = url.lower()
			if url_lc.endswith('.torrent') or url_lc.startswith('magnet:'):
				return True
		if not self.patterns or not self.hosts:
			self.hosts, self.patterns = self.get_all_hosters()
		if url:
			if not url.endswith('/'):
				url += '/'
			for pattern in self.patterns:
				if pattern.findall(url):
					return True
		elif host:
			if host.startswith('www.'):
				host = host.replace('www.', '')
			if any(host in item for item in self.hosts):
				return True
		return False


	def resolve_magnet_pack(self, media_id, season, episode, ep_title):
		from resources.lib.modules.source_utils import seas_ep_filter, episode_extras_filter
		try:
			file_url = None
			correct_files = []

			extensions = supported_video_extensions()
			extras_filtering_list = episode_extras_filter()

			data = {'src': media_id}
			response = self._post(transfer_directdl, data)
			if not 'status' in response or response['status'] != 'success':
				return None

			valid_results = [i for i in response.get('content')if any(i.get('path').lower().endswith(x) for x in extensions) and not i.get('link', '') == '']
			if len(valid_results) == 0:
				return

			for item in valid_results:
				if seas_ep_filter(season, episode, re.sub('[^A-Za-z0-9]+', '.', unquote(item['path'].split('/')[-1])).lower()):
					correct_files.append(item)
				if len(correct_files) == 0:
					continue

				episode_title = re.sub('[^A-Za-z0-9-]+', '.', ep_title.replace('\'', '')).lower()

				for i in correct_files:
					compare_link = re.sub('[^A-Za-z0-9-]+', '.', unquote(i['path'].replace("\'", ''))).lower()
					compare_link = seas_ep_filter(season, episode, compare_link, split=True)
					compare_link = re.sub(episode_title, '', compare_link)

					if not any(x in compare_link for x in extras_filtering_list):
						file_url = i['link']
						break

			if file_url:
				return self.add_headers_to_url(file_url)

		except Exception as e:
			log_utils.log('Error resolve_magnet_pack: %s' % str(e), __name__, log_utils.LOGDEBUG)
			return None


	def display_magnet_pack(self, magnet_url, info_hash):
		try:
			end_results = []
			extensions = supported_video_extensions()
			data = {'src': magnet_url}
			result = self._post(transfer_directdl, data=data)
			if not 'status' in result or result['status'] != 'success':
				return None
			for item in result.get('content'):
				if any(item.get('path').lower().endswith(x) for x in extensions) and not item.get('link', '') == '':
					try:
						path = item['path'].split('/')[-1]
					except:
						path = item['path']
					end_results.append({'link': item['link'], 'filename': path, 'size': float(item['size'])/1073741824})
			return end_results
		except Exception as e:
			log_utils.log('Error display_magnet_pack: %s' % str(e), __name__, log_utils.LOGDEBUG)
			return None


	def add_headers_to_url(self, url):
		return url + '|' + urlencode(self.headers)


	def check_cache_item(self, media_id):
		try:
			media_id = media_id.encode('ascii', errors='ignore').decode('ascii', errors='ignore')
			media_id = media_id.replace(' ', '')
			url = '%s?items[]=%s' % (cache_check, media_id)
			result = requests.get(url, headers=self.headers).json()
			if 'status' in result:
				if result.get('status') == 'success':
					response = result.get('response', False)
					if isinstance(response, list):
						return response[0]
				if result.get('status') == 'error':
					control.notification(title='default', message=result.get('message'), icon='default')
		except:
			log_utils.error()
			pass
		return False


	def check_cache_list(self, hashList):
		try:
			postData = {'items[]': hashList}
			response = requests.post(cache_check, data=postData, headers=self.headers, timeout=10).json()
			if 'status' in response:
				if response.get('status') == 'success':
					response = response.get('response', False)
					if isinstance(response, list):
						return response
		except:
			log_utils.error()
			pass
		return False


	def list_transfer(self):
		try:
			response = self._get(transfer_list)
			if not response:
				return None
			if response.get('status') == 'success':
				return response.get('transfers')
		except:
			log_utils.error()
			pass
		return None


	def id_transfer_status(self, transfer_id):
		try:
			response = self.list_transfer()
			if not response:
				return None
			for item in response:
				if item.get('id') == transfer_id:
					return item
		except:
			log_utils.error()
			pass
		return None


	def create_transfer(self, media_id, folder_id=0):
		try:
			data = {'src': media_id, 'folder_id': folder_id}
			response = self._post(transfer_create, data=data)
			if response:
				if response.get('status') == 'success':
					control.notification(title='default', message='Transfer successfully started to the Premiumize.me cloud', icon='default')
					percent_list = [25, 50, 75]
					while True:
						control.sleep(10*1000*60) # 10min
						item = self.id_transfer_status(response.get('id'))
						if item.get('status') ==  'running':
							for i in percent_list:
								if item.get('progress') * 100 >= i:
									percent_list.remove(i)
									control.notification(title='default', message='PM stransfer = ' + str(item.get('progress') * 100) + '% complete', icon='default')
						if item.get('status') ==  'seeding':
							control.notification(title='default', message='PM stransfer complete', icon='default')
							break
				# self.clear_finished_transfers() # PM issue with doing this
				return
			else:
				return
		except:
			log_utils.error()
			pass
		return


	def clear_finished_transfers(self):
		try:
			response = self._post(transfer_clear_finished)
			if not response:
				return
			if 'status' in response:
				if response.get('status') == 'success':
					log_utils.log('Finished transfers successfully cleared from the Premiumize.me cloud', __name__, log_utils.LOGDEBUG)
					control.execute('Container.Refresh')
					return
		except:
			log_utils.error()
			pass
		return


	def delete_transfer(self, media_id, folder_name=None):
		# log_utils.log('media_id = %s' % str(media_id), __name__, log_utils.LOGDEBUG)
		try:
			yes = control.yesnoDialog(control.lang(40050) % folder_name, '', '')
			if not yes:
				return
			data = {'id': media_id}
			response = self._post(transfer_delete, data)
			if not response:
				return
			if 'status' in response:
				if response.get('status') == 'success':
					log_utils.log('Transfer successfully deleted from the Premiumize.me cloud', __name__, log_utils.LOGDEBUG)
					control.execute('Container.Refresh')
					return
		except:
			log_utils.error()
			pass
		return


	def my_files(self, folder_id=None):
		try:
			if folder_id:
				url = folder_list + '?id=%s' % folder_id
			else:
				url = folder_list
			response = self._get(url)
			if response:
				return response.get('content')
		except:
			log_utils.error()
			pass
		return None


	def my_files_to_listItem(self, folder_id=None, folder_name=None):
		try:
			sysaddon = argv[0]
			syshandle = int(argv[1])
			extensions = supported_video_extensions()
			cloud_files = self.my_files(folder_id)
			if not cloud_files:
				control.notification(title='default', message='Empty Content', icon='default')
				return
			cloud_files = [i for i in cloud_files if ('link' in i and i['link'].lower().endswith(tuple(extensions))) or i['type'] == 'folder']
			cloud_files = sorted(cloud_files, key=lambda k: k['name'])
			cloud_files = sorted(cloud_files, key=lambda k: k['type'], reverse=True)
		except:
			log_utils.error()
			return
		folder_str, file_str, downloadMenu, renameMenu, deleteMenu = control.lang(40046).upper(), control.lang(40047).upper(), control.lang(40048), control.lang(40049), control.lang(40050)
		for count, item in enumerate(cloud_files, 1):
			try:
				cm = []
				type = item['type']
				name = item['name']
				# name = control.strip_non_ascii_and_unprintable(item['name']) #keep an eye out if this is needed
				if type == 'folder':
					isFolder = True
					size = 0
					label = '%02d | [B]%s[/B] | [I]%s [/I]' % (count, folder_str, name)
					url = '%s?action=pmMyFiles&id=%s&name=%s' % (sysaddon, item['id'], quote_plus(name))
				else:
					isFolder = False
					url_link = item['link']
					if url_link.startswith('/'):
						url_link = 'https' + url_link
					size = item['size']
					display_size = float(int(size))/1073741824
					label = '%02d | [B]%s[/B] | %.2f GB | [I]%s [/I]' % (count, file_str, display_size, name)
					url = '%s?action=playURL&url=%s' % (sysaddon, url_link)
					cm.append((downloadMenu, 'RunPlugin(%s?action=download&name=%s&image=%s&url=%s&caller=premiumize)' %
								(sysaddon, quote_plus(name), quote_plus(pm_icon), url_link)))
				cm.append((renameMenu % type.capitalize(), 'RunPlugin(%s?action=pmRename&type=%s&id=%s&name=%s)' %
								(sysaddon, type, item['id'], quote_plus(name))))
				cm.append((deleteMenu % type.capitalize(), 'RunPlugin(%s?action=pmDelete&type=%s&id=%s&name=%s)' %
								(sysaddon, type, item['id'], quote_plus(name))))

				item = control.item(label=label)
				item.addContextMenuItems(cm)
				item.setArt({'icon': pm_icon, 'poster': pm_icon, 'thumb': pm_icon, 'fanart': addonFanart, 'banner': pm_icon})
				item.setInfo(type='video', infoLabels='')
				video_streaminfo = {'codec': 'h264'}
				item.addStreamInfo('video', video_streaminfo)
				control.addItem(handle=syshandle, url=url, listitem=item, isFolder=isFolder)
			except:
				log_utils.error()
				pass
		control.content(syshandle, 'files')
		control.directory(syshandle, cacheToDisc=True)


	def user_transfers(self):
		try:
			response = self._get(transfer_list)
			if response:
				return response.get('transfers')
		except:
			log_utils.error()
			pass
		return None


	def user_transfers_to_listItem(self):
		try:
			sysaddon = argv[0]
			syshandle = int(argv[1])
			extensions = supported_video_extensions()
			transfer_files = self.user_transfers()
			if not transfer_files:
				control.notification(title='default', message='Empty Content', icon='default')
				return
		except:
			log_utils.error()
			return
		folder_str, file_str, downloadMenu, renameMenu, deleteMenu, clearFinishedMenu = control.lang(40046).upper(),\
			control.lang(40047).upper(), control.lang(40048), control.lang(40049), control.lang(40050), control.lang(40051)
		for count, item in enumerate(transfer_files, 1):
			try:
				cm = []
				type = 'folder' if item['file_id'] is None else 'file'
				name = item['name']
				# name = control.strip_non_ascii_and_unprintable(item['name']) #keep an eye out if this is needed
				status = item['status']
				progress = item['progress']
				if status == 'finished':
					progress = 100
				else:
					try:
						progress = re.findall(r'(?:\d{0,1}\.{0,1})(\d+)', str(progress))[0][:2]
					except:
						progress = 'UNKNOWN'
				if type == 'folder':
					isFolder = True if status == 'finished' else False
					status_str = '[COLOR %s]%s[/COLOR]' % (control.getColor(control.setting('highlight.color')), status.capitalize())
					label = '%02d | [B]%s[/B] - %s | [B]%s[/B] | [I]%s [/I]' % (count, status_str, str(progress) + '%', folder_str, name)
					url = '%s?action=pmMyFiles&id=%s&name=%s' % (sysaddon, item['folder_id'], quote_plus(name))

# Till PM addresses issue with item also being removed from public acess if item not accessed for 60 days this option is disabled.
					# cm.append((clearFinishedMenu, 'RunPlugin(%s?action=pmClearFinishedTransfers)' % sysaddon))
					if status != 'finished':
						cm.append((deleteMenu % 'Transfer', 'RunPlugin(%s?action=pmDeleteTransfer&id=%s&name=%s)' %
								(sysaddon, item['id'], quote_plus(name))))
				else:
					isFolder = False
					details = self.item_details(item['file_id'])
					if not details:
						control.notification(title='default', message='Empty Content', icon='default')
						return

					url_link = details['link']
					if url_link.startswith('/'):
						url_link = 'https' + url_link
					size = details['size']
					display_size = float(int(size))/1073741824
					label = '%02d | %s%% | [B]%s[/B] | %.2f GB | [I]%s [/I]' % (count, str(progress), file_str, display_size, name)
					url = '%s?action=playURL&url=%s' % (sysaddon, url_link)
					cm.append((downloadMenu, 'RunPlugin(%s?action=download&name=%s&image=%s&url=%s&caller=premiumize)' %
								(sysaddon, quote_plus(name), quote_plus(pm_icon), url_link)))

				item = control.item(label=label)
				item.addContextMenuItems(cm)
				item.setArt({'icon': pm_icon, 'poster': pm_icon, 'thumb': pm_icon, 'fanart': addonFanart, 'banner': pm_icon})
				item.setInfo(type='video', infoLabels='')
				video_streaminfo = {'codec': 'h264'}
				item.addStreamInfo('video', video_streaminfo)
				control.addItem(handle=syshandle, url=url, listitem=item, isFolder=isFolder)
			except:
				log_utils.error()
				pass
		control.content(syshandle, 'files')
		control.directory(syshandle, cacheToDisc=True)



	def item_details(self, item_id):
		try:
			data = {'id': item_id}
			itemDetails = self._post(item_details, data)
			return itemDetails
		except:
			log_utils.error()
			pass
		return None


	def rename(self, type, folder_id=None, folder_name=None):
		try:
			if type == 'folder':
				url = folder_rename
				t = control.lang(40049) % type
			else:
				yes = control.yesnoDialog(control.lang(40049) % folder_name + ': [B](YOU MUST ENTER MATCHING FILE EXT.)[/B]', '', '')
				if not yes:
					return
				url = item_rename
				t = control.lang(40049) % type + ': [B](YOU MUST ENTER MATCHING FILE EXT.)[/B]'
			k = control.keyboard('', t)
			k.doModal()
			q = k.getText() if k.isConfirmed() else None
			if not q:
				return
			data = {'id': folder_id, 'name': q}
			response = self._post(url, data=data)
			if not response:
				return
			if 'status' in response:
				if response.get('status') == 'success':
					control.execute('Container.Refresh')
		except:
			log_utils.error()
			pass


	def delete(self, type, folder_id=None, folder_name=None):
		try:
			if type == 'folder':
				url = folder_delete
			else:
				url = item_delete
			yes = control.yesnoDialog(control.lang(40050) % folder_name, '', '')
			if not yes:
				return
			data = {'id': folder_id}
			response = self._post(url, data=data)
			if not response:
				return
			if 'status' in response:
				if response.get('status') == 'success':
					control.execute('Container.Refresh')
		except:
			log_utils.error()
			pass
