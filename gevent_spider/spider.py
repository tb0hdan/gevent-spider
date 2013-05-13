from gevent.threadpool import ThreadPool
from gevent.pool import Pool
from lxml.html import fromstring
from urlparse import urlsplit, urljoin
import requests
from .utils import timer

def spider(client, url, domain_whitelist=None, pool=None, threadpool=None, tested=None):
    client.send_status('Spidering {url}...'.format(url=url))

    domain_whitelist = domain_whitelist or (urlsplit(url).netloc,)
    threadpool = threadpool or ThreadPool(4) # for lxml - 4 workers
    pool = pool or Pool() # maximum number of concurrent HTTP requests
    tested = tested or set([url])

    user_agent = {'User-agent': 'Opera/9.80 (Linux; i686; en) Presto/2.12.388 Version/12.14'}
    with timer() as timed:
        response = requests.get(url, headers=user_agent)

    result = dict(
        status_code = response.status_code,
        length = len(response.text),
        headers = response.headers,
        url = url,
        duration = timed.result(),
    )
    content_type = response.headers.get('content-type')
    client.send_result(result)

    if not content_type.startswith('text/html'):
        return pool

    html = threadpool.apply(fromstring, [response.text])
    try:
        links = html.cssselect('a')
    except:
        links = []
    for link in links:
        try:
            href = link.attrib.get('href').split('#')[0].strip()
        except:
            href = None
        if not href:
            continue
        url = urljoin(response.url, href)
        parts = urlsplit(url)
        if parts.netloc not in domain_whitelist:
            continue
        if url in tested:
            continue
        tested.add(url)
        pool.spawn(spider, client, url, domain_whitelist, pool, threadpool, tested)
    return pool
