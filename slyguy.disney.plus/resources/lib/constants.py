CLIENT_ID = 'disney-svod-3d9324fc'
CLIENT_VERSION = '6.1.0' #6.5.0

API_VERSION = '5.1'
API_KEY = 'ZGlzbmV5JmFuZHJvaWQmMS4wLjA.bkeb0m230uUhv8qrAXuNu39tbE_mD5EEhM_NAcohjyA'
CONFIG_URL = 'https://bam-sdk-configs.bamgrid.com/bam-sdk/v3.0/{}/android/v{}/google/tv/prod.json'.format(CLIENT_ID, CLIENT_VERSION)
PAGE_SIZE_SETS = 15
PAGE_SIZE_CONTENT = 30
SEARCH_QUERY_TYPE = 'ge'
BAM_PARTNER = 'disney'

WATCHLIST_SET_ID = '6f3e3200-ce38-4865-8500-a9f463c1971e'
WATCHLIST_SET_TYPE = 'WatchlistSet'
CONTINUE_WATCHING_SET_ID = '76aed686-1837-49bd-b4f5-5d2a27c0c8d4'
CONTINUE_WATCHING_SET_TYPE = 'ContinueWatchingSet'

HEADERS = {
    'User-Agent': 'BAMSDK/v{} ({} 1.16.0.0; v3.0/v{}; android; tv)'.format(CLIENT_VERSION, CLIENT_ID, CLIENT_VERSION),
    'x-application-version': 'google',
    'x-bamsdk-platform-id': 'android-tv',
    'x-bamsdk-client-id': CLIENT_ID,
    'x-bamsdk-platform': 'android-tv',
    'x-bamsdk-version': CLIENT_VERSION,
    'Accept-Encoding': 'gzip',
}

RATIO_ASK = 0
RATIO_IMAX = 1
RATIO_WIDESCREEN = 2
RATIO_TYPES = [RATIO_ASK, RATIO_IMAX, RATIO_WIDESCREEN]