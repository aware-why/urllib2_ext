import sys, os
import socket
import urllib, urllib2, cookielib

from urllib2_file import new_httphandler

tmp = os.path.join(os.path.dirname(__file__), 'tests')
sys.path.insert(0, tmp)
import testHTTPServer

class HTTPClient(object):
    default_encode = "utf-8"
    def __init__(self, cookie = False, encode = "utf-8"):
        if cookie:
            self.cookie = cookielib.MozillaCookieJar(str(cookie))
        else:
            self.cookie = False
        self.request = None
        self.encode = encode

        ## Whether to use custome opener to post multipart/form-data
        self.use_new_httphandler = False  
        self.extra_handlers = []
                
    def get(self, url, headers=False):
        self.request = urllib2.Request(url)
        self._before(headers, self.cookie);
        resp = urllib2.urlopen(self.request)
        return self._after(resp)

    # Generally, post data is string or tuple 
    # post file if data is dict
    # example:data = {'form_name':{ 'fd':open('/lib/libresolv.so.2','filename':'libresolv.so'}}            
    def post(self, url, data, headers={}):
        if isinstance(data, dict):
            self.use_new_httphandler = True
 
        self._before(headers=headers, cookie=self.cookie);

        if self.use_new_httphandler:
            self.extra_handlers.append(new_httphandler)
        else:
            pass
        self.request = urllib2.Request(url, headers=headers)
        opener = urllib2.build_opener(*self.extra_handlers)    
        resp = opener.open(self.request, data)
                
        self.use_new_httphandler = False
        self.extra_handlers = []
        
        return self._after(resp)
    
    def _before(self, headers = False, cookie = False):
        if cookie != False:
            self._handle_cookie(cookie)
        if headers != False:
            self._handle_header(headers)
            
    def _after(self, resp):
        if self.cookie:
            self.cookie.save(ignore_discard = True, ignore_expires = True)
        
        res = resp.read()
        if self.encode != HTTPClient.default_encode:
            return res.decode(self.encode, HTTPClient.default_encode)
        return res
    
    def _handle_cookie(self, cookie):
        self.extra_handlers.append(urllib2.HTTPCookieProcessor(cookie))
                                   
    def _handle_header(self, headers):
        for (k,v) in headers.items():
            self.request.add_header(k, v)


if __name__ == '__main__':
    # start http server
    listen_port_start = 32800
    for listen_port in range(listen_port_start, listen_port_start + 10):
        # print "trying to bind on port %s" % listen_port
        httpd = testHTTPServer.testHTTPServer('127.0.0.1', listen_port, )
        try:
            httpd.listen()
            break
        except socket.error, (errno, strerr):
            # already in use
            if errno == 98:
                continue
            else:
                print "ERROR: listen: ", errno, strerr 
                sys.exit(-1)
    print "http server bound to port", listen_port
    httpd.start()

    httpserver = 'http://127.0.0.1:%s' % listen_port
    while not httpd.isReady():
        time.sleep(0.1)
    u = urllib2.urlopen(httpserver + '/ping') 
    data = u.read()
    if data != "pong":
        print "error"
        sys.exit(-1)

    client = HTTPClient(cookie=True)
    post_data1 = {'file1': {'filename': 'file1_name',
                           'fd': open('/bin/ls')}
                 }
    ret = client.post(httpserver, post_data1)
    print ret

    post_data2 = 'Text to be posted'
    ret = client.post(httpserver, post_data2,
                      headers={'Content-Type' : 'binary'})
    ret = client.post(httpserver, post_data2,
                      headers={'Content-Type' : 'text/html'})
    print ret

    post_data3 = 'var1=value1;var2=value2'
    ret = client.post(httpserver, post_data3)
    print ret

    httpd.die()
    httpd.join()
    print "http server stopped"
    
    
   
