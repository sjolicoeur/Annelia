try:
    from io import UnsupportedOperation
except ImportError:
    UnsupportedOperation = object()
import logging
import mimetypes
mimetypes.init()
mimetypes.types_map['.dwg']='image/x-dwg'
mimetypes.types_map['.ico']='image/x-icon'
mimetypes.types_map['.bz2']='application/x-bzip2'
mimetypes.types_map['.gz']='application/x-gzip'

import os
import re
import stat
import time

import cherrypy
from cherrypy._cpcompat import ntob, unquote
from cherrypy.lib import cptools, httputil, file_generator_limited
from cherrypy.lib.static import _serve_fileobj

def serve_file(path, content_type=None, disposition=None, name=None, content_length=None,debug=False):
    """Set status, headers, and body in order to serve the given path.
    
    The Content-Type header will be set to the content_type arg, if provided.
    If not provided, the Content-Type will be guessed by the file extension
    of the 'path' argument.
    
    If disposition is not None, the Content-Disposition header will be set
    to "<disposition>; filename=<name>". If name is None, it will be set
    to the basename of path. If disposition is None, no Content-Disposition
    header will be written.
    """
    
    response = cherrypy.serving.response
    
    # If path is relative, users should fix it by making path absolute.
    # That is, CherryPy should not guess where the application root is.
    # It certainly should *not* use cwd (since CP may be invoked from a
    # variety of paths). If using tools.staticdir, you can make your relative
    # paths become absolute by supplying a value for "tools.staticdir.root".
    if not os.path.isabs(path):
        msg = "'%s' is not an absolute path." % path
        if debug:
            cherrypy.log(msg, 'TOOLS.STATICFILE')
        raise ValueError(msg)
    
    try:
        st = os.stat(path)
    except OSError:
        if debug:
            cherrypy.log('os.stat(%r) failed' % path, 'TOOLS.STATIC')
        raise cherrypy.NotFound()
    
    # Check if path is a directory.
    if stat.S_ISDIR(st.st_mode):
        # Let the caller deal with it as they like.
        if debug:
            cherrypy.log('%r is a directory' % path, 'TOOLS.STATIC')
        raise cherrypy.NotFound()
    
    # Set the Last-Modified response header, so that
    # modified-since validation code can work.
    response.headers['Last-Modified'] = httputil.HTTPDate(st.st_mtime)
    cptools.validate_since()
    
    if content_type is None:
        # Set content-type based on filename extension
        ext = ""
        i = path.rfind('.')
        if i != -1:
            ext = path[i:].lower()
        content_type = mimetypes.types_map.get(ext, None)
    if content_type is not None:
        response.headers['Content-Type'] = content_type
    if debug:
        cherrypy.log('Content-Type: %r' % content_type, 'TOOLS.STATIC')
    
    cd = None
    if disposition is not None:
        if name is None:
            name = os.path.basename(path)
        cd = '%s; filename="%s"' % (disposition, name)
        response.headers["Content-Disposition"] = cd
    if debug:
        cherrypy.log('Content-Disposition: %r' % cd, 'TOOLS.STATIC')
    
    # Set Content-Length and use an iterable (file object)
    #   this way CP won't load the whole file in memory
    if not content_length :
        content_length = st.st_size
    fileobj = open(path, 'rb')
    return _serve_fileobj(fileobj, content_type, content_length, debug=debug)