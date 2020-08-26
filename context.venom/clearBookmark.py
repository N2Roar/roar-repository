import sys
import xbmc

try:
	from urlparse import parse_qsl
	from urllib import quote_plus
except:
	from urllib.parse import parse_qsl
	from urllib.parse import quote_plus

if __name__ == '__main__':
	item = sys.listitem
	path = item.getPath()
	# xbmc.log('path = %s' % path, 2)
	plugin = 'plugin://plugin.video.venom/'
	args = path.split(plugin, 1)
	params = dict(parse_qsl(args[1].replace('?', '')))

	year = params.get('year')
	name = params.get('title') + ' (%s)' % year

	if 'tvshowtitle' in params:
		season = params.get('season', '')
		episode = params.get('episode', '')
		name = params.get('tvshowtitle') + ' S%02dE%02d' % (int(season), int(episode))
	sysname = quote_plus(name)

	venom_path = 'RunPlugin(%s?action=clearBookmark&name=%s&year=%s&opensettings=false)' % (plugin, sysname, year)
	xbmc.executebuiltin(venom_path)

	path = path.split('&meta=')[0]
	kodi_path = 'RunPlugin(%s?action=clearLocalBookmark&url=%s)' % (plugin, quote_plus(path))
	xbmc.executebuiltin(kodi_path)

	xbmc.executebuiltin('UpdateLibrary(video,special://skin/foo)')