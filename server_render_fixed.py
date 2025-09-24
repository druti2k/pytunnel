#!/usr/bin/env python3
"""
Ultra-Simple PyTunnel Server for Render.com
Maximum compatibility version
"""

import os
import sys
import logging
from aiohttp import web, WSMsgType
import json
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global state
tunnels = {}
tunnel_counter = 0
MAX_CONNECTIONS = 100

def create_tunnel(client_id, subdomain=None):
    """Create a new tunnel"""
    global tunnel_counter
    if len(tunnels) >= MAX_CONNECTIONS:
        raise Exception("Maximum connections reached")
        
    tunnel_counter += 1
    if not subdomain:
        subdomain = f"tunnel{tunnel_counter:03d}"
        
    tunnel_id = f"{subdomain}_{client_id[:8]}"
    
    tunnels[tunnel_id] = {
        'client_id': client_id,
        'subdomain': subdomain,
        'created_at': time.time(),
        'last_activity': time.time(),
        'status': 'active'
    }
    
    logger.info(f"Created tunnel: {tunnel_id}")
    return tunnel_id

def remove_tunnel(tunnel_id):
    """Remove a tunnel"""
    if tunnel_id in tunnels:
        del tunnels[tunnel_id]
        logger.info(f"Removed tunnel: {tunnel_id}")

def get_tunnel(subdomain):
    """Get tunnel by subdomain"""
    for tunnel_id, tunnel in tunnels.items():
        if tunnel['subdomain'] == subdomain:
            return tunnel_id, tunnel
    return None, None

async def websocket_handler(request):
    """Handle WebSocket connections"""
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    client_id = None
    tunnel_id = None
    
    try:
        logger.info(f"New WebSocket connection from {request.remote}")
        
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                try:
                    data = json.loads(msg.data)
                    msg_type = data.get('type')
                    
                    if msg_type == 'connect':
                        subdomain = data.get('subdomain')
                        client_id = data.get('client_id', f"client_{int(time.time())}")
                        
                        try:
                            tunnel_id = create_tunnel(client_id, subdomain)
                            await ws.send_json({
                                'type': 'connected',
                                'tunnel_id': tunnel_id,
                                'subdomain': tunnels[tunnel_id]['subdomain'],
                                'status': 'active'
                            })
                            logger.info(f"Client {client_id} connected with tunnel {tunnel_id}")
                            
                        except Exception as e:
                            await ws.send_json({
                                'type': 'error',
                                'message': str(e)
                            })
                            logger.error(f"Failed to create tunnel: {e}")
                            
                    elif msg_type == 'heartbeat':
                        if tunnel_id:
                            tunnels[tunnel_id]['last_activity'] = time.time()
                            await ws.send_json({'type': 'heartbeat_ack'})
                            
                    elif msg_type == 'disconnect':
                        if tunnel_id:
                            remove_tunnel(tunnel_id)
                        break
                        
                except json.JSONDecodeError:
                    await ws.send_json({'type': 'error', 'message': 'Invalid JSON'})
                    
            elif msg.type == WSMsgType.ERROR:
                logger.error(f"WebSocket error: {ws.exception()}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket handler error: {e}")
        
    finally:
        if tunnel_id:
            remove_tunnel(tunnel_id)
        logger.info(f"WebSocket connection closed for {client_id}")
        return ws

async def http_handler(request):
    """Handle HTTP requests"""
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
                <p>Max Connections: {MAX_CONNECTIONS}</p>
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
    tunnel_id, tunnel = get_tunnel(subdomain)
    
    if not tunnel:
        return web.Response(
            status=404,
            text=f"Tunnel '{subdomain}' not found. Available tunnels: {list(tunnels.keys())}"
        )
    
    tunnel['last_activity'] = time.time()
    
    return web.Response(
        text=f"Tunnel '{subdomain}' is active. Client: {tunnel['client_id']}",
        content_type='text/plain'
    )

async def health_handler(request):
    """Health check endpoint"""
    logger.info(f"Health check requested from {request.remote}")
    response_text = f"OK\nPyTunnel Server Running\nPort: {os.getenv('PORT', '8081')}\nActive Tunnels: {len(tunnels)}\nTimestamp: {time.time()}"
    return web.Response(
        text=response_text,
        content_type='text/plain',
        status=200
    )

def main():
    """Main application entry point"""
    logger.info("=== PyTunnel Server Starting ===")
    logger.info(f"Python version: {sys.version}")
    
    # Get port from environment
    port = int(os.getenv('PORT', 8081))
    logger.info(f"Using port: {port}")
    logger.info(f"Environment PORT: {os.getenv('PORT', 'not set')}")
    
    # Create app
    app = web.Application()
    
    # Add routes
    app.router.add_get('/health', health_handler)
    app.router.add_get('/test', lambda r: web.Response(text="Test endpoint working!", content_type='text/plain'))
    app.router.add_get('/ws', websocket_handler)
    app.router.add_get('/', http_handler)
    app.router.add_route('*', '/{path:.*}', http_handler)
    
    logger.info(f"Starting PyTunnel server on port {port}")
    logger.info(f"Max connections: {MAX_CONNECTIONS}")
    logger.info(f"WebSocket endpoint: ws://0.0.0.0:{port}/ws")
    logger.info(f"Health check: http://0.0.0.0:{port}/health")
    
    # Start server
    try:
        web.run_app(app, host='0.0.0.0', port=port, access_log=logger)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
