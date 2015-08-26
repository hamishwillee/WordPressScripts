#!/usr/bin/env python
'''
copy common-* pages from one site to another

Copying will fail 
* (with announcement) if the target version is newer - but you can force the copy to happen anyway with the --force parameter.
* (silently) if the source has the [copywiki] shortcode and the target wiki is not in its desination field. The copy will not work 
  even if -force is True, but will emit a reason for failure.
'''

import datetime, xmlrpclib, sys, tempfile
from datetime import datetime
import re #To determine if there are copy parameters in the source file

from optparse import OptionParser
parser = OptionParser("copy_common.py [options]")
parser.add_option("--username", help="Wordpress username", default=None)
parser.add_option("--password", help="Wordpress password", default=None)
parser.add_option("--url-src", help="Source Wordpress URL", default=None)
parser.add_option("--url-dst", help="Destination Wordpress URL", default=None)
parser.add_option("--slug-prefix", help="slug prefix to look for (editable part of url)", default="common-")
parser.add_option("--blog-id", help="ID of wiki", default='')
parser.add_option("--force", action='store_true', help="force update", default=False)

(opts, args) = parser.parse_args()

if opts.url_src is None or opts.url_dst is None:
    print("You must supply a base URL for both wordpress sites")
    sys.exit(1)

if opts.username is None or opts.password is None:
    print("You must supply a username and password")
    sys.exit(1)

src_server = xmlrpclib.ServerProxy(opts.url_src + '/xmlrpc.php')
dst_server = xmlrpclib.ServerProxy(opts.url_dst + '/xmlrpc.php')
src_server.accept_gzip_encoding = False
dst_server.accept_gzip_encoding = False

def find_post_by_title_prefix(server, slug_prefix):
    '''find the source posts'''
    posts = server.wp.getPosts(opts.blog_id, opts.username, opts.password,
                               { 'post_type' : 'wiki', 'number' : 1000000 },
                               [ 'post_title', 'post_id', 'post_modified','post_name' ])


    ret = {}
    allpost_id_title_name = {}
    allpost_slug_id_title = {}
    for p in posts:
        #get matching posts
        if p['post_name'].startswith(slug_prefix):
            ret[p['post_name']] = { 'post_id' : p['post_id'], 'post_modified' : p['post_modified'], 'post_title' : p['post_title'] }

        #Get all posts ID to slug map. 
        allpost_id_title_name[p['post_id']] = { 'post_title' : p['post_title'], 'post_name' : p['post_name'] }
        #Get all posts slug to id and title map
        allpost_slug_id_title[p['post_name']] = { 'post_title' : p['post_title'], 'post_id' : p['post_id'] }



    return ret, allpost_id_title_name, allpost_slug_id_title

posts, src_all_by_id, src_all_by_slug = find_post_by_title_prefix(src_server, opts.slug_prefix)


if not posts:
    print("No matching posts found")
    sys.exit(1)

dst_posts, dst_all_by_id, dst_all_by_slug = find_post_by_title_prefix(dst_server, opts.slug_prefix)


exit_code = 0

# which fields to copy over

new_keys = ['post_mime_type', 'post_date_gmt', 'sticky', 'post_date',
            'post_type', 'post_modified', 'custom_fields',
            'post_title', 'post_status', 'post_content',
            'terms', 'post_thumbnail', 'ping_status',
            'comment_status', 'post_format', 'post_name',
            'post_modified_gmt', 'post_excerpt',
            'menu_order']


for slug in posts.keys():
    if slug in dst_posts and posts[slug]['post_modified'] <= dst_posts[slug]['post_modified'] and not opts.force:
        src_date = datetime.strptime('%s' % posts[slug]['post_modified'], "%Y%m%dT%H:%M:%S")
        dst_date = datetime.strptime('%s' %dst_posts[slug]['post_modified'], "%Y%m%dT%H:%M:%S")
        timedelta = dst_date - src_date
        timemins = timedelta.total_seconds() / 60
        #print 'src_date_orig: %s' % posts[slug]['post_modified']
        #print 'dst_date_orig: %s' % dst_posts[slug]['post_modified']
        #print 'src_date: %s' % src_date
        #print 'dst_date: %s' % dst_date
        #print 'timedelta: %s' % timedelta
        #print 'timemins: %s' % timemins
        #print 'repr %s' % repr(timedelta)


        if timemins > 20:
            print("Destination is newer for (%s): %s by %s" % (opts.url_dst, slug, timemins) )
            continue

    try:
        print("Fetching %s" % posts[slug]['post_title'])
    except:
        print("Fetching %s" % slug)

    post = src_server.wp.getPost(opts.blog_id, opts.username, opts.password, posts[slug]['post_id'])


    #Check if post is copyable to target. 
    #Post is not copyable IFF there is a [copywiki] shortcode but it doesn't have the target wiki 
    #listed in the destination string. ie To stop copying, add the shortcode and destination string
    #but omit the target wiki in the destingation string.
    p=re.compile('\[copywiki (.*?)\]')
    p_dest=re.compile('destination="(.*)"')
    m=p.search(post['post_content'])
    target_wiki=opts.url_dst.split('http://')[-1].split('.')[0].lower()

    if m: #There is a match, so we need to confirm if we can copy
        m_dest=p_dest.search(m.group(1))
        if m_dest:
            valid_targets = m_dest.group(1).lower() #These are valid destinations for copy
            if target_wiki not in valid_targets:
                if opts.force:
                    print "CANT COPY. Target wiki (%s) not in article destination shortcode (%s)" % (target_wiki, m.group()) 
                continue



    new_post = {}
    for k in new_keys:
        new_post[k] = post[k]

    #Determine id of post parent if one is defined and matching parent slug exists in target wiki
    if post['post_parent'] != '0': 
        src_parent_id= post['post_parent']
        src_parent_title=src_all_by_id[src_parent_id]['post_title']
        src_parent_slug=src_all_by_id[src_parent_id]['post_name']
        try:
            dst_parent_title=dst_all_by_slug[src_parent_slug]['post_title']
            dst_parent_id=dst_all_by_slug[src_parent_slug]['post_id']

            #Set post parent
            new_post['post_parent'] = dst_parent_id

        except:
            print 'Debug: parent post (slug) missing from desination wik - no parent set'


    if 'link' in post:
        link = post['link']
        newlink = link.replace(opts.url_src, opts.url_dst)
        new_post['link'] = newlink

    # force author to be autotest
    new_post['post_author'] = 'autotest'

    #debug
    #sys.exit(exit_code)

    if slug in dst_posts:
        dst_post = dst_server.wp.getPost(opts.blog_id, opts.username, opts.password, dst_posts[slug]['post_id'])

        if post['post_modified'] <= dst_post['post_modified'] and not opts.force:
            print("Destination is newer")
            continue

        try:
            print("Uploading existing post: %s" % posts[slug]['post_title'])
        except:
            print("Uploading existing post: %s" % slug)

        #print 'debug - slug is present in both so we over-write'
        if not dst_server.wp.editPost(opts.blog_id, opts.username, opts.password, dst_posts[slug]['post_id'], new_post):
            print("Failed to update %s" % posts[slug]['post_title'])
            exit_code = 1
    else:
        try:
            print("Uploading new post: %s" % posts[slug]['post_title'])
        except:
            print("Uploading new post: %s" % slug)

        print 'debug - slug is not present so is new title'
        if not dst_server.wp.newPost(opts.blog_id, opts.username, opts.password, new_post):
            try:
                print("Failed to upload %s" % posts[slug]['post_title'])
            except:
                print("Failed to upload %s" % slug)

            exit_code = 1

sys.exit(exit_code)
