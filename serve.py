import os, http.server, socketserver
os.chdir("/Users/rhett.nicholas/Desktop/ACN-AI-News2You")
handler = http.server.SimpleHTTPRequestHandler
with socketserver.TCPServer(("", 8765), handler) as httpd:
    httpd.serve_forever()
