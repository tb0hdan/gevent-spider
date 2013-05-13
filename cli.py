#!/usr/bin/env python2.7
from gevent.monkey import patch_all; patch_all()

def web():
    from gevent_spider.web import serve
    print 'Serving on port 8088...'
    serve()

web()