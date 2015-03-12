#!/usr/bin/env python
'''
Export all files in our wordpress servers into a specified directory (with metadata) and use git client to upload to standard git repo.
Using the Git API might be better, but initial testing was unsuccessful. This method is "OK"
'''

import datetime, xmlrpclib, sys, tempfile


import os
import subprocess #for calling git


server_list = ['planner.ardupilot.com', 'copter.ardupilot.com'];


from optparse import OptionParser
parser = OptionParser("copy_common.py [options]")
parser.add_option("-u","--username", help="Wordpress username", default=None)
parser.add_option("-p","--password", help="Wordpress password", default=None)
parser.add_option("--git_user", help="Git user id", default=None)
parser.add_option("--git_password", help="Git password", default=None)
parser.add_option("--target_dir", help="Directory to store data (absolute path to root)", default="/data/hamish/deleteme/")
parser.add_option("--blog-id", help="ID of wiki", default='')
parser.add_option("--git_site", help="Git site owner to upload to", default='diydrones')
parser.add_option("--git_repo", help="Git repo name", default='ardupilot_wordpress_sources')
parser.add_option("--clean", help="If defined, clean the repo and restart", default=None)
parser.add_option("--delete", help="Delete any items from repo that are not retrieved from server", default=None)

(opts, args) = parser.parse_args()


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

clonerepo="https://github.com/"+opts.git_site+"/"+opts.git_repo+".git"
#print 'clonerepo: %s' % clonerepo
clonetarget=opts.target_dir+opts.git_repo+'/'
#print 'clonetarget: %s' % clonetarget

#Clean directory to get everything from git if reqeusted
if opts.clean:
    print 'cleaning'
    exitCode = subprocess.call(["sudo", "rm", "-r", opts.target_dir ] )


def setup_target_directories(servers):
    # Create root directory on host computer for containing the git tree
    if not os.path.exists(opts.target_dir):
        print 'Create root directory: %s' % opts.target_dir
        os.makedirs(opts.target_dir)

        #print 'Cloning git repo'
        os.chdir(opts.target_dir)
        exitCode = subprocess.check_call(["git", "clone", clonerepo, clonetarget ] )

        #print 'exitcode: %s' % exitCode                  

    else:
        #Check if git repo exists and pull latest
        if not os.path.exists(clonetarget+'.git'):
            #print 'Cloning git repo'
            os.chdir(opts.target_dir)
            exitCode = subprocess.check_call(["git", "clone", clonerepo, clonetarget ] )
        else:
            #Git pull
            os.chdir(clonetarget)
            exitCode = subprocess.check_call(["git", "pull"] )


        

    # Create directory for common files (from planner.ardupilot.com)
    commondir= opts.target_dir+opts.git_repo+'/common.ardupilot.com/'
    if not os.path.exists(commondir):
        print 'Create common directory: %s' % commondir
        os.makedirs(commondir)

    #Create each of the server directories
    for a_server in servers:
        server_dir=opts.target_dir + opts.git_repo +'/'+ a_server + '/'
        if not os.path.exists(server_dir):
            print 'Create directory for: %s' % a_server
            os.makedirs(server_dir)


def get_files_in_git():
    """Returns dictionary of servers, each containing set of stubs for articles. Gets from filename - should be run after git but before getting new files. Assumes file hierarchy."""
    import glob
    ret={}
    matchfiles= glob.glob(clonetarget+"/*/*.html")            
    for file in matchfiles:
        filesplit=file.rsplit("/",2)
        if filesplit[1] in ret:
            tmpset=ret[filesplit[1]]
        else:
            tmpset=set()
        tmpset.add(filesplit[2].rsplit(".",1)[0])
        ret[filesplit[1]]=tmpset
    return ret



def find_posts_by_server(server):
    """Gets all the post information into a stub-sorted dictionary. Common topics only collected in plannner. wiki"""

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
    ret={}
    for a_server in servers:
	print 'Getting server: %s' % a_server
        posts_by_slug = find_posts_by_server(a_server)

        if not posts_by_slug:
            print("No matching posts found in: %s" % a_server)
            sys.exit(1)

        #process all of the files
        for slug in posts_by_slug:
            metadata=export_post_metadata(posts_by_slug[slug])
            server_name = a_server
            if posts_by_slug[slug]['post_name'].startswith('common-'):
                server_name='common.ardupilot.com'
            filename=clonetarget + server_name + '/'+slug+'.html'
            print 'writing file: %s' % filename
            target_file = open (filename, 'w') ## a will append, w will over-write
            target_file.write(metadata.encode('utf8'))
            target_file.write(posts_by_slug[slug]['post_content'].encode('utf8'))
            target_file.close()
            if server_name in ret:
                tmp_set=ret[server_name]
            else:
                tmp_set=set()
            tmp_set.add(slug)
            ret[server_name]=tmp_set
            #sys.exit(1)
    return ret


def remove_missing_files_git(files_git,files_server):
    print 'Files in Git but not server - may need to be deleted'
    for server in files_git:
        print "Server: %s" % server
        print files_git[server]-files_server[server]


            
def upload_to_git():
    os.chdir(clonetarget)
    #add any missing topics
    exitCode = subprocess.check_call(["git", "add", "."] )

    try:
        #commit changes
        exitCode = subprocess.check_call(["git", "commit", "-m","Auto commiting files"] )
    except:
        print 'Possible error commiting  list - may just be nothing to commit'
        
    try:
        #Push changes
        gitpushrepo="https://"+opts.git_user+':'+opts.git_password+'@github.com/'+opts.git_site+"/"+opts.git_repo+".git"
        exitCode = subprocess.check_call(["git", "push", "--repo", gitpushrepo ] )
    except:
        print 'Possible error pushing changes - check log'


setup_target_directories(server_list)
stubs_in_git=get_files_in_git()
stubs_from_servers=process_all_servers(server_list)
upload_to_git()
remove_missing_files_git(stubs_in_git,stubs_from_servers)


