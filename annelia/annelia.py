#!/usr/bin/env python
from __future__ import with_statement
import time
import os
import re
from cgi import escape
from optparse import OptionParser

import os.path
import mimetypes
import urllib
import cherrypy
from cherrypy.process.plugins import Daemonizer
from multiprocessing import Process, Queue, current_process
from urllib import FancyURLopener

from monkey_staticserve import serve_file
mimetypes.add_type("application/vnd.ms-fontobject", ".eot")
mimetypes.add_type("application/octet-stream", ".otf")
mimetypes.add_type("application/octet-stream", ".ttf")
mimetypes.add_type("application/octet-stream", ".woff")
mimetypes.init()

class AnneliaOpener(FancyURLopener):
    version = 'Annelia'



BEING_DOWNLOADED = {}

def download_file(file_path, size, remote_file=None):
    if  remote_file :
        with open(file_path, "w+ar") as f:
            block = remote_file.read(size)
            while block:
                f.write(block)
                f.flush()
                block = remote_file.read(size)
            BEING_DOWNLOADED.pop(file_path)
            #print "\n\n\t\tended file!!!\n\n"

def friends_have_file(servers, path, requester_ip=None):
    path_regex = r'^(?P<path>[\w|/|\-~]+)/(?P<file>[\w|-]+\.[\w]{1,3})?'
    # split by / look at last and see if it is a file in not don't pop out
    for server in servers :
        # if server ip in excluded ips meaning a request coming from a friendly do not ask it for the file
        url = server + path
        cherrypy.log( " contacting friend :: %s" % url )
        filehandle = AnneliaOpener().open(url) #urllib.urlopen(url)
        if filehandle.code == 200 :
            cherrypy.log( "found file in remote server" )
            # sync file
            # ask friend if path is file or dir or get from headers?
            #data = filehandle.read()
            regex_match = re.match(path_regex, path)
            if regex_match :
                fs_dir_path = ROOT_DIR + regex_match.group("path")
                cherrypy.log( "Matched the following %s for path : %s" % (regex_match.groups(), path ) )
                if not os.path.isdir(fs_dir_path) :
                    # create dir
                    cherrypy.log( "creating directory : %s" % fs_dir_path )
                    os.makedirs(fs_dir_path)
                if not regex_match.group("file") :
                    filehandle = None # do not download index file
            return True, filehandle
    return False, None


def not_found():
    """Called if no URL matches."""
    raise cherrypy.HTTPError(404, "Not Found.")
    

class Annelia(object):
    _cp_config = { 
            'tools.encode.on':True,
            'tools.encode.encoding':'utf8',
            } 
    
    @cherrypy.expose()
    def index(self):
        """This function will be mounted on "/"
    	"""
        cherrypy.lib.cptools.response_headers(headers=[('Content-Type', "text/html; charset=UTF-8")], debug=True )
        return '''Great You've found me! Now Dance!!!!!'''


    @cherrypy.expose()
    def default(self, *args, **kwarg):
        req = cherrypy.serving.request
        user_agent = req.headers['User-Agent']
        requested_path = "/".join(args) #environ.get('PATH_INFO', '').lstrip('/')
        system_path = ROOT_DIR + requested_path
        if os.path.exists(system_path) : # file has been found
            if os.path.isdir(system_path) :
                return self.index()
            else :
                cherrypy.log( " already had file on hand! " )
                guessed_mime_type = mimetypes.guess_type(system_path)[0]
                return serve_file(system_path, content_type=guessed_mime_type,debug=True, content_length=BEING_DOWNLOADED.get(system_path, None))
        elif user_agent.lower().startswith("annelia") : # do not have the file and req from another annelia server
            # file was not found and this is a friend ... raise 404
            cherrypy.log( "file was not found and this is a friend ... raise 404" )
            return not_found()
        else :
            cherrypy.log( " searching for file " )
            found_file, remote_file = friends_have_file(FRIENDS, requested_path)
            if os.path.isdir(system_path) :
                return index()
            elif found_file and remote_file and not system_path in BEING_DOWNLOADED:
                BEING_DOWNLOADED[system_path] = True
                guessed_mime_type = remote_file.info().getheader("Content-Type")  
                cherrypy.log( "guessed mimetype : %s" % guessed_mime_type )
                content_length = remote_file.info().getheader("Content-Length") #("Transfer-Encoding","chunked")
                BEING_DOWNLOADED[system_path] = content_length
                # fork download here
                Process(target=download_file, args=(system_path, BLOCK_SIZE, remote_file)).start()
                #sleep a while to let the download start
                time.sleep(0.2)
                return serve_file(system_path, content_type=guessed_mime_type, content_length=content_length, debug=True)
                
            else :
                BEING_DOWNLOADED.pop(system_path)
                return not_found()

        return not_found()
    
    default._cp_config = {'response.stream': True}
    
def get_config():
    """ get the config from the cmd-line"""    
    parser = OptionParser(add_help_option=False)
    parser.add_option("-h", "--help", action="help")
    parser.add_option("-v", "--version",action="store_true", dest="verbose",
                      help="Output the version")
    parser.add_option("-c","--config", dest="config_file", type="string", default='annelia.conf.example',
                      help="set the path of the config file")
    return parser.parse_args()
    
if __name__ == '__main__':
    (options, args) = get_config()
    import ConfigParser
    config = ConfigParser.RawConfigParser()
    config.read(options.config_file)
    
    try :    
        BLOCK_SIZE=  config.getint('ServerConfig', 'block_size')
        ROOT_DIR = config.get('ServerConfig', 'root_dir').strip(" ")
        FRIENDS = [x.strip(" ") for x in config.get('ServerConfig', 'friends').split(",")]
        HOST_IP = config.get('ServerConfig', 'host_ip')
        HOST_PORT = config.getint('ServerConfig', 'host_port')
        THREAD_NUM = config.getint('ServerConfig', 'thread_num')
    except :
        print "BAD CONFIG FILE "
    cherrypy.config.update({'server.socket_host': HOST_IP,
                            'server.socket_port': HOST_PORT,
                            'server.thread_pool' : THREAD_NUM,
                            'server.max_request_body_size' : 50000000000,
                            'server.protocol_version' : "HTTP/1.1",
                            'log.access_file' : os.path.join(os.path.dirname(__file__), "access.log"),             
                            'log.error_file': os.path.join(os.path.dirname(__file__), "errors.log"),             

                            'log.screen': False,  
                            'tools.sessions.on': False,
                            'request.show_tracebacks': False,
                            'environment' : 'production',
                            'tools.gzip.on': True,
                            'autoreload_on' : True,
                            })
    print "BOOTING UP..........", ".."*12 
    cherrypy.quickstart(Annelia())
    #cherrypy.engine.start()
    
    #cherrypy.tree.mount(Annelia()) 
    #cherrypy.process.plugins.Daemonizer(cherrypy.engine).subscribe()    
    #cherrypy.root = Annelia()              
    #annelie = Daemonizer(cherrypy.engine)
    #annelie.subscribe()
    #annelie.start()
    #cherrypy.quickstart(Annelia())
    #cherrypy.engine.block() 
    
    #cherrypy.engine.start()
    #cherrypy.engine.block()
    
