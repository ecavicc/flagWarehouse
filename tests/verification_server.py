import http.server
import random
import socketserver

PORT = 8000


class ServerHandler(http.server.BaseHTTPRequestHandler):
    def do_PUT(self):
        body = random.choices(
            population=['accepted\n', 'invalid\n', 'too old', 'is not available'],
            weights=(1, 0.1),
            k=1
        )[0]
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(bytes(body, 'utf-8'))


handler = ServerHandler

httpd = socketserver.TCPServer(("", PORT), handler)

print("Serving at port", PORT)
httpd.serve_forever()
