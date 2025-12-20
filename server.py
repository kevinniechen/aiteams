#!/usr/bin/env python3
"""
Simple server that serves static files and handles spam marking
"""

import http.server
import json
import os

SPAM_FILE = "spam.json"

def load_spam():
    if os.path.exists(SPAM_FILE):
        with open(SPAM_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_spam(data):
    with open(SPAM_FILE, 'w') as f:
        json.dump(data, f, indent=2)

class Handler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/spam.json':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            spam = load_spam()
            self.wfile.write(json.dumps(spam).encode())
        else:
            super().do_GET()
    
    def do_POST(self):
        if self.path == '/spam':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode())
            
            spam = load_spam()
            company = data.get('company')
            name = data.get('name')
            is_spam = data.get('is_spam', True)
            
            if company not in spam:
                spam[company] = []
            
            if is_spam and name not in spam[company]:
                spam[company].append(name)
            elif not is_spam and name in spam[company]:
                spam[company].remove(name)
            
            save_spam(spam)
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({'ok': True}).encode())
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    port = 8080
    print(f"Serving on http://localhost:{port}")
    http.server.HTTPServer(('', port), Handler).serve_forever()



