# -*- coding: utf-8 -*-
import sys

# Support Python 2.7 (Kodi 17.6) and Python 3+ (Kodi 18).
if sys.version.startswith('3'):
    from urllib.parse import parse_qsl, urlencode, quote_plus
    DICT_ITER_ITEMS = lambda d: iter(d.items())
    DICT_ITER_KEYS = lambda d: iter(d.keys())
    UNICODE = str
    RANGE = range
else:
    from urlparse import parse_qsl
    from urllib import urlencode, quote_plus
    DICT_ITER_ITEMS = lambda d: d.iteritems()
    DICT_ITER_KEYS = lambda d: d.iterkeys()
    UNICODE = unicode
    RANGE = xrange