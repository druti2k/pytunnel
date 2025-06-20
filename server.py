# server.py
import asyncio
import websockets
import os
import logging
import socket
from http import HTTPStatus
from aiohttp import web
from urllib.parse import urlparse
import json
import traceback
import random
import string
from collections import defaultdict

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more detailed logs
    format='%(asctime)s - %(levelname)s - %(message)s'
)

AUTH_TOKEN = os.getenv("AUTH_TOKEN", "mysecrettoken")
PUBLIC_HOST = os.getenv("PUBLIC_HOST", "localhost")  # Change this to your public IP/domain

# Store connected clients and their subdomains
tunnels = {}
subdomains = {}
# Store pending responses for each tunnel
pending_responses = defaultdict(dict)

def generate_subdomain():
    """Generate a random subdomain"""
    letters = string.ascii_lowercase + string.digits
    return ''.join(random.choice(letters) for _ in range(8))

def find_available_port(start_port=8081, max_port=8090):
    """Find an available port to bind to"""
    for port in range(start_port, max_port + 1):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(('0.0.0.0', port))  # Listen on all interfaces
                return port
        except OSError:
            continue
    raise OSError("No available ports found")

async def websocket_handler(websocket, path):
    """Handle WebSocket connections from clients"""
    # Generate a unique subdomain for this tunnel
    subdomain = generate_subdomain()
    while subdomain in subdomains:
        subdomain = generate_subdomain()
    
    logging.info(f"New tunnel connection: {subdomain}")
    tunnels[subdomain] = websocket
    subdomains[subdomain] = websocket
    
    # Send the subdomain to the client
    await websocket.send(json.dumps({
        'type': 'subdomain',
        'subdomain': subdomain
    }))
    
    try:
        async for message in websocket:
            try:
                data = json.loads(message)
                logging.debug(f"Received message: {data}")
                
                if data.get('type') == 'http-response':
                    # Get the request ID from the response
                    request_id = data.get('request_id')
                    if request_id and request_id in pending_responses[subdomain]:
                        # Set the response for the waiting request
                        pending_responses[subdomain][request_id].set_result(data)
                    else:
                        logging.error(f"No pending request found for ID: {request_id}")
                
            except json.JSONDecodeError as e:
                logging.error(f"Invalid JSON message: {e}")
            except Exception as e:
                logging.error(f"Error processing message: {e}\n{traceback.format_exc()}")
    except websockets.exceptions.ConnectionClosed:
        logging.info(f"Tunnel {subdomain} disconnected")
    finally:
        tunnels.pop(subdomain, None)
        subdomains.pop(subdomain, None)
        # Clean up any pending responses
        if subdomain in pending_responses:
            del pending_responses[subdomain]

async def http_handler(request):
    """Handle HTTP requests and forward them to the appropriate tunnel"""
    # Extract subdomain from host header
    host = request.headers.get('Host', '')
    subdomain = host.split('.')[0] if '.' in host else 'default'
    
    logging.debug(f"Received HTTP request for subdomain: {subdomain}")
    
    if subdomain not in tunnels:
        logging.error(f"Tunnel {subdomain} not found")
        return web.Response(
            status=404,
            text=f"Tunnel {subdomain} not found"
        )
    
    # Get the tunnel's WebSocket connection
    ws = tunnels[subdomain]
    
    try:
        # Generate a unique request ID
        request_id = str(random.randint(1000, 9999))
        
        # Create a future to wait for the response
        response_future = asyncio.Future()
        pending_responses[subdomain][request_id] = response_future
        
        # Forward the request to the tunnel
        request_data = {
            'type': 'http-request',
            'request_id': request_id,
            'method': request.method,
            'path': request.path,
            'headers': dict(request.headers),
            'body': await request.text()
        }
        logging.debug(f"Sending request to tunnel: {request_data}")
        await ws.send(json.dumps(request_data))
        
        # Wait for response from the tunnel with a timeout
        try:
            response_data = await asyncio.wait_for(response_future, timeout=30.0)
            return web.Response(
                status=response_data.get('status', 200),
                text=response_data.get('body', '')
            )
        except asyncio.TimeoutError:
            logging.error(f"Request timed out for {subdomain}")
            return web.Response(status=504, text="Gateway Timeout")
        finally:
            # Clean up the pending response
            if request_id in pending_responses[subdomain]:
                del pending_responses[subdomain][request_id]
            
    except Exception as e:
        logging.error(f"Error handling request: {e}\n{traceback.format_exc()}")
        return web.Response(status=500, text=f"Internal Server Error: {str(e)}")

async def start_server():
    # Start WebSocket server
    ws_server = await websockets.serve(
        websocket_handler,
        "0.0.0.0",
        8765
    )
    logging.info("WebSocket server started on ws://localhost:8765")
    
    # Start HTTP server
    app = web.Application()
    app.router.add_route('*', '/', http_handler)
    app.router.add_route('*', '/{tail:.*}', http_handler)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8081)
    await site.start()
    logging.info("HTTP server started on http://localhost:8081")
    
    # Keep the server running
    await asyncio.Future()

if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        logging.info("Server stopped")
    except Exception as e:
        logging.error(f"Server error: {e}")
