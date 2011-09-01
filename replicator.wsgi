#! /usr/bin/env python


import re
from cgi import escape
from wsgiref.simple_server import make_server
import os.path
import mimetypes
import urllib


mimetypes.init()
ROOT_DIR = "/tmp/"#"/Users/sjolicoeur/Sites/"
BLOCK_SIZE = 2048
FRIENDS = ["http://localhost/"] #["http://www.nfb.ca/"]

# 
def download_and_send_file(file_path, size, remote_file=None):
    if  remote_file :
        with open(file_path, "w") as f:
            block = remote_file.read(size)
            while block:
                yield block
                f.write(block)
                block = remote_file.read(size)
            
def send_file(file_path, size, remote_file=None):
    with open(file_path) as f:
        block = f.read(size)
        while block:
            yield block
            block = f.read(size)

def friends_have_file(servers, path, requester_ip=None):
    path_regex = r'^(?P<path>[\w|/|\-~]+)/(?P<file>[\w|-]+\.[\w]{1,3})?'
    for server in servers :
        # if server ip in excluded ips meaning a request coming from a friendly do not ask it for the file
        url = server + path
        filehandle = urllib.urlopen(url)
        if filehandle.code == 200 :
            # sync file
            # ask friend if path is file or dir or get from headers?
            #data = filehandle.read()
            regex_match = re.match(path_regex, path)
            if regex_match :
                fs_dir_path = ROOT_DIR + regex_match.group("path")
                print "Matched the following " , regex_match.groups(), "for path :", path
                if not os.path.isdir(fs_dir_path) :
                    # create dir
                    print "creating directory", fs_dir_path
                    os.makedirs(fs_dir_path)
                #if regex_match.group("file") :
                #    print "creating file", regex_match.group("file"), "in path :", ROOT_DIR + path
                #    with open(ROOT_DIR + path, "w") as f:
                #        f.write(data)  
            return True, filehandle
    return False, None

# 
# size= os.path.getsize(file_path)
# headers = [
#    ("Content-type", mimetype),
#    ("Content-length", str(size)),
# ]
# start_response("200 OK", headers)
# return send_file(file_path, size)


def index(environ, start_response):
    """This function will be mounted on "/"
	"""
    start_response('200 OK', [('Content-Type', 'text/html')])
    return ['''Great You've found me! Now Dance!!!!!''']


def not_found(environ, start_response):
    """Called if no URL matches."""
    start_response('404 NOT FOUND', [('Content-Type', 'text/plain')])
    return ['Not Found']


def application(environ, start_response):
    """
    The main WSGI application. Dispatch the current request to
    the functions from above and store the regular expression
    captures in the WSGI environment as  `myapp.url_args` so that
    the functions from above can access the url placeholders.

    If nothing matches call the `not_found` function.
    """
    #print environ
    requested_path = environ.get('PATH_INFO', '').lstrip('/')
    system_path = ROOT_DIR + requested_path
    if os.path.exists(system_path) :
        if os.path.isdir(system_path) :
            return index(environ, start_response)
        else :
            print " already had file on hand! "
            guessed_mime_type = mimetypes.guess_type(system_path)[0]
            start_response('200 OK', [('Content-Type', guessed_mime_type)])
            return send_file(system_path, BLOCK_SIZE)
    else :
        print " searching for file "
        found_file, remote_file = friends_have_file(FRIENDS, requested_path)
        if found_file :
            guessed_mime_type = mimetypes.guess_type(system_path)[0]
            start_response('200 OK', [('Content-Type', guessed_mime_type)])
            return download_and_send_file(system_path, BLOCK_SIZE, remote_file)
        else :
            return not_found(environ, start_response)

    return not_found(environ, start_response)

if __name__ == '__main__':
	httpd = make_server('localhost', 8051, application)
	httpd.serve_forever()
