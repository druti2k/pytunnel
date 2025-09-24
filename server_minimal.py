#!/usr/bin/env python3
"""
Minimal PyTunnel Server for Render.com
Absolute minimum implementation
"""

import os
import sys
from aiohttp import web, WSMsgType
import json
import time

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

async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    client_id = None
    tunnel_id = None
    
    try:
        print(f"New WebSocket connection from {request.remote}")
        
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    msg_type = data.get('type')
                    
                    if msg_type == 'connect':
                        subdomain = data.get('subdomain')
                        client_id = data.get('client_id', f"client_{int(time.time())}")
                        
                        tunnel_id = create_tunnel(client_id, subdomain)
                        await ws.send_json({
                            'type': 'connected',
                            'tunnel_id': tunnel_id,
                            'subdomain': tunnels[tunnel_id]['subdomain'],
                            'status': 'active'
                        })
                        print(f"Client {client_id} connected with tunnel {tunnel_id}")
                        
                    elif msg_type == 'heartbeat':
                        await ws.send_json({'type': 'heartbeat_ack'})
                        
                    elif msg_type == 'disconnect':
                        if tunnel_id:
                            remove_tunnel(tunnel_id)
                        break
                        
                except json.JSONDecodeError:
                    await ws.send_json({'type': 'error', 'message': 'Invalid JSON'})
                    
            elif msg.type == WSMsgType.ERROR:
                print(f"WebSocket error: {ws.exception()}")
                break
                
    except Exception as e:
        print(f"WebSocket handler error: {e}")
        
    finally:
        if tunnel_id:
            remove_tunnel(tunnel_id)
        print(f"WebSocket connection closed for {client_id}")
        return ws

async def http_handler(request):
    path = request.path.lstrip('/')
    
    if not path:
        return web.Response(
            text=f"""
            <html>
            <head><title>PyTunnel Server</title></head>
            <body>
                <h1>🚀 PyTunnel Server</h1>
                <p>Status: Running</p>
                <p>Active Tunnels: {len(tunnels)}</p>
                <hr>
                <h2>Active Tunnels:</h2>
                <ul>
                    {''.join([f'<li>{tunnel_id}: {tunnel["subdomain"]}</li>' for tunnel_id, tunnel in tunnels.items()])}
                </ul>
            </body>
            </html>
            """,
            content_type='text/html'
        )
    
    subdomain = path.split('/')[0]
    tunnel_id = None
    tunnel = None
    
    for tid, t in tunnels.items():
        if t['subdomain'] == subdomain:
            tunnel_id = tid
            tunnel = t
            break
    
    if not tunnel:
        return web.Response(
            status=404,
            text=f"Tunnel '{subdomain}' not found"
        )
    
    return web.Response(
        text=f"Tunnel '{subdomain}' is active. Client: {tunnel['client_id']}",
        content_type='text/plain'
    )

async def health_handler(request):
    print(f"Health check requested from {request.remote}")
    response_text = f"OK\nPyTunnel Server Running\nPort: {os.getenv('PORT', '8081')}\nActive Tunnels: {len(tunnels)}\nTimestamp: {time.time()}"
    return web.Response(
        text=response_text,
        content_type='text/plain',
        status=200
    )

def main():
    print("=== PyTunnel Server Starting ===")
    print(f"Python version: {sys.version}")
    
    port = int(os.getenv('PORT', 8081))
    print(f"Using port: {port}")
    print(f"Environment PORT: {os.getenv('PORT', 'not set')}")
    
    app = web.Application()
    
    app.router.add_get('/health', health_handler)
    app.router.add_get('/test', lambda r: web.Response(text="Test endpoint working!", content_type='text/plain'))
    app.router.add_get('/ws', websocket_handler)
    app.router.add_get('/', http_handler)
    app.router.add_route('*', '/{path:.*}', http_handler)
    
    print(f"Starting PyTunnel server on port {port}")
    print(f"WebSocket endpoint: ws://0.0.0.0:{port}/ws")
    print(f"Health check: http://0.0.0.0:{port}/health")
    
    try:
        web.run_app(app, host='0.0.0.0', port=port)
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
