#!/usr/bin/env python3
"""
Ultra-minimal PyTunnel Server using Python's built-in HTTP server
Maximum compatibility for Render.com
"""

import os
import sys
import json
import time
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import socketserver

# Global state
tunnels = {}
tunnel_counter = 0

def create_tunnel(client_id, subdomain=None):
    global tunnel_counter
    tunnel_counter += 1
    if not subdomain:
        subdomain = f"tunnel{tunnel_counter:03d}"
    tunnel_id = f"{subdomain}_{client_id[:8]}"
    tunnels[tunnel_id] = {
        'client_id': client_id,
        'subdomain': subdomain,
        'created_at': time.time(),
        'status': 'active'
    }
    print(f"Created tunnel: {tunnel_id}")
    return tunnel_id

def remove_tunnel(tunnel_id):
    if tunnel_id in tunnels:
        del tunnels[tunnel_id]
        print(f"Removed tunnel: {tunnel_id}")

class PyTunnelHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            parsed_path = urlparse(self.path)
            path = parsed_path.path.lstrip('/')
            
            if path == 'health':
                self.send_health_response()
            elif path == 'test':
                self.send_test_response()
            elif path == '':
                self.send_root_response()
            else:
                self.send_tunnel_response(path)
                
        except Exception as e:
            print(f"Error handling request: {e}")
            self.send_error(500, str(e))
    
    def send_health_response(self):
        print(f"Health check requested from {self.client_address[0]}")
        response_text = f"OK\nPyTunnel Server Running\nPort: {os.getenv('PORT', '8081')}\nActive Tunnels: {len(tunnels)}\nTimestamp: {time.time()}"
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(response_text.encode())
    
    def send_test_response(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"Test endpoint working!")
    
    def send_root_response(self):
        tunnels_html = ''.join([f'<li>{tunnel_id}: {tunnel["subdomain"]}</li>' for tunnel_id, tunnel in tunnels.items()])
        
        html = f"""
        <html>
        <head><title>PyTunnel Server</title></head>
        <body>
            <h1>🚀 PyTunnel Server</h1>
            <p>Status: Running</p>
            <p>Active Tunnels: {len(tunnels)}</p>
            <hr>
            <h2>Active Tunnels:</h2>
            <ul>
                {tunnels_html}
            </ul>
        </body>
        </html>
        """
        
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(html.encode())
    
    def send_tunnel_response(self, subdomain):
        tunnel_id = None
        tunnel = None
        
        for tid, t in tunnels.items():
            if t['subdomain'] == subdomain:
                tunnel_id = tid
                tunnel = t
                break
        
        if not tunnel:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Tunnel '{subdomain}' not found".encode())
            return
        
        response_text = f"Tunnel '{subdomain}' is active. Client: {tunnel['client_id']}"
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(response_text.encode())
    
    def log_message(self, format, *args):
        # Suppress default logging
        pass

class ThreadedHTTPServer(socketserver.ThreadingMixIn, HTTPServer):
    """Handle requests in a separate thread."""
    pass

def main():
    print("=== PyTunnel Built-in HTTP Server Starting ===")
    print(f"Python version: {sys.version}")
    
    port = int(os.getenv('PORT', 8081))
    print(f"Using port: {port}")
    print(f"Environment PORT: {os.getenv('PORT', 'not set')}")
    
    print(f"Starting PyTunnel server on port {port}")
    print(f"Health check: http://0.0.0.0:{port}/health")
    print(f"Test endpoint: http://0.0.0.0:{port}/test")
    
    try:
        server = ThreadedHTTPServer(('0.0.0.0', port), PyTunnelHandler)
        print(f"Server running on http://0.0.0.0:{port}")
        server.serve_forever()
    except Exception as e:
        print(f"Failed to start server: {e}")
        raise

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("Server stopped by user")
    except Exception as e:
        print(f"Server error: {e}")
        sys.exit(1)
