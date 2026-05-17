#!/usr/bin/env python3
"""Simple HTTP server for EV control UI"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json

JSON_FILE = "/tmp/ev_ui_values.json"

class Handler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.path = '/ui.html'
        
        if self.path.endswith('.html'):
            try:
                with open(self.path[1:], 'rb') as f:
                    self.send_response(200)
                    self.send_header('Content-type', 'text/html')
                    self.end_headers()
                    self.wfile.write(f.read())
            except:
                self.send_error(404)
        
        elif self.path == '/values':
            try:
                with open(JSON_FILE, 'r') as f:
                    data = json.load(f)
            except:
                data = {"soc": 10, "target_soc": 80, "departure_time_hours": 2, 
                       "max_current": 200, "max_power": 50, "bpt_enabled": False}
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode())
    
    def do_POST(self):
        if self.path == '/update':
            length = int(self.headers['Content-Length'])
            data = json.loads(self.rfile.read(length))
            
            try:
                with open(JSON_FILE, 'r') as f:
                    current = json.load(f)
            except:
                current = {}
            
            current.update(data)
            
            with open(JSON_FILE, 'w') as f:
                json.dump(current, f, indent=2)
            
            print(f"✅ UI updated: SOC={current.get('soc', '?')}%")
            
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b'OK')

print("="*50)
print("UI Server running at http://localhost:8000")
print("="*50)
HTTPServer(("0.0.0.0", 8000), Handler).serve_forever()