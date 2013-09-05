#!/usr/bin/env python

import BaseHTTPServer
import cgi
import select
import socket
import sys
import threading
import time
import urlparse

class testHTTPHandler (BaseHTTPServer.BaseHTTPRequestHandler):
    """ disable printing log access """
    def log_request(self, format, *args):
        pass

    def do_GET(self):
        if self.path == "/ping":
            self.send_response(200, "OK")
            self.end_headers()
            self.wfile.write("pong")
            return

        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.end_headers()

        u_split = urlparse.urlsplit(self.path)
        q_split = cgi.parse_qsl(u_split[3])

        for key, value in (q_split):
            self.wfile.write("GET_VAR name=%s value=%s <br/>\n" % (key, value))

    def do_POST(self):
        if not self.headers.has_key("Content-Type"):
            self.send_response(500)
            self.end_headers()
            self.wfile.write("Needs Content-Type\n")
            return
        
        if self.headers['Content-Type'].find('form') == -1:
            self.send_response(200)
            self.end_headers()
            varLen = int(self.headers['Content-Length'])
            postVars = self.rfile.read(varLen)
            self.wfile.write('POST_%s length=%s\n' % (self.headers['Content-Type'], varLen))
            return
                         
        form = cgi.FieldStorage(fp = self.rfile,
                                headers = self.headers,
                                environ = {'REQUEST_METHOD':    'POST',
                                           'CONTENT_TYPE':      self.headers['Content-Type']}
                                )
        if len(form) == 0:
            self.send_response(200)
            self.end_headers()
            self.wfile.write("NO_FORM_DATA found\n")
            return
         
        self.send_response(200)
        self.end_headers()
        for field in form.keys():
            if form[field].filename:
                self.wfile.write("POST_FILE name=%s filename=%s length=%d <br/>\n"  % (field, form[field].filename, len(form[field].file.read())))
            else:
                self.wfile.write("POST_VAR name=%s value=%s <br/>\n" % (field, form[field].value) )
 
class testHTTPServer(threading.Thread):
    def __init__(self, host, port):
        threading.Thread.__init__(self)

        self.host_port = (host, port)
        self.must_die = False
        self.is_ready = False

    def listen(self):
        self.httpd = BaseHTTPServer.HTTPServer(self.host_port, testHTTPHandler)

    def run(self):
        self.is_ready = True 
        while not self.must_die:
            result = select.select([self.httpd.socket.fileno()], [], [], 1)
            if self.httpd.socket.fileno() in result[0]:
                self.httpd.handle_request()

    def die(self):
        self.must_die = True

    def isReady(self):
        return self.is_ready

httpd = None
def main():
    global httpd

    import signal
    import traceback
    def receive_signal(signum, stack):
        print '[main] Received signal:', signum
        print '[main] Current stack:'
        traceback.print_stack(stack)

        httpd.die()
        httpd.join()
        sys.exit(0)

    
    signal.signal(signal.SIGINT, receive_signal)
    
    listen_port_start = 32800
    for listen_port in range(listen_port_start, listen_port_start + 2):
        print "[main] trying to bind on port %s" % listen_port
        httpd = testHTTPServer('127.0.0.1', listen_port, )
        try:
            httpd.listen()
            break
        except socket.error, (errno, strerr):
            # already in use
            print "ERROR: listen: ", errno, strerr 
            if errno == 98:
                continue
            else:
                print "ERROR: listen: ", errno, strerr 
                sys.exit(-1)

    httpd.start()
    print "[main] started on port", listen_port
    try:
        time.sleep(9999999.)
        print '[main] Time is up'
    except KeyboardInterrupt:
        print '[main] Keyboard Interrupt'
        pass
    httpd.die()
    httpd.join()

if __name__ == '__main__':
    main()
