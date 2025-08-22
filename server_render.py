#!/usr/bin/env python3
"""
PyTunnel Server - Render.com Optimized Version
Simplified for Render's free tier with WebSocket support
"""

import asyncio
import logging
import os
import signal
import sys
from aiohttp import web, WSMsgType
from aiohttp.web import WebSocketResponse
import json
import time
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=getattr(logging, os.getenv('LOG_LEVEL', 'INFO')),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global state
tunnels = {}
tunnel_counter = 0
MAX_CONNECTIONS = int(os.getenv('MAX_CONNECTIONS', 100))
HEARTBEAT_INTERVAL = int(os.getenv('HEARTBEAT_INTERVAL', 30))
CONNECTION_TIMEOUT = int(os.getenv('CONNECTION_TIMEOUT', 300))

class TunnelManager:
    def __init__(self):
        self.tunnels = {}
        self.counter = 0
        
    def create_tunnel(self, client_id, subdomain=None):
        """Create a new tunnel"""
        if len(self.tunnels) >= MAX_CONNECTIONS:
            raise Exception("Maximum connections reached")
            
        self.counter += 1
        if not subdomain:
            subdomain = f"tunnel{self.counter:03d}"
            
        tunnel_id = f"{subdomain}_{client_id[:8]}"
        
        self.tunnels[tunnel_id] = {
            'client_id': client_id,
            'subdomain': subdomain,
            'created_at': time.time(),
            'last_activity': time.time(),
            'status': 'active'
        }
        
        logger.info(f"Created tunnel: {tunnel_id}")
        return tunnel_id
        
    def remove_tunnel(self, tunnel_id):
        """Remove a tunnel"""
        if tunnel_id in self.tunnels:
            del self.tunnels[tunnel_id]
            logger.info(f"Removed tunnel: {tunnel_id}")
            
    def get_tunnel(self, subdomain):
        """Get tunnel by subdomain"""
        for tunnel_id, tunnel in self.tunnels.items():
            if tunnel['subdomain'] == subdomain:
                return tunnel_id, tunnel
        return None, None

tunnel_manager = TunnelManager()

async def websocket_handler(request):
    """Handle WebSocket connections for tunnel clients"""
    ws = WebSocketResponse()
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
                        # Client wants to create a tunnel
                        subdomain = data.get('subdomain')
                        client_id = data.get('client_id', f"client_{int(time.time())}")
                        
                        try:
                            tunnel_id = tunnel_manager.create_tunnel(client_id, subdomain)
                            await ws.send_json({
                                'type': 'connected',
                                'tunnel_id': tunnel_id,
                                'subdomain': tunnel_manager.tunnels[tunnel_id]['subdomain'],
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
                        # Client heartbeat
                        if tunnel_id:
                            tunnel_manager.tunnels[tunnel_id]['last_activity'] = time.time()
                            await ws.send_json({'type': 'heartbeat_ack'})
                            
                    elif msg_type == 'disconnect':
                        # Client disconnecting
                        if tunnel_id:
                            tunnel_manager.remove_tunnel(tunnel_id)
                        break
                        
                except json.JSONDecodeError:
                    await ws.send_json({'type': 'error', 'message': 'Invalid JSON'})
                    
            elif msg.type == WSMsgType.ERROR:
                logger.error(f"WebSocket error: {ws.exception()}")
                break
                
    except Exception as e:
        logger.error(f"WebSocket handler error: {e}")
        
    finally:
        # Cleanup
        if tunnel_id:
            tunnel_manager.remove_tunnel(tunnel_id)
        logger.info(f"WebSocket connection closed for {client_id}")
        return ws

async def http_handler(request):
    """Handle HTTP requests to tunnels"""
    path = request.path.lstrip('/')
    
    if not path:
        # Root path - show tunnel status
        return web.Response(
            text=f"""
            <html>
            <head><title>PyTunnel Server</title></head>
            <body>
                <h1>🚀 PyTunnel Server</h1>
                <p>Status: Running</p>
                <p>Active Tunnels: {len(tunnel_manager.tunnels)}</p>
                <p>Max Connections: {MAX_CONNECTIONS}</p>
                <hr>
                <h2>Active Tunnels:</h2>
                <ul>
                    {''.join([f'<li>{tunnel_id}: {tunnel["subdomain"]}</li>' for tunnel_id, tunnel in tunnel_manager.tunnels.items()])}
                </ul>
            </body>
            </html>
            """,
            content_type='text/html'
        )
    
    # Check if this is a tunnel request
    subdomain = path.split('/')[0]
    tunnel_id, tunnel = tunnel_manager.get_tunnel(subdomain)
    
    if not tunnel:
        return web.Response(
            status=404,
            text=f"Tunnel '{subdomain}' not found. Available tunnels: {list(tunnel_manager.tunnels.keys())}"
        )
    
    # Update last activity
    tunnel['last_activity'] = time.time()
    
    # For now, return a simple response
    # In a full implementation, this would proxy to the client
    return web.Response(
        text=f"Tunnel '{subdomain}' is active. Client: {tunnel['client_id']}",
        content_type='text/plain'
    )

async def health_handler(request):
    """Health check endpoint for Render"""
    logger.info(f"Health check requested from {request.remote}")
    response_text = f"OK\nPyTunnel Server Running\nPort: {os.getenv('PORT', '8081')}\nActive Tunnels: {len(tunnel_manager.tunnels)}\nTimestamp: {time.time()}"
    logger.info(f"Health check response: {response_text}")
    return web.Response(
        text=response_text,
        content_type='text/plain',
        status=200
    )

async def cleanup_old_tunnels():
    """Clean up inactive tunnels"""
    while True:
        try:
            current_time = time.time()
            to_remove = []
            
            for tunnel_id, tunnel in tunnel_manager.tunnels.items():
                if current_time - tunnel['last_activity'] > CONNECTION_TIMEOUT:
                    to_remove.append(tunnel_id)
                    
            for tunnel_id in to_remove:
                tunnel_manager.remove_tunnel(tunnel_id)
                
            if to_remove:
                logger.info(f"Cleaned up {len(to_remove)} inactive tunnels")
                
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
            
        await asyncio.sleep(60)  # Run every minute

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    logger.info("Shutting down PyTunnel server...")
    sys.exit(0)

async def main():
    """Main application entry point"""
    logger.info("=== PyTunnel Server Starting ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Environment PORT: {os.getenv('PORT', 'not set')}")
    logger.info(f"Environment LOG_LEVEL: {os.getenv('LOG_LEVEL', 'INFO')}")
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create web application
    app = web.Application()
    
    # Add routes - order matters!
    app.router.add_get('/health', health_handler)
    app.router.add_get('/test', lambda r: web.Response(text="Test endpoint working!", content_type='text/plain'))
    app.router.add_get('/ws', websocket_handler)
    app.router.add_get('/', http_handler)  # Root path
    app.router.add_route('*', '/{path:.*}', http_handler)  # Catch-all for tunnels
    
    # Start cleanup task
    asyncio.create_task(cleanup_old_tunnels())
    
    # Get port from environment (Render sets PORT)
    port = int(os.getenv('PORT', 8081))
    
    # Log the port being used
    logger.info(f"Using port: {port} (from environment: {os.getenv('PORT', 'not set')})")
    
    logger.info(f"Starting PyTunnel server on port {port}")
    logger.info(f"Max connections: {MAX_CONNECTIONS}")
    logger.info(f"WebSocket endpoint: ws://0.0.0.0:{port}/ws")
    logger.info(f"Health check: http://0.0.0.0:{port}/health")
    
    # Start server
    try:
        runner = web.AppRunner(app)
        await runner.setup()
        
        site = web.TCPSite(runner, '0.0.0.0', port)
        await site.start()
        
        logger.info(f"PyTunnel server is running on port {port}")
        logger.info(f"Server bound to 0.0.0.0:{port}")
        logger.info(f"Health check available at: http://0.0.0.0:{port}/health")
        
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        raise
    
    # Keep server running
    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        pass
    finally:
        await runner.cleanup()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)
