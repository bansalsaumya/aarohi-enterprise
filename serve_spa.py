import http.server
import socketserver
import os
import posixpath
import urllib

PORT = 8080
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class SPAHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

    def do_GET(self):
        clean_path = self.path.split('?')[0].split('#')[0]
        full_path = os.path.join(DIRECTORY, clean_path.lstrip('/\\').replace('/', os.sep))
        
        # If it matches an actual file, serve it directly
        if os.path.isfile(full_path):
            return super().do_GET()
            
        # Check if requested path has a file extension like .webp, .jpg, .png, .css, .js
        _, ext = os.path.splitext(clean_path)
        if ext and not os.path.isfile(full_path):
            self.send_error(404, f"File not found: {clean_path}")
            return

        # Otherwise fallback to index.html for Single Page Application client-side routing
        self.path = '/index.html'
        return super().do_GET()

socketserver.TCPServer.allow_reuse_address = True
with socketserver.TCPServer(("", PORT), SPAHandler) as httpd:
    print(f"Serving SPA correctly at http://localhost:{PORT}")
    httpd.serve_forever()
