#!/usr/bin/env python
'''
copy common-* pages from one site to another
'''

import datetime, xmlrpclib, sys, tempfile
from datetime import datetime


from optparse import OptionParser
parser = OptionParser("copy_common.py [options]")
parser.add_option("--username", help="Wordpress username", default=None)
parser.add_option("--password", help="Wordpress password", default=None)
parser.add_option("--url-src", help="Source Wordpress URL", default='http://copter.ardupilot.com')
parser.add_option("--blog-id", help="ID of wiki", default='')
parser.add_option("--force", action='store_true', help="force update", default=False)

(opts, args) = parser.parse_args()

if opts.username is None or opts.password is None:
    print("You must supply a username and password")
    sys.exit(1)

src_server = xmlrpclib.ServerProxy(opts.url_src + '/xmlrpc.php')
src_server.accept_gzip_encoding = False

def read_server(server):
    '''find the source posts'''
    try:
        posts = server.wp.getPosts(opts.blog_id, opts.username, opts.password,
                               { 'post_type' : 'wiki', 'number' : 1 },
                               [ 'post_name' ])
    except:
        sys.exit(1)


read_server(src_server)

#sys.exit(1)

