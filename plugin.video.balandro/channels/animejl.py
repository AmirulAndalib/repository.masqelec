# -*- coding: utf-8 -*-

import re

from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, servertools, tmdb


host = 'https://www.anime-jl.net/'


def mainlist(item):
    return mainlist_animes(item)


def mainlist_animes(item):
    logger.info()
    itemlist = []

    descartar_anime = config.get_setting('descartar_anime', default=False)

    if descartar_anime: return itemlist

    if config.get_setting('adults_password'):
        from modules import actions
        if actions.adults_password(item) == False:
            return itemlist

    itemlist.append(item.clone( title = 'Buscar anime ...', action = 'search', search_type = 'tvshow', text_color='springgreen' ))

    itemlist.append(item.clone( title = 'Catálogo', action = 'list_all', url = host + 'animes', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Últimos episodios', action = 'list_last', url = host, search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Estrenos', action = 'list_all', url = host + 'animes?estado%5B%5D=2&order=created', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'En emisión', action = 'list_all', url = host + 'animes?estado%5B%5D=0&order=created', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Finalizados', action = 'list_all', url = host + 'animes?estado%5B%5D=1&order=created', search_type = 'tvshow' ))

    itemlist.append(item.clone( title = 'Por categorías', action = 'categorias', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Por género', action = 'generos', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Por año', action = 'anios', search_type = 'tvshow' ))

    return itemlist


def categorias(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone( title = 'Animes', action = 'list_all', url = host + 'animes?tipo%5B%5D=1&order=created', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Donghuas', action = 'list_all', url = host + 'animes?tipo%5B%5D=7&order=created', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Ovas', action = 'list_all', url = host + 'animes?tipo%5B%5D=2&order=created', search_type = 'tvshow' ))
    itemlist.append(item.clone( title = 'Películas', action = 'list_all', url = host + 'animes?tipo%5B%5D=3&order=created', search_type = 'tvshow' ))

    return itemlist


def generos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(host + 'animes').data
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, '<select name="genre(.*?)</select>')

    matches = re.compile("<option value='(.*?)'.*?>(.*?)</option>").findall(bloque)

    for value, title in matches:
        url = host + 'animes?genre%5B%5D=' + value + '&order=created'

        itemlist.append(item.clone( title = title, action = 'list_all', url = url ))

    return sorted(itemlist,key=lambda x: x.title)


def anios(item):
    logger.info()
    itemlist = []

    from datetime import datetime
    current_year = int(datetime.today().year)

    for x in range(current_year, 1989, -1):
        url = host + 'animes?year%5B%5D=' + str(x) + '&order=created'

        itemlist.append(item.clone( title = str(x), url = url, action='list_all' ))

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    patron = "<article class='Anime alt B'><a href='([^']+)'>.*?class=.*?<img src='([^']+)' alt='([^']+)'>"
    patron += "</figure><span class='Type' .*?>([^']+)</span>.*?star.*?<p>([^<]+)</p>"

    matches = scrapertools.find_multiple_matches(data, patron)

    for url, thumb, title, type, plot in matches:
        thumb = host + thumb

        type = type.strip().lower()

        titulo = title
        titulo = titulo.replace('Español Latino', '').replace('Español latino', '').replace('español Latino', '').replace('spañol latino', '').strip()

        if type == 'pelicula':
            itemlist.append(item.clone( action='episodios', url=url, title=title, thumbnail=thumb, 
                                        contentType = 'movie', contentTitle = titulo, infoLabels={'year': '-', 'plot': plot} ))
        else:
            itemlist.append(item.clone( action='episodios', url=url, title=title, thumbnail=thumb, 
                                        contentType = 'tvshow', contentSerieName = titulo, infoLabels={'year': '-', 'plot': plot} ))

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        next_page = scrapertools.find_single_match(data, '<a class="page-link" href="([^"]+)" rel="next">')

        if next_page:
            actual_page = scrapertools.find_single_match(item.url, '([^\?]+)?')

            itemlist.append(item.clone( title = 'Siguientes ...', url = '%s%s' % (host, next_page) if not host in next_page else next_page,
                                        action = 'list_all', text_color = 'coral' ))

    return itemlist


def list_last(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    bloque = scrapertools.find_single_match(data, "<h2>Últimos episodios agregados(.*?)</ul>")

    patron = "<li><a href='(.*?)' class.*?<img src='(.*?)' alt='(.*?)'></span><span class='Capi'>(.*?)</span>"

    matches = scrapertools.find_multiple_matches(bloque, patron)

    for url, thumb, title, epis in matches:
        title = title.replace('ver ', '')

        thumb = host + thumb

        if not epis.lower() in title: titulo = '%s - %s' % (title, epis)
        else: titulo = title

        itemlist.append(item.clone( action='findvideos', url=url, title=titulo, thumbnail=thumb, contentType='movie', contentTitle=title ))

    return itemlist


def episodios(item):
    logger.info()
    itemlist = []

    if not item.page: item.page = 0
    if not item.perpage: item.perpage = 50

    data = httptools.downloadpage(item.url).data
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    matches = scrapertools.find_multiple_matches(data, '\[(\d+),"([^"]+)","([^"]+)",[^\]]+\]')

    if item.page == 0:
        sum_parts = len(matches)
        if sum_parts > 250:
            if platformtools.dialog_yesno(item.contentSerieName.replace('&#038;', '&').replace('&#8217;', "'"), '¿ Hay [COLOR yellow][B]' + str(sum_parts) + '[/B][/COLOR] elementos disponibles, desea cargarlos en bloques de [COLOR cyan][B]250[/B][/COLOR] elementos?'):
                platformtools.dialog_notification('AnimeJl', '[COLOR cyan]Cargando elementos[/COLOR]')
                item.perpage = 250

    for epis, url, thumb in matches[item.page * item.perpage:]:
        title = 'Episodio %s' % epis

        url = "%s/%s" % (item.url, url)

        itemlist.append(item.clone( action='findvideos', url = url, title = title, language='Vose',
                        contentType = 'episode', contentSeason = 1, contentEpisodeNumber=epis ))

        if len(itemlist) >= item.perpage:
            break

    tmdb.set_infoLabels(itemlist)

    if itemlist:
        if len(matches) > ((item.page + 1) * item.perpage):
            itemlist.append(item.clone( title="Siguientes ...", action="episodios", page = item.page + 1, perpage = item.perpage, text_color='coral' ))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r'\n|\r|\t|\s{2}|&nbsp;', '', data)

    ses = 0

    matches = scrapertools.find_multiple_matches(data, 'video\[\d+\]\s*=\s*\'<iframe.*?src="([^"]+)"')

    for url in matches:
        ses += 1

        if url:
            if url.startswith('//'): url = 'https:' + url

            if '/hqq.' in url or '/waaw.' in url or '/netu.' in url: continue

            if url.startswith('https://animejl.top/v/'): url = url.replace('https://animejl.top/v/', 'https://vanfem.com/v/')

            servidor = servertools.get_server_from_url(url)
            servidor = servertools.corregir_servidor(servidor)

            url = servertools.normalize_url(servidor, url)

            if servidor == 'zplayer': url = url + '|' + host

            if not servidor == 'directo':
                itemlist.append(Item( channel = item.channel, action = 'play', server = servidor, title = '', url = url ))

    # ~ descargas  no se tratan por anomizador

    if not itemlist:
        if not ses == 0:
            platformtools.dialog_notification(config.__addon_name, '[COLOR tan][B]Sin enlaces Soportados[/B][/COLOR]')
            return

    return itemlist


def search(item, texto):
    logger.info()
    try:
        item.url = host + 'animes?q=' + texto.replace(" ", "+")
        return list_all(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
