# -*- coding: utf-8 -*-
'''
#:'######::'####:'##::::'##:'####:'########::::'###:::::'######::
#'##... ##:. ##:: ##:::: ##:. ##::... ##..::::'## ##:::'##... ##:
# ##:::..::: ##:: ##:::: ##:: ##::::: ##:::::'##:. ##:: ##:::..::
# ##:::::::: ##:: ##:::: ##:: ##::::: ##::::'##:::. ##:. ######::
# ##:::::::: ##::. ##:: ##::: ##::::: ##:::: #########::..... ##:
# ##::: ##:: ##:::. ## ##:::: ##::::: ##:::: ##.... ##:'##::: ##:
#. ######::'####:::. ###::::'####:::: ##:::: ##:::: ##:. ######::
#:......:::....:::::...:::::....:::::..:::::..:::::..:::......:::
'''

import urlparse
from civitasscrapers.modules import control
from civitasscrapers import providerSources, providerNames

params = dict(urlparse.parse_qsl(sys.argv[2].replace('?', '')))
mode = params.get('mode')

def ScraperChoice():
    from civitasscrapers import providerSources
    sourceList = sorted(providerSources())
    control.idle()
    select = control.selectDialog([i for i in sourceList])
    if select == -1: return
    module_choice = sourceList[select]
    control.setSetting('module.provider', module_choice)
    control.openSettings('0.1')

def ToggleProviderAll(enable):
    from civitasscrapers import providerNames
    sourceList = providerNames()
    (setting, open_id) = ('true', '0.3') if enable else ('false', '0.2')
    for i in sourceList:
        source_setting = 'provider.' + i
        control.setSetting(source_setting, setting)
    control.openSettings(open_id)

def toggleAll(setting, open_id=None, sourceList=None):
    from civitasscrapers import getAllHosters
    sourceList = getAllHosters() if not sourceList else sourceList
    for i in sourceList:
        source_setting = 'provider.' + i
        control.setSetting(source_setting, setting)
    control.openSettings(open_id)



if mode == "CivitasSettings":
    control.openSettings('0.0', 'script.module.civitasscrapers')

if mode == "ScraperChoice":
    ScraperChoice()

if mode == "ToggleProviderAll":
    ToggleProviderAll(False if params['action'] == "DisableModuleAll" else True)

if mode == "toggleAll":
    open_id = params['open_id'] if 'open_id' in params else '0.0'
    sourcelist = params['sourcelist'] if 'sourcelist' in params else None
    toggleAll(params['setting'], open_id, sourceList=sourcelist)

if mode == "toggleAllDebrid":
    sourcelist = ['300mbfilms','bestmoviez','directdl','ddlvalley','invictus','myvideolink','playmovies','scenerls','ultrahd','wrzcraft']
    toggleAll(params['setting'], params['open_id'], sourcelist)

if mode == "toggleAllGerman":
    sourcelist = ['allucde','animebase','animeloads','bs','cine','cinenator','ddl','filmpalast','foxx','hdfilme','hdstreams','horrorkino','iload','kinodogs','kinoking','kinow','kinox','lichtspielhaus','movie2k-ac','movie2k-ag','movie2z','movie4k','moviesever','movietown','netzkino','proxer','pureanime','serienstream','seriesever','stream-to','streamdream','streamflix','streamit','tata','video4k','view4u']
    toggleAll(params['setting'], params['open_id'], sourcelist)

if mode == "toggleAllPolish":
    sourcelist = ['alltube','boxfilm','cdahd','cdax','ekinomaniak','ekinotv','filiser','filmwebbooster','iitv','movieneo','openkatalog','paczamy','segos','szukajkatv','trt']
    toggleAll(params['setting'], params['open_id'], sourcelist)

if mode == "toggleAllForeign":
    sourcelist = ['allucde','animebase','animeloads','bs','cine','cinenator','ddl','filmpalast','foxx','hdfilme','hdstreams','horrorkino','iload','kinodogs','kinoking','kinow','kinox','lichtspielhaus','movie2k-ac','movie2k-ag','movie2z','movie4k','moviesever','movietown','netzkino','proxer','pureanime','serienstream','seriesever','stream-to','streamdream','streamflix','streamit','tata','video4k','view4u','alltube','boxfilm','cdahd','cdax','ekinomaniak','ekinotv','filiser','filmwebbooster','iitv','movieneo','openkatalog','paczamy','segos','szukajkatv','trt']
    toggleAll(params['setting'], params['open_id'], sourcelist)

if mode == "toggleAllTorrent":
    sourcelist = ['bitlord','torrentapi']
    toggleAll(params['setting'], params['open_id'], sourcelist)

if mode == "Defaults":
    sourcelist = ['0123putlocker','123fox','123hbo','123hulu','123movieshubz','300mbdownload','animetoon','azmovies','bnwmovies','cartoonhd','cmovies','cmovieshdbz','coolmoviezone','extramovies','fmovies','freefmovies','freeputlockers','furk','gostream','gowatchseries','Hdmto','hdpopcorns','kattv','l23movies','library','moviesonline','movietoken','myprojectfreetv','openloadmovie','ororo','plocker','primewire','putlocker','reddit','rlsbb','scenerls','seehd','series9','seriesfree','seriesonline','solarmovies','tvbox','videoscraper','vidics','watchseries','xwatchseries']
    toggleAll(params['setting'], params['open_id'], sourcelist)
