#!/usr/bin/env python
'''
Export all files in our wordpress servers into a specified directory (with metadata) and use git client to upload to standard git repo.
Using the Git API might be better, but initial testing was unsuccessful. This method is "OK"
'''

import datetime, xmlrpclib, sys, tempfile
from datetime import datetime


import os

server_list = ['planner.ardupilot.com', 'copter.ardupilot.com'];


from optparse import OptionParser
parser = OptionParser("copy_common.py [options]")
parser.add_option("-u","--username", help="Wordpress username", default=None)
parser.add_option("-p","--password", help="Wordpress password", default=None)
parser.add_option("--git_user", help="Git user id", default=None)
parser.add_option("--git_password", help="Git password", default=None)
parser.add_option("--target_dir", help="Directory to store data", default="/data/hamish/deleteme/")
#parser.add_option("--slug-prefix", help="slug prefix to look for (editable part of url)", default="common-")
#parser.add_option("--blog-id", help="ID of wiki", default='')
#parser.add_option("--force", action='store_true', help="force update", default=False)

(opts, args) = parser.parse_args()

#Make the target (root) directory on host computer - for containing git tree


if opts.username is None or opts.password is None:
    print("You must supply a username and password for Wordpress")
    sys.exit(1)

if opts.git_user is None or opts.git_password is None:
    print("You must supply a username and password for Git")
    sys.exit(1)


def setup_target_directories(servers):
    # Create root directory on host computer for containing the git tree
    if not os.path.exists(opts.target_dir):
        print 'Create root directory: %s' % opts.target_dir
        os.makedirs(opts.target_dir)
    #Create each of the server directories
    for a_server in servers:
        server_dir=opts.target_dir + a_server + '/'
        if not os.path.exists(server_dir):
            print 'Create directory for: %s' % a_server
            os.makedirs(server_dir)
            

def find_posts_by_server(server):

    src_server = xmlrpclib.ServerProxy('http://'+ server + '/xmlrpc.php')
    src_server.accept_gzip_encoding = False
    '''find the source posts'''
    posts = src_server.wp.getPosts(opts.blog_id, opts.username, opts.password,
                               { 'post_type' : 'wiki', 'number' : 1000000 },
                               [ 'post_title', 'post_id', 'post_modified','post_name' ])


    ret = {}
    allpost_id_title_name = {}
    allpost_slug_id_title = {}
    for p in posts:
        #get matching posts
        if p['post_name'].startswith(slug_prefix):
            ret[p['post_name']] = { 'post_id' : p['post_id'], 'post_modified' : p['post_modified'], 'post_title' : p['post_title'] }

    return ret


def process_all_servers(servers):
    for a_server in servers:
        posts_by_slug = find_posts_by_server(a_server)

        if not posts_by_slug:
            print("No matching posts found in: %s" % a_server)
            sys.exit(1)



        # Create each file

    

        print 'Server: %s' % a_server
        print len(posts_by_slug)


setup_target_directories(server_list)
sys.exit(1)
process_all_servers(server_list)

exit_code = 0

sys.exit(exit_code)  #Debug

