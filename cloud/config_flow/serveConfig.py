import os
import json
import requests
import sys

import http.server
import socketserver

# serveConfig.py port localhost configFilePath

class HTTPrequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = sys.argv[2]  
        return http.server.SimpleHTTPRequestHandler.do_GET(self)

# Create an object of the above class
handler_object = HTTPrequestHandler

# if len(sys.argv) <= 2:
# 	HOST = ""
# else:
# HOST = str(sys.argv[2])
PORT = int(sys.argv[1])
my_server = socketserver.TCPServer(("", PORT), handler_object)

# Star the server
my_server.serve_forever()
