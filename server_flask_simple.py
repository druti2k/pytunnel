#!/usr/bin/env python3
"""
Flask-based PyTunnel Server for Render.com
Simple and reliable implementation
"""

import os
import sys
import json
import time
from flask import Flask, request, jsonify, render_template_string

app = Flask(__name__)

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

@app.route('/health')
def health():
    print(f"Health check requested from {request.remote_addr}")
    response_text = f"OK\nPyTunnel Server Running\nPort: {os.getenv('PORT', '8081')}\nActive Tunnels: {len(tunnels)}\nTimestamp: {time.time()}"
    return response_text, 200

@app.route('/test')
def test():
    return "Test endpoint working!", 200

@app.route('/')
def index():
    tunnels_html = ''.join([f'<li>{tunnel_id}: {tunnel["subdomain"]}</li>' for tunnel_id, tunnel in tunnels.items()])
    
    return render_template_string("""
    <html>
    <head><title>PyTunnel Server</title></head>
    <body>
        <h1>🚀 PyTunnel Server</h1>
        <p>Status: Running</p>
        <p>Active Tunnels: {{ tunnels_count }}</p>
        <hr>
        <h2>Active Tunnels:</h2>
        <ul>
            {{ tunnels_html|safe }}
        </ul>
    </body>
    </html>
    """, tunnels_html=tunnels_html, tunnels_count=len(tunnels))

@app.route('/<path:subdomain>')
def tunnel_handler(subdomain):
    tunnel_id = None
    tunnel = None
    
    for tid, t in tunnels.items():
        if t['subdomain'] == subdomain:
            tunnel_id = tid
            tunnel = t
            break
    
    if not tunnel:
        return f"Tunnel '{subdomain}' not found", 404
    
    return f"Tunnel '{subdomain}' is active. Client: {tunnel['client_id']}", 200

@app.route('/api/tunnels', methods=['POST'])
def create_tunnel_api():
    try:
        data = request.get_json()
        subdomain = data.get('subdomain')
        client_id = data.get('client_id', f"client_{int(time.time())}")
        
        tunnel_id = create_tunnel(client_id, subdomain)
        return jsonify({
            'tunnel_id': tunnel_id,
            'subdomain': tunnels[tunnel_id]['subdomain'],
            'status': 'active'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/api/tunnels/<tunnel_id>', methods=['DELETE'])
def delete_tunnel_api(tunnel_id):
    try:
        remove_tunnel(tunnel_id)
        return jsonify({'message': 'Tunnel deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

def main():
    print("=== PyTunnel Flask Server Starting ===")
    print(f"Python version: {sys.version}")
    
    port = int(os.getenv('PORT', 8081))
    print(f"Using port: {port}")
    print(f"Environment PORT: {os.getenv('PORT', 'not set')}")
    
    print(f"Starting PyTunnel server on port {port}")
    print(f"Health check: http://0.0.0.0:{port}/health")
    print(f"Test endpoint: http://0.0.0.0:{port}/test")
    
    try:
        app.run(host='0.0.0.0', port=port, debug=False)
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
