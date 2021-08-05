# -*- coding: utf-8 -*-

import random, time

from core import httptools, scrapertools
from platformcode import logger

host = 'https://dood.to'

def get_video_url(page_url, url_referer=''):
    logger.info("(page_url='%s')" % page_url)
    video_urls = []

    page_url = page_url.replace('/d/','/e/')

    data = httptools.downloadpage(page_url, headers={"referer": host}).data
    # ~ logger.debug(data)

    url = scrapertools.find_single_match(data, "get\('(/pass_md5/[^']+)")
    if url:
        headers = {'Referer': page_url}
        data2 = httptools.downloadpage(host + url, headers=headers).data
        # ~ logger.debug(data2)
        if not data2: return 'Vídeo sin resolver'

        token = scrapertools.find_single_match(data, '"?token=([^"&]+)')
        if not token: return video_urls

        a = ''.join([random.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789') for i in range(10)])
        a += '?token=' + token + '&expiry=' + str(int(time.time()*1000))

        video_urls.append(['mp4', data2 + a +'|Referer=%s' % page_url])

    return video_urls
