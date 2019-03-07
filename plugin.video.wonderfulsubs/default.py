from resources.lib.ui import control
from resources.lib.ui import utils
from resources.lib.ui.SourcesList import SourcesList
from resources.lib.ui.router import on_param, route, router_process
from resources.lib.WonderfulSubsBrowser import WonderfulSubsBrowser
from resources.lib.WatchlistIntegration import add_watchlist
import urlparse

AB_LIST = ["none"] + [chr(i) for i in range(ord("a"), ord("z")+1)]
AB_LIST_NAMING = ["No Letter"] + [chr(i) for i in range(ord("A"), ord("Z")+1)]

HISTORY_KEY = "addon.history"
LASTWATCHED_KEY = "addon.last_watched"
LASTWATCHED_NAME_KEY = "%s.name" % LASTWATCHED_KEY
LASTWATCHED_URL_KEY = "%s.url" % LASTWATCHED_KEY
LASTWATCHED_IMAGE_KEY = "%s.image" % LASTWATCHED_KEY
HISTORY_DELIM = ":_:"

MENU_ITEMS = [
    (control.lang(30001), "all", ''),
    (control.lang(30002), "letter", ''),
    (control.lang(30003), "latest", ''),
    (control.lang(30004), "popular", ''),
    (control.lang(30005), "random", ''),
    (control.lang(30006), "search_history", ''),
    (control.lang(30007), "settings", ''),
]

_BROWSER = WonderfulSubsBrowser()
control.setContent('tvshows');

def _add_last_watched():
    if not control.getSetting(LASTWATCHED_URL_KEY):
        return

    MENU_ITEMS.insert(0, (
        "%s[I]%s[/I]" % (control.lang(30000),
                         control.getSetting(LASTWATCHED_NAME_KEY)),
        control.getSetting(LASTWATCHED_URL_KEY),
        control.getSetting(LASTWATCHED_IMAGE_KEY)
    ))

def __set_last_watched(url, is_dubbed, name, image):
    control.setSetting(LASTWATCHED_URL_KEY, 'animes/%s/%s' %(url, "dub" if is_dubbed else "sub"))
    control.setSetting(LASTWATCHED_NAME_KEY, '%s %s' %(name, "(Dub)" if is_dubbed else "(Sub)"))
    control.setSetting(LASTWATCHED_IMAGE_KEY, image)

def sortResultsByRes(fetched_urls):
    prefereResSetting = utils.parse_resolution_of_source(control.getSetting('prefres'))

    filtered_urls = filter(lambda x: utils.parse_resolution_of_source(x[0]) <=
                           prefereResSetting, fetched_urls)

    return sorted(filtered_urls, key=lambda x:
                  utils.parse_resolution_of_source(x[0]),
                  reverse=True)

@route('settings')
def SETTINGS(payload, params):
    return control.settingsMenu();

@route('animes/*')
def ANIMES_PAGE(payload, params):
    anime_url, flavor_or_season = payload.rsplit("/", 1)
    if anime_url.find("/") == -1:
        # Seasons
        is_dubbed = True if "dub" == flavor_or_season else False
        seasons = _BROWSER.get_anime_seasons(anime_url, is_dubbed)
        return control.draw_items(seasons)

    season = flavor_or_season
    anime_url, flavor = anime_url.rsplit("/", 1)
    is_dubbed = True if "dub" == flavor else False

    order = control.getSetting('reverseorder')
    episodes = _BROWSER.get_anime_episodes(anime_url, is_dubbed, season)
    if "Ascending" in order:
        episodes = reversed(episodes)
    return control.draw_items(episodes)

@route('letter')
def LIST_ALL_AB(payload, params):
    return control.draw_items([utils.allocate_item(AB_LIST_NAMING[i],
                                                   "letter/%s/1" % x, True)
                               for i, x in enumerate(AB_LIST)])

@route('letter/*')
def SHOW_AB_LISTING(payload, params):
    letter, page = payload.rsplit("/", 1)
    assert letter in AB_LIST, "Bad Param"
    return control.draw_items(_BROWSER.get_by_letter(letter, int(page)))

@route('all')
def LATEST(payload, params):
    return control.draw_items(_BROWSER.get_all())

@route('all/*')
def LATEST_PAGES(payload, params):
    return control.draw_items(_BROWSER.get_all(int(payload)))

@route('latest')
def LATEST(payload, params):
    return control.draw_items(_BROWSER.get_latest())

@route('latest/*')
def LATEST_PAGES(payload, params):
    return control.draw_items(_BROWSER.get_latest(int(payload)))

@route('popular')
def POPSUBBED(payload, params):
    return control.draw_items(_BROWSER.get_popular())

@route('popular/*')
def POPSUBBED_PAGES(payload, params):
    return control.draw_items(_BROWSER.get_popular(int(payload)))

@route('random')
def RANDOM(payload, params):
    return control.draw_items(_BROWSER.get_random())

@route('random/*')
def RANDOM_PAGES(payload, params):
    return control.draw_items(_BROWSER.get_random(int(payload)))

@route('search_history')
def SEARCH_HISTORY(payload, params):
    history = control.getSetting(HISTORY_KEY)
    history_array = history.split(HISTORY_DELIM)
    if history != "" and "Yes" in control.getSetting('searchhistory') :
        return control.draw_items(_BROWSER.search_history(history_array))
    else :
        return SEARCH(payload,params)

@route('clear_history')
def CLEAR_HISTORY(payload, params):
    control.setSetting(HISTORY_KEY, "")
    return LIST_MENU(payload, params)

@route('search')
def SEARCH(payload, params):
    query = control.keyboard(control.lang(30006))
    if not query:
        return False

    # TODO: Better logic here, maybe move functionatly into router?
    if "Yes" in control.getSetting('searchhistory') :
        history = control.getSetting(HISTORY_KEY)
        if history != "" :
            query = query+HISTORY_DELIM
        history=query+history
        while history.count(HISTORY_DELIM) > 6 :
            history=history.rsplit(HISTORY_DELIM, 1)[0]
        control.setSetting(HISTORY_KEY, history)

    return control.draw_items(_BROWSER.search_site(query))

@route('search/*')
def SEARCH_PAGES(payload, params):
    query, page = payload.rsplit("/", 1)
    return control.draw_items(_BROWSER.search_site(query, int(page)))

@route('play/*')
def PLAY(payload, params):
    anime_url, episode = payload.rsplit("/", 1)
    anime_url, season = anime_url.rsplit("/", 1)
    anime_url, flavor = anime_url.rsplit("/", 1)
    is_dubbed = True if "dub" == flavor else False
    name, image = _BROWSER.get_anime_metadata(anime_url, is_dubbed)
    sources = _BROWSER.get_episode_sources(anime_url, is_dubbed, season, episode)
    autoplay = True if 'true' in control.getSetting('autoplay') else False

    s = SourcesList(sorted(sources.items()), autoplay, sortResultsByRes, {
        'title': control.lang(30100),
        'processing': control.lang(30101),
        'choose': control.lang(30102),
        'notfound': control.lang(30103),
    })

    __set_last_watched(anime_url, is_dubbed, name, image)
    return control.play_source(s.get_video_link())

@route('')
def LIST_MENU(payload, params):
    return control.draw_items(
        [utils.allocate_item(name, url, True, image) for name, url, image in MENU_ITEMS]
    )

add_watchlist(MENU_ITEMS)
_add_last_watched()
router_process(control.get_plugin_url(), control.get_plugin_params())