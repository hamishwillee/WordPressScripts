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
parser.add_option("--blog-id", help="ID of wiki", default='')
#parser.add_option("--slug-prefix", help="slug prefix to look for (editable part of url)", default="common-")
#parser.add_option("--blog-id", help="ID of wiki", default='')
#parser.add_option("--force", action='store_true', help="force update", default=False)

(opts, args) = parser.parse_args()

#Make the target (root) directory on host computer - for containing git tree

print 'WP Username: %s' % opts.username
print 'WP Password: %s' % opts.password
print 'Git Username: %s' % opts.git_user
print 'Git Password: %s' % opts.git_password
print 'Target Git directory (on local PC): %s' % opts.target_dir

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

    # Create directory for common files (from planner.ardupilot.com)
    commondir= opts.target_dir+'common.ardupilot.com/'
    if not os.path.exists(commondir):
        print 'Create common directory: %s' % commondir
        os.makedirs(commondir)

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
                               [ 'post_title', 'post_id', 'post_modified','post_name','post_content','post_status','menu_order','post_parent' ])


    ret = {}
    parentmap={}
    for p in posts:
        #store value if it is published. Only store "common" pages for planner wiki.
        if 'publish' == p['post_status']:
            parentmap[p['post_id']] = { 'post_name': p['post_name'], 'post_title':p['post_title'] }
            if not p['post_name'].startswith('common-'):
                ret[p['post_name']] = { 'post_id' : p['post_id'], 'post_modified' : p['post_modified'], 'post_title' : p['post_title'], 'post_name' : p['post_name'], 'post_content':p['post_content'],
                'menu_order':p['menu_order'],'post_parent':p['post_parent'] }
            else:
                if server.startswith('planner.'):
                    ret[p['post_name']] = { 'post_id' : p['post_id'], 'post_modified' : p['post_modified'], 'post_title' : p['post_title'], 'post_name' : p['post_name'], 'post_content':p['post_content'],'menu_order':p['menu_order'],'post_parent':p['post_parent'] }   
    
    #Get the stub and title of the parent
    for stub in ret:
        parentid=ret[stub]['post_parent']
        if parentid in parentmap:
            ret[stub]['post_parent_stub']=parentmap[parentid]['post_name']
            ret[stub]['post_parent_title']=parentmap[parentid]['post_title']
        else:
            ret[stub]['post_parent_stub']=''
            ret[stub]['post_parent_title']=''


    return ret


def export_post_metadata(page):
    metadata='<!-- \nSTART METADATA - Only title should be translated \n'
    #print page
    metadata=metadata+'slug: %s \n' % page['post_name']
    metadata=metadata+'title: %s \n' % page['post_title']
    metadata=metadata+'id: %s \n' % page['post_id']
    metadata=metadata+'menu_order: %s \n' % page['menu_order']
    metadata=metadata+'post_parent_id: %s \n' % page['post_parent']
    metadata=metadata+'post_parent_stub: %s \n' % page['post_parent_stub']
    metadata=metadata+'post_parent_title: %s \n' % page['post_parent_title']
    metadata=metadata+'END METADATA \n-->\n'

    return metadata
    



def process_all_servers(servers):
    for a_server in servers:
	print 'Getting server: %s' % a_server
        posts_by_slug = find_posts_by_server(a_server)

        if not posts_by_slug:
            print("No matching posts found in: %s" % a_server)
            sys.exit(1)


        #process all of the files
        for slug in posts_by_slug:
            metadata=export_post_metadata(posts_by_slug[slug])
            print 'writing file: %s' % slug
            if posts_by_slug[slug]['post_name'].startswith('common-'):
                filename=opts.target_dir + 'common.ardupilot.com' + '/'+slug+'.html'
            else:
                filename=opts.target_dir + a_server + '/'+slug+'.html'
            print 'filename: %s' % filename
            target_file = open (filename, 'w') ## a will append, w will over-write
            target_file.write(metadata.encode('utf8'))
            target_file.write(posts_by_slug[slug]['post_content'].encode('utf8'))
            target_file.close()
            #sys.exit(1)
            
            


setup_target_directories(server_list)
process_all_servers(server_list)

exit_code = 0
sys.exit(exit_code)  #Debug

