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
	# message = item.getLabel()
	path = item.getPath()
	# xbmc.log('path = %s' % path, 2)
	plugin = 'plugin://plugin.video.venom/'
	args = path.split(plugin, 1)
	params = dict(parse_qsl(args[1].replace('?', '')))
	name = params['tvshowtitle'] if 'tvshowtitle' in params else params['title']
	sysname = quote_plus(name)

	imdb = params.get('imdb', '')
	tvdb = params.get('tvdb', '')
	season = params.get('season', '')
	episode = params.get('episode', '')

	path = 'RunPlugin(%s?action=traktManager&name=%s&imdb=%s&tvdb=%s&season=%s&episode=%s)' % (
				plugin, sysname, imdb, tvdb, season, episode)
	xbmc.executebuiltin(path)