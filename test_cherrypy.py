import time
import os
import re
from cgi import escape

import os.path
import mimetypes
import urllib
import cherrypy
from multiprocessing import Process, Queue, current_process

from config import ROOT_DIR, BLOCK_SIZE, FRIENDS
from monkey_staticserve import serve_file
mimetypes.init()

file_path2 = "/tmp/test.m4v"
guessed_mime_type = mimetypes.guess_type(file_path2)[0]
size =  2048
BEING_DOWNLOADED = {}

def download_file(file_path, size, remote_file=None):
    if  remote_file :
        with open(file_path, "w+ar") as f:
            block = remote_file.read(size)
            while block:
                #yield block #"%x" % len(block) + "\r\n" + block + "\r\n"
                f.write(block)
                f.flush()
                block = remote_file.read(size)
            BEING_DOWNLOADED.pop(file_path)
            print "\n\n\t\tended file!!!\n\n"
            #yield "0\r\n\r\n"

def download_and_send_file(file_path, size, remote_file=None):
    if  remote_file :
        with open(file_path, "w+ar") as f:
            block = remote_file.read(size)
            while block:
                yield block #"%x" % len(block) + "\r\n" + block + "\r\n"
                f.write(block)
                block = remote_file.read(size)
                print " read block \n"
            BEING_DOWNLOADED.pop(file_path)
            print "\n\n\t\tended file!!!\n\n"
            #yield "0\r\n\r\n"
            
def send_file(file_path, size, remote_file=None):
    with open(file_path) as f:
        block = f.read(size)
        while block:
            yield block
            block = f.read(size)

def friends_have_file(servers, path, requester_ip=None):
    path_regex = r'^(?P<path>[\w|/|\-~]+)/(?P<file>[\w|-]+\.[\w]{1,3})?'
    # split by / look at last and see if it is a file in not don't pop out
    for server in servers :
        # if server ip in excluded ips meaning a request coming from a friendly do not ask it for the file
        url = server + path
        print " contacting friend :: ", url
        filehandle = urllib.urlopen(url)
        if filehandle.code == 200 :
            print "found file in remote server"
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
                if not regex_match.group("file") :
                    filehandle = None # do not download index file
                #    print "creating file", regex_match.group("file"), "in path :", ROOT_DIR + path
                #    with open(ROOT_DIR + path, "w") as f:
                #        f.write(data)  
            return True, filehandle
    return False, None




def index():
    """This function will be mounted on "/"
	"""
    cherrypy.lib.cptools.response_headers(headers=[('Content-Type', "text/html; charset=UTF-8")], debug=True )
    return '''Great You've found me! Now Dance!!!!!'''


def not_found():
    """Called if no URL matches."""
    raise cherrypy.HTTPError(404, "Not Found.")
    


  

class Questions(object):
    _cp_config = { 
            'tools.encode.on':True,
            'tools.encode.encoding':'utf8',
            } 
    

    @cherrypy.expose()
    #@cherrypy.tools.firstheaders()
    def index(self):    
        cherrypy.lib.cptools.response_headers(headers=[('Content-Type', guessed_mime_type)], debug=True )
        ##cherrypy.response.first_headers = [('Content-Type', guessed_mime_type)]#[('foo', '1'), ('foo', '2')]    
        print "in index!!!"
        def get_file():
            with open(file_path2, "r") as f:
                
                block = f.read(size)
                while block:
                    #print "\t\t\twritting block"
                    yield block 
                    block = f.read(size)
        #return get_file()
        #return cherrypy.lib.static.serve_file(file_path2, content_type=guessed_mime_type,debug=True)
        return serve_file(file_path2, content_type=guessed_mime_type,debug=True)
        
    index._cp_config = {'response.stream': True}

    @cherrypy.expose()
    def default(self, *args, **kwarg):
        #cherrypy.lib.cptools.response_headers(headers=[('Content-Type', "text/html; charset=UTF-8")], debug=True )
        #path =  "/".join(args) 
        #return attr.upper()
        #
        requested_path = "/".join(args) #environ.get('PATH_INFO', '').lstrip('/')
        print " this is the requested path ", requested_path
        system_path = ROOT_DIR + requested_path
        print " this is what  am looking for ", system_path
        if os.path.exists(system_path) :
            if os.path.isdir(system_path) :
                return index()
            else :
                print " already had file on hand! "
                print " of cached length :: ", BEING_DOWNLOADED.get(system_path, None)
                guessed_mime_type = mimetypes.guess_type(system_path)[0]
                #cherrypy.lib.cptools.response_headers(headers=[('Content-Type', guessed_mime_type)], debug=True )
                #return send_file(system_path, BLOCK_SIZE)
                return serve_file(system_path, content_type=guessed_mime_type,debug=True, content_length=BEING_DOWNLOADED.get(system_path, None))
                
        else :
            print " searching for file "
            found_file, remote_file = friends_have_file(FRIENDS, requested_path)
            if os.path.isdir(system_path) :
                return index()
            elif found_file and remote_file and not system_path in BEING_DOWNLOADED:
                BEING_DOWNLOADED[system_path] = True
                #guessed_mime_type = mimetypes.guess_type(system_path)[0] or 'text/html'
                guessed_mime_type = remote_file.info().getheader("Content-Type")  
                print "guessed mimetype", guessed_mime_type
                content_length = remote_file.info().getheader("Content-Length") #("Transfer-Encoding","chunked")
                BEING_DOWNLOADED[system_path] = content_length
                #cherrypy.lib.cptools.response_headers(headers=[ ("Content-Length",content_length)], debug=True )
                # fork download here
                Process(target=download_file, args=(system_path, BLOCK_SIZE, remote_file)).start()
                #sleep a while to let the download start
                time.sleep(0.2)
                #return download_and_send_file(system_path, BLOCK_SIZE, remote_file)
                return serve_file(system_path, content_type=guessed_mime_type, content_length=content_length, debug=True)
                
            else :
                print "file not found!", BEING_DOWNLOADED
                return not_found()

        return not_found()
        
        
        
        
        
    default._cp_config = {'response.stream': True}
    
    
    
if __name__ == '__main__':
    cherrypy.config.update({'server.socket_host': '0.0.0.0',
                               'server.socket_port': 8080,
                               'server.thread_pool' : 30,
                               'server.max_request_body_size' : 50000000000,
                               'server.protocol_version' : "HTTP/1.1",
                            })
    #root = Questions()
    #app = cherrypy.tree.mount(root, script_name='/')
    #cherrypy.engine.start()
    #cherrypy.engine.block()
    cherrypy.quickstart(Questions())
