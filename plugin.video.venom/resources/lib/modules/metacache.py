# -*- coding: utf-8 -*-

import time, xbmc
from resources.lib.modules import control

try:
	from sqlite3 import dbapi2 as database
except:
	from pysqlite2 import dbapi2 as database


def fetch(items, lang = 'en', user=''):
	try:
		t2 = int(time.time())

		if not control.existsPath(control.dataPath):
			control.makeFile(control.dataPath)

		dbcon = database.connect(control.metacacheFile)
		dbcur = dbcon.cursor()
		dbcur.execute("CREATE TABLE IF NOT EXISTS meta (""imdb TEXT, ""tmdb TEXT, ""tvdb TEXT, ""lang TEXT, ""user TEXT, ""item TEXT, ""time TEXT, ""UNIQUE(imdb, tmdb, tvdb, lang, user)"");")
		dbcur.connection.commit()
	except:
		return items

	for i in range(0, len(items)):
		try:
			dbcur.execute("SELECT * FROM meta WHERE (imdb = '%s' and lang = '%s' and user = '%s' and not imdb = '0') or (tmdb = '%s' and lang = '%s' and user = '%s' and not tmdb = '0') or (tvdb = '%s' and lang = '%s' and user = '%s' and not tvdb = '0')" % (items[i]['imdb'], lang, user, items[i]['tmdb'], lang, user, items[i]['tvdb'], lang, user))
			match = dbcur.fetchone()
			if match is not None:
				t1 = int(match[6])
				update = (abs(t2 - t1) / 3600) >= 720

				if update is True:
					raise Exception()

				item = eval(match[5].encode('utf-8'))
				item = dict((k, v) for k, v in item.iteritems() if v != '0')
				items[i].update(item)
				items[i].update({'metacache': True})
		except:
			import traceback
			traceback.print_exc()
			pass

	dbcon.close()
	return items


def insert(meta):
	try:
		control.makeFile(control.dataPath)
		dbcon = database.connect(control.metacacheFile)
		dbcur = dbcon.cursor()
		dbcur.execute("CREATE TABLE IF NOT EXISTS meta (""imdb TEXT, ""tmdb TEXT, ""tvdb TEXT, ""lang TEXT, ""user TEXT, ""item TEXT, ""time TEXT, ""UNIQUE(imdb, tmdb, tvdb, lang, user)"");")
		t = int(time.time())

		for m in meta:
			if "user" not in m:
				m["user"] = ''
			if "lang" not in m:
				m["lang"] = 'en'
			i = repr(m['item'])

			dbcur.execute("DELETE FROM meta WHERE (imdb = '%s' and lang = '%s' and user = '%s' and not imdb = '0') or (tmdb = '%s' and lang = '%s' and user = '%s' and not tmdb = '0') or (tvdb = '%s' and lang = '%s' and user = '%s' and not tvdb = '0')" % (m['imdb'], m['lang'], m['user'], m['tmdb'], m['lang'], m['user'], m['tvdb'], m['lang'], m['user']))
			dbcur.execute("INSERT INTO meta Values (?, ?, ?, ?, ?, ?, ?)", (m['imdb'], m['tmdb'], m['tvdb'], m['lang'], m['user'], i, t))

		dbcur.connection.commit()
		dbcon.close()
	except:
		dbcon.close()
		import traceback
		traceback.print_exc()
		return


def local(items, link, poster, fanart):
	try:
		# dbcon = database.connect(control.metaFile())
		dbcon = database.connect(control.metacacheFile)
		dbcur = dbcon.cursor()
		args = [i['imdb'] for i in items]
		dbcur.execute('SELECT * FROM mv WHERE imdb IN (%s)' % ', '.join(list(map(lambda arg:  "'%s'" % arg, args))))
		data = dbcur.fetchall()
	except:
		return items

	for i in range(0, len(items)):
		try:
			item = items[i]
			match = [x for x in data if x[1] == item['imdb']][0]
			try:
				if poster in item and item[poster] != '0':
					raise Exception()
				if match[2] == '0':
					raise Exception()
				items[i].update({poster: link % ('300', '/%s.jpg' % match[2])})
			except:
				pass
			try:
				if fanart in item and item[fanart] != '0':
					raise Exception()
				if match[3] == '0':
					raise Exception()
				items[i].update({fanart: link % ('1280', '/%s.jpg' % match[3])})
			except:
				pass
		except:
			pass

	dbcon.close()
	return items
