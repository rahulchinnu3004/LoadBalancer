from http.server import HTTPServer, BaseHTTPRequestHandler
import sys

# Usage:
# python backend.py 8001 Server-1

PORT = int(sys.argv[1])
SERVER_NAME = sys.argv[2]

class MyHandler(BaseHTTPRequestHandler):
    def do_GET(self):

        response = f"Hello from {SERVER_NAME} 1"
        self.send_response(200)
        self.send_header("Content-Type", "text/plain")
        self.send_header("Server", SERVER_NAME)
        self.send_header("Content-length", str(len(response)))
        self.end_headers()
        self.wfile.write(response.encode())



    # Optional: suppress default request logging
    def log_message(self, format, *args):
        print(f"[{SERVER_NAME}] {self.address_string()} - {format % args}")

server = HTTPServer(("localhost", PORT), MyHandler)

print(f"{SERVER_NAME} running on http://localhost:{PORT}")

try:
    server.serve_forever()
except KeyboardInterrupt:
    print("\nShutting down...")
    server.server_close()