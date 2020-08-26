# -*- coding: utf-8 -*-

'''
	Venom Add-on
'''

import json
import re
import requests
from sys import argv

try:
	from urllib import quote_plus, unquote
except:
	from urllib.parse import quote_plus, unquote

from resources.lib.modules import cleantitle
from resources.lib.modules import control
from resources.lib.modules import log_utils
from resources.lib.modules import workers
from resources.lib.modules.source_utils import supported_video_extensions

FormatDateTime = "%Y-%m-%dT%H:%M:%S.%fZ"
rest_base_url = 'https://api.real-debrid.com/rest/1.0/'
oauth_base_url = 'https://api.real-debrid.com/oauth/v2/'
unrestrict_link_url = 'unrestrict/link'
device_code_url = 'device/code?%s'
credentials_url = 'device/credentials?%s'
downloads_delete_url = 'downloads/delete'
add_magnet_url = 'torrents/addMagnet'
torrents_info_url = 'torrents/info'
select_files_url = 'torrents/selectFiles'
torrents_delete_url = 'torrents/delete'
check_cache_url = 'torrents/instantAvailability'
hosts_regex_url = 'hosts/regex'
hosts_domains_url = 'hosts/domains'
rd_icon = control.joinPath(control.artPath(), 'realdebrid.png')
addonFanart = control.addonFanart()


class RealDebrid:
	def __init__(self):
		self.hosters = None
		self.hosts = None
		self.cache_check_results = {}
		self.token = control.addon('script.module.resolveurl').getSetting('RealDebridResolver_token')
		self.headers = {'Authorization': 'Bearer %s' % self.token}
		self.client_ID = control.addon('script.module.resolveurl').getSetting('RealDebridResolver_client_id')
		if self.client_ID == '':
			self.client_ID = 'X245A4XAIBGVM'
		self.secret = control.addon('script.module.resolveurl').getSetting('RealDebridResolver_client_secret')
		self.device_code = ''
		self.auth_timeout = 0
		self.auth_step = 0


	def get_url(self, url, fail_check=False, token_ck=False):
		try:
			original_url = url
			url = rest_base_url + url
			if self.token == '':
				log_utils.log('No Real Debrid Token Found', __name__, log_utils.LOGDEBUG)
				return None
			# if not fail_check: # with fail_check=True new token does not get added
			if '?' not in url:
				url += "?auth_token=%s" % self.token
			else:
				url += "&auth_token=%s" % self.token

			response = requests.get(url, timeout=15).json()
			if 'bad_token' in str(response) or 'Bad Request' in str(response):
				if not fail_check:
					if self.refresh_token() and token_ck:
						return
					response = self.get_url(original_url, fail_check=True)
			return response
		except:
			log_utils.error()
			pass
		return None


	def post_url(self, url, data):
		try:
			original_url = url
			url = rest_base_url + url
			if self.token == '':
				log_utils.log('No Real Debrid Token Found', __name__, log_utils.LOGDEBUG)
				return None
			if '?' not in url:
				url += "?auth_token=%s" % self.token
			else:
				url += "&auth_token=%s" % self.token

			# msg : JSONDecodeError -> Expecting value: line 1 column 1 (char 0) check for this error
			response = requests.post(url, data=data, timeout=15).json()
			if 'bad_token' in str(response) or 'Bad Request' in str(response):
				self.refresh_token()
				response = self.post_url(original_url, data)
			return response
		except:
			log_utils.error()
			pass
		return None


	def auth_loop(self):
		control.sleep(self.auth_step*1000)
		url = 'client_id=%s&code=%s' % (self.client_ID, self.device_code)
		url = oauth_base_url + credentials_url % url
		response = json.loads(requests.get(url).text)
		if 'error' in response:
			return
		else:
			try:
				control.progressDialog.close()
				self.client_ID = response['client_id']
				self.secret = response['client_secret']
			except:
				log_utils.error()
				control.okDialog(title='default', message=control.lang(40053))
			return


	def auth(self):
		self.secret = ''
		self.client_ID = 'X245A4XAIBGVM'
		url = 'client_id=%s&new_credentials=yes' % self.client_ID
		url = oauth_base_url + device_code_url % url
		response = json.loads(requests.get(url).text)
		control.progressDialog.create(control.lang(40055))
		control.progressDialog.update(-1,
				control.lang(32513) % 'https://real-debrid.com/device',
				control.lang(32514) % response['user_code'])

		self.auth_timeout = int(response['expires_in'])
		self.auth_step = int(response['interval'])
		self.device_code = response['device_code']

		while self.secret == '':
			if control.progressDialog.iscanceled():
				control.progressDialog.close()
				break
			self.auth_loop()
		if self.secret:
			self.get_token()


	def user_info(self):
		return self.get_url('user')


	def user_info_to_dialog(self):
		from datetime import datetime
		import time
		try:
			userInfo = self.user_info()
			try:
				expires = datetime.strptime(userInfo['expiration'], FormatDateTime)
			except:
				expires = datetime(*(time.strptime(userInfo['expiration'], FormatDateTime)[0:6]))
			days_remaining = (expires - datetime.today()).days
			expires = expires.strftime('%Y-%m-%d')
			items = []
			items += [control.lang(40035) % userInfo['email']]
			items += [control.lang(40036) % userInfo['username']]
			items += [control.lang(40037) % userInfo['type'].capitalize()]
			items += [control.lang(40041) % expires]
			items += [control.lang(40042) % days_remaining]
			items += [control.lang(40038) % userInfo['points']]
			return control.selectDialog(items, 'Real-Debrid')
		except:
			log_utils.error()
			pass
		return


	def user_torrents(self):
		try:
			url = 'torrents'
			return self.get_url(url)
		except:
			log_utils.error()
			pass


	def user_torrents_to_listItem(self):
		try:
			sysaddon = argv[0]
			syshandle = int(argv[1])
			torrent_files = self.user_torrents()
			# log_utils.log('torrent_files = %s' %  str(torrent_files), __name__, log_utils.LOGDEBUG)
			if not torrent_files:
				return
			# torrent_files = [i for i in torrent_files if i['status'] == 'downloaded']
			folder_str, deleteMenu = control.lang(40046).upper(), control.lang(40050)

			for count, item in enumerate(torrent_files, 1):
				try:
					cm = []
					isFolder = True if item['status'] == 'downloaded' else False

					status = '[COLOR %s]%s[/COLOR]' % (control.getColor(control.setting('highlight.color')), item['status'].capitalize())
					folder_name = cleantitle.normalize(item['filename'])
					label = '%02d | [B]%s[/B] - %s | [B]%s[/B] | [I]%s [/I]' % (count, status, str(item['progress']) + '%', folder_str, folder_name)

					url = '%s?action=rdBrowseUserTorrents&id=%s' % (sysaddon, item['id']) if isFolder else None

					cm.append((deleteMenu % 'Torrent', 'RunPlugin(%s?action=rdDeleteUserTorrent&id=%s&name=%s)' %
							(sysaddon, item['id'], quote_plus(folder_name))))
					item = control.item(label=label)
					item.addContextMenuItems(cm)
					item.setArt({'icon': rd_icon, 'poster': rd_icon, 'thumb': rd_icon, 'fanart': addonFanart, 'banner': rd_icon})
					item.setInfo(type='video', infoLabels='')
					control.addItem(handle=syshandle, url=url, listitem=item, isFolder=isFolder)
				except:
					log_utils.error()
					pass
			control.content(syshandle, 'files')
			control.directory(syshandle, cacheToDisc=True)
		except:
			log_utils.error()
			pass


	def browse_user_torrents(self, folder_id):
		try:
			sysaddon = argv[0]
			syshandle = int(argv[1])
			torrent_files = self.torrent_info(folder_id)
		except:
			return
		extensions = supported_video_extensions()
		try:
			file_info = [i for i in torrent_files['files'] if i['path'].lower().endswith(tuple(extensions))]
			file_urls = torrent_files['links']
			for c, i in enumerate(file_info):
				try:
					i.update({'url_link': file_urls[c]})
				except:
					pass
			pack_info = sorted(file_info, key=lambda k: k['path'])
		except:
			return control.notification(title='default', message=33586, icon='default')

		file_str, downloadMenu, renameMenu, deleteMenu, clearFinishedMenu = \
				control.lang(40047).upper(), control.lang(40048), control.lang(40049), control.lang(40050), control.lang(40051)

		for count, item in enumerate(pack_info, 1):
			try:
				cm = []
				name = item['path']
				if name.startswith('/'):
					name = name.split('/')[-1]

				url_link = item['url_link']
				if url_link.startswith('/'):
					url_link = 'http' + url_link

				size = float(int(item['bytes']))/1073741824
				label = '%02d | [B]%s[/B] | %.2f GB | [I]%s [/I]' % (count, file_str, size, name)

				url = '%s?action=playURL&url=%s&caller=realdebrid&type=unrestrict' % (sysaddon, url_link)

				cm.append((downloadMenu, 'RunPlugin(%s?action=download&name=%s&image=%s&url=%s&caller=realdebrid&type=unrestrict)' %
							(sysaddon, quote_plus(name), quote_plus(rd_icon), url_link)))
				cm.append((deleteMenu % 'Torrent', 'RunPlugin(%s?action=rdDeleteUserTorrent&id=%s&name=%s)' %
							(sysaddon, item['id'], quote_plus(name))))

				item = control.item(label=label)
				item.addContextMenuItems(cm)
				item.setArt({'icon': rd_icon, 'poster': rd_icon, 'thumb': rd_icon, 'fanart': addonFanart, 'banner': rd_icon})
				item.setInfo(type='video', infoLabels='')
				video_streaminfo = {'codec': 'h264'}
				item.addStreamInfo('video', video_streaminfo)
				control.addItem(handle=syshandle, url=url, listitem=item, isFolder=False)
			except:
				log_utils.error()
				pass
		control.content(syshandle, 'files')
		control.directory(syshandle, cacheToDisc=True)


	def delete_user_torrent(self, media_id, name):
		try:
			yes = control.yesnoDialog(control.lang(40050) % name, '', '')
			if not yes:
				return
			url = torrents_delete_url + "/%s&auth_token=%s" % (media_id, self.token)
			response = requests.delete(rest_base_url + url).text
			if not 'error' in response:
				log_utils.log('Real-Debrid: %s was removed from your active Torrents' % name, __name__, log_utils.LOGDEBUG)
				control.execute('Container.Refresh')
				return
		except Exception as e:
			log_utils.log('Real-Debrid Error: DELETE TORRENT %s | %s' % (name, e), __name__, log_utils.LOGDEBUG)
			raise


	def downloads(self, page):
		import math
		try:
			# Need to check token, and refresh if needed
			ck_token = self.get_url('user', token_ck=True)
			url = 'downloads?page=%s&auth_token=%s' % (page, self.token)
			response = requests.get(rest_base_url + url)
			total_count = float(response.headers['X-Total-Count'])
			pages = int(math.ceil(total_count / 50.0))
			return json.loads(response.text), pages
		except:
			log_utils.error()
			pass


	def my_downloads_to_listItem(self, page):
		try:
			from datetime import datetime
			sysaddon = argv[0]
			syshandle = int(argv[1])
			my_downloads, pages = self.downloads(page)
		except:
			my_downloads = None

		if not my_downloads:
			return
		extensions = supported_video_extensions()
		my_downloads = [i for i in my_downloads if i['download'].lower().endswith(tuple(extensions))]
		downloadMenu, deleteMenu = control.lang(40048), control.lang(40050)

		for count, item in enumerate(my_downloads, 1):
			if page > 1:
				count += (page-1)*50
			try:
				cm = []
				generated = datetime.strptime(item['generated'], FormatDateTime)
				generated = generated.strftime('%Y-%m-%d')
				name = control.strip_non_ascii_and_unprintable(item['filename'])

				size = float(int(item['filesize']))/1073741824
				label = '%02d | %.2f GB | %s  | [I]%s [/I]' % (count, size, generated, name)

				url_link = item['download']
				url = '%s?action=playURL&url=%s' % (sysaddon, url_link)
				cm.append((downloadMenu, 'RunPlugin(%s?action=download&name=%s&image=%s&url=%s&caller=realdebrid)' %
								(sysaddon, quote_plus(name), quote_plus(rd_icon), url_link)))

				cm.append((deleteMenu % 'File', 'RunPlugin(%s?action=rdDeleteDownload&id=%s&name=%s)' %
								(sysaddon, item['id'], name)))

				item = control.item(label=label)
				item.addContextMenuItems(cm)
				item.setArt({'icon': rd_icon, 'poster': rd_icon, 'thumb': rd_icon, 'fanart': addonFanart, 'banner': rd_icon})
				item.setInfo(type='video', infoLabels='')
				video_streaminfo = {'codec': 'h264'}
				item.addStreamInfo('video', video_streaminfo)
				control.addItem(handle=syshandle, url=url, listitem=item, isFolder=False)
			except:
				log_utils.error()
				pass

		if page < pages:
			page += 1
			next = True
		else:
			next = False

		if next:
			try:
				nextMenu = control.lang(32053)
				url = '%s?action=rdMyDownloads&query=%s' % (sysaddon, page)
				page = '  [I](%s)[/I]' % page
				nextMenu = '[COLOR skyblue]' + nextMenu + page + '[/COLOR]'
				item = control.item(label=nextMenu)
				icon = control.addonNext()
				item.setArt({'icon': rd_icon, 'poster': rd_icon, 'thumb': rd_icon, 'fanart': addonFanart, 'banner': rd_icon})
				control.addItem(handle=syshandle, url=url, listitem=item, isFolder=True)
			except:
				log_utils.error()
				pass
		control.content(syshandle, 'files')
		control.directory(syshandle, cacheToDisc=True)


	def delete_download(self, media_id, name):
		try:
			yes = control.yesnoDialog(control.lang(40050) % name, '', '')
			if not yes:
				return
			# Need to check token, and refresh if needed
			ck_token = self.get_url('user', token_ck=True)
			url = downloads_delete_url + "/%s&auth_token=%s" % (media_id, self.token)
			response = requests.delete(rest_base_url + url).text
			if not 'error' in response:
				log_utils.log('Real-Debrid: %s was removed from your MyDownloads' % name, __name__, log_utils.LOGDEBUG)
				control.execute('Container.Refresh')
				return
		except Exception as e:
			log_utils.log('Real-Debrid Error: DELETE DOWNLOAD %s | %s' % (name, e), __name__, log_utils.LOGDEBUG)


	def check_cache_list(self, hashList):
		if isinstance(hashList, list):
			hashList = [hashList[x:x+100] for x in range(0, len(hashList), 100)]
			# Need to check token, and refresh if needed, before blasting threads at it
			ck_token = self.get_url('user', token_ck=True)

			threads = []
			for section in hashList:
				threads.append(workers.Thread(self.check_hash_thread, section))
			[i.start() for i in threads]
			[i.join() for i in threads]

			return self.cache_check_results
		else:
			hashString = "/" + hashList
			return self.get_url("torrents/instantAvailability" + hashString)


	def check_hash_thread(self, hashes):
		try:
			hashString = '/' + '/'.join(hashes)
			response = self.get_url("torrents/instantAvailability" + hashString)
			self.cache_check_results.update(response)
		except:
			log_utils.error()
			pass


	def resolve_magnet_pack(self, media_id, info_hash, season, episode, ep_title):
		from resources.lib.modules.source_utils import seas_ep_filter, episode_extras_filter
		try:
			info_hash = info_hash.lower()
			torrent_id = None
			rd_url = None
			match = False

			extensions = supported_video_extensions()
			extras_filtering_list = episode_extras_filter()

			info_hash = info_hash.lower()

			torrent_files = self.get_url(check_cache_url + '/' + info_hash)
			if not info_hash in torrent_files:
				return None

			torrent_id = self.create_transfer(media_id)
			torrent_files = torrent_files[info_hash]['rd']

			for item in torrent_files:
				video_only = self.video_only(item, extensions)
				if not video_only:
					continue

				correct_file_check = False
				item_values = [i['filename'] for i in item.values()]
				for value in item_values:
					correct_file_check = seas_ep_filter(season, episode, re.sub('[^A-Za-z0-9]+', '.', unquote(value)).lower())
					if correct_file_check:
						break

				if not correct_file_check:
					continue

				torrent_keys = item.keys()
				if len(torrent_keys) == 0:
					continue

				torrent_keys = ','.join(torrent_keys)
				self.select_file(torrent_id, torrent_keys)

				torrent_info = self.torrent_info(torrent_id)

				selected_files = [(idx, i) for idx, i in enumerate([i for i in torrent_info['files'] if i['selected'] == 1])]

				correct_files = []
				correct_file_check = False

				for value in selected_files:
					checker = re.sub('[^A-Za-z0-9]+', '.', unquote(value[1]['path'])).lower()
					correct_file_check = seas_ep_filter(season, episode, checker)
					if correct_file_check:
						correct_files.append(value[1])
						break

				if len(correct_files) == 0:
					continue

				episode_title = re.sub('[^A-Za-z0-9-]+', '.', ep_title.replace("\'", '')).lower()

				for i in correct_files:
					compare_link = re.sub('[^A-Za-z0-9-]+', '.', unquote(i['path'].replace("\'", ''))).lower()
					compare_link = seas_ep_filter(season, episode, compare_link, split=True)
					compare_link = re.sub(episode_title, '', compare_link)

					if any(x in compare_link for x in extras_filtering_list):
						continue
					else:
						match = True
						break

				if match:
					index = [i[0] for i in selected_files if i[1]['path'] == correct_files[0]['path']][0]

				rd_link = torrent_info['links'][index]
				rd_url = self.unrestrict_link(rd_link)

				# should we be deleting torrents?  isn't this our cloud account?
				self.delete_torrent(torrent_id)

				return rd_url

			self.delete_torrent(torrent_id)
		except Exception as e:
			if torrent_id: self.delete_torrent(torrent_id)
			log_utils.log('Real-Debrid Error: RESOLVE MAGNET PACK | %s' % e, __name__, log_utils.LOGDEBUG)
			raise


	def display_magnet_pack(self, magnet_url, info_hash):
		try:
			torrent_id = None
			rd_url = None
			match = False
			video_only_items = []
			list_file_items = []
			info_hash = info_hash.lower()
			extensions = supported_video_extensions()

			torrent_files = self.get_url(check_cache_url + '/' + info_hash)
			if not info_hash in torrent_files:
				return None

			torrent_id = self.create_transfer(magnet_url)

			if not torrent_id:
				return None

			torrent_files = torrent_files[info_hash]['rd']
			for item in torrent_files:
				video_only = self.video_only(item, extensions)
				if not video_only: continue

				torrent_keys = item.keys()
				if len(torrent_keys) == 0: continue

				video_only_items.append(torrent_keys)

			video_only_items = max(video_only_items, key=len)

			torrent_keys = ','.join(video_only_items)

			self.select_file(torrent_id, torrent_keys)

			torrent_info = self.torrent_info(torrent_id)

			list_file_items = [dict(i, **{'link':torrent_info['links'][idx]})  for idx, i in enumerate([i for i in torrent_info['files'] if i['selected'] == 1])]
			list_file_items = [{'link': i['link'], 'filename': i['path'].replace('/', ''), 'size': float(i['bytes'])/1073741824} for i in list_file_items]

			self.delete_torrent(torrent_id)

			return list_file_items
		except Exception as e:
			if torrent_id: self.delete_torrent(torrent_id)
			log_utils.log('Real-Debrid Error: DISPLAY MAGNET PACK | %s' % str(e), __name__, log_utils.LOGDEBUG)
			raise


	def torrent_info(self, torrent_id):
		try:
			url = torrents_info_url + "/%s" % torrent_id
			return self.get_url(url)
		except Exception as e:
			log_utils.log('Real-Debrid Error: TORRENT INFO | %s' % e, __name__, log_utils.LOGDEBUG)
			raise


	def create_transfer(self, media_id):
		try:
			data = {'magnet': media_id}
			js_result = self.post_url(add_magnet_url, data)
			log_utils.log('Real-Debrid: Sending MAGNET URL %s to the real-debrid cloud' % media_id, __name__, log_utils.LOGDEBUG)
			return js_result.get('id', "")
		except Exception as e:
			log_utils.log('Real-Debrid Error: ADD MAGNET | %s' % e, __name__, log_utils.LOGDEBUG)
			raise


	def select_file(self, torrent_id, file_id):
		try:
			url = '%s/%s' % (select_files_url, torrent_id)
			data = {'files': file_id}
			self.post_url(url, data)
			log_utils.log('Real-Debrid: Selected file ID %s from Torrent ID %s to transfer' % (file_id, torrent_id), __name__, log_utils.LOGDEBUG)
			return True
		except Exception as e:
			log_utils.log('Real-Debrid Error: SELECT FILE | %s' % e, __name__, log_utils.LOGDEBUG)
			return False


	def unrestrict_link(self, link):
		post_data = {'link': link}
		response = self.post_url(unrestrict_link_url, post_data)
		try:
			return response['download']
		except:
			return None


	def delete_torrent(self, torrent_id):
		try:
			# Need to check token, and refresh if needed
			ck_token = self.get_url('user', token_ck=True)
			url = torrents_delete_url + "/%s&auth_token=%s" % (torrent_id, self.token)
			response = requests.delete(rest_base_url + url)
			log_utils.log('Real-Debrid: Torrent ID %s was removed from your active torrents' % torrent_id, __name__, log_utils.LOGDEBUG)
			return True
		except Exception as e:
			log_utils.log('Real-Debrid Error: DELETE TORRENT | %s' % e, __name__, log_utils.LOGDEBUG)
			raise


	def add_torrent_select(self, torrent_id, file_ids):
		self.clear_cache()
		url = "torrents/selectFiles/%s" % torrent_id
		post_data = {'files': file_ids}
		return self.post_url(url, post_data)


# video_files = []
# all_files = torrent_info['files']
# for item in all_files:
	# if any(item['path'].lower().endswith(x) for x in extensions):
		# video_files.append(item)
# torrent_keys = [str(i['id']) for i in video_files]
# torrent_keys = ','.join(torrent_keys)
# self.add_torrent_select(torrent_id, torrent_keys)



	def get_link(self, link):
		if 'download' in link:
			if 'quality' in link:
				label = '[%s] %s' % (link['quality'], link['download'])
			else:
				label = link['download']
			return label, link['download']


	def video_only(self, storage_variant, extensions):
		return False if len([i for i in storage_variant.values() if not i['filename'].lower().endswith(tuple(extensions))]) > 0 else True


	def refresh_token(self):
		try:
			self.client_ID = control.addon('script.module.resolveurl').getSetting('RealDebridResolver_client_id')
			self.secret = control.addon('script.module.resolveurl').getSetting('RealDebridResolver_client_secret')
			self.device_code = control.addon('script.module.resolveurl').getSetting('RealDebridResolver_refresh')
			log_utils.log('Refreshing Expired Real Debrid Token: |%s|%s|' % (self.client_ID, self.device_code), __name__, log_utils.LOGDEBUG)
			if not self.get_token():
				# empty all auth settings to force a re-auth on next use
				self.reset_authorization()
				log_utils.log('Unable to Refresh Real Debrid Token', __name__, log_utils.LOGDEBUG)
			else:
				log_utils.log('Real Debrid Token Successfully Refreshed', __name__, log_utils.LOGDEBUG)
				return True
		except:
			return False


	def get_token(self):
		try:
			url = oauth_base_url + 'token'
			postData = {'client_id': self.client_ID, 'client_secret': self.secret, 'code': self.device_code, 'grant_type': 'http://oauth.net/grant_type/device/1.0'}
			response = requests.post(url, data=postData).json()
			# log_utils.log('Authorizing Real Debrid Result: |%s|' % response, __name__, log_utils.LOGDEBUG)
			self.token = response['access_token']
			control.addon('script.module.resolveurl').setSetting('RealDebridResolver_client_id', self.client_ID)
			control.addon('script.module.resolveurl').setSetting('RealDebridResolver_client_secret', self.secret,)
			control.addon('script.module.resolveurl').setSetting('RealDebridResolver_token', self.token)
			control.addon('script.module.resolveurl').setSetting('RealDebridResolver_refresh', response['refresh_token'])
			return True
		except Exception as e:
			log_utils.log('Real Debrid Authorization Failed: %s' % e, __name__, log_utils.LOGDEBUG)
			return False


	def reset_authorization(self):
		control.addon('script.module.resolveurl').setSetting('RealDebridResolver_client_id', '')
		control.addon('script.module.resolveurl').setSetting('RealDebridResolver_client_secret', '')
		control.addon('script.module.resolveurl').setSetting('RealDebridResolver_token', '')
		control.addon('script.module.resolveurl').setSetting('RealDebridResolver_refresh', '')