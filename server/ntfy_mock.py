# Stand-in for the ntfy bridge: receives Traccar's forwarded events and logs them.
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
class H(BaseHTTPRequestHandler):
    def do_POST(self):
        body = self.rfile.read(int(self.headers.get("Content-Length", 0)))
        open("/tmp/traccar/forwarded_events.jsonl", "ab").write(body + b"\n")
        self.send_response(200); self.end_headers()
    def log_message(self, *a): pass
HTTPServer(("127.0.0.1", 9999), H).serve_forever()
