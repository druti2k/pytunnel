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
import ssl
from cert_utils import CertificateManager

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more detailed logs
    format='%(asctime)s - %(levelname)s - %(message)s'
)

AUTH_TOKEN = os.getenv("AUTH_TOKEN", "mysecrettoken")
PUBLIC_HOST = os.getenv("PUBLIC_HOST", "localhost")  # Change this to your public IP/domain

# SSL/TLS Configuration
USE_SSL = os.getenv("USE_SSL", "true").lower() == "true"
SSL_CERT_FILE = os.getenv("SSL_CERT_FILE", "certs/server.crt")
SSL_KEY_FILE = os.getenv("SSL_KEY_FILE", "certs/server.key")
SSL_CA_CERT_FILE = os.getenv("SSL_CA_CERT_FILE", "certs/ca.crt")

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

async def websocket_handler(websocket):
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
    
    logging.info(f"Received HTTP request for subdomain: {subdomain}")
    logging.info(f"Request method: {request.method}")
    logging.info(f"Request path: {request.path}")
    logging.info(f"Request headers: {dict(request.headers)}")
    
    if subdomain not in tunnels:
        logging.error(f"Tunnel {subdomain} not found. Available tunnels: {list(tunnels.keys())}")
        return web.Response(
            status=404,
            text=f"Tunnel {subdomain} not found. Available tunnels: {list(tunnels.keys())}"
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
        logging.info(f"Sending request to tunnel: {request_data}")
        await ws.send(json.dumps(request_data))
        
        # Wait for response from the tunnel with a timeout
        try:
            response_data = await asyncio.wait_for(response_future, timeout=30.0)
            logging.info(f"Received response from tunnel: {response_data}")
            return web.Response(
                status=response_data.get('status', 200),
                text=response_data.get('body', ''),
                headers=response_data.get('headers', {})
            )
        except asyncio.TimeoutError:
            logging.error(f"Request timed out for {subdomain}")
            return web.Response(status=504, text="Gateway Timeout")
        finally:
            # Clean up the pending response
            if subdomain in pending_responses and request_id in pending_responses[subdomain]:
                del pending_responses[subdomain][request_id]
            
    except Exception as e:
        logging.error(f"Error handling request: {e}\n{traceback.format_exc()}")
        return web.Response(status=500, text=f"Internal Server Error: {str(e)}")

async def health_handler(request):
    """Simple health check endpoint"""
    return web.Response(text="OK", status=200)

@web.middleware
async def logging_middleware(request, handler):
    """Log all incoming requests"""
    logging.info(f"HTTP Request: {request.method} {request.path} from {request.remote}")
    logging.info(f"Headers: {dict(request.headers)}")
    try:
        response = await handler(request)
        logging.info(f"Response: {response.status}")
        return response
    except Exception as e:
        logging.error(f"Error in handler: {e}")
        raise

async def start_server(host="0.0.0.0", ws_port=8765, http_port=8081, use_ssl=None):
    # Initialize certificate manager
    cert_manager = CertificateManager()
    
    # Determine SSL usage
    if use_ssl is None:
        use_ssl = USE_SSL
    
    # Create SSL context if needed
    ssl_context = None
    if use_ssl:
        try:
            ssl_context = cert_manager.create_ssl_context(
                SSL_CERT_FILE, 
                SSL_KEY_FILE, 
                SSL_CA_CERT_FILE
            )
            logging.info("SSL/TLS enabled")
        except Exception as e:
            logging.warning(f"Failed to load SSL certificates: {e}")
            logging.info("Falling back to HTTP/WS")
            use_ssl = False
    
    # Start WebSocket server
    if use_ssl and ssl_context:
        ws_server = await websockets.serve(
            websocket_handler,
            host,
            ws_port,
            ssl=ssl_context
        )
        protocol = "wss"
        logging.info(f"Secure WebSocket server started on wss://{host}:{ws_port}")
    else:
        ws_server = await websockets.serve(
            websocket_handler,
            host,
            ws_port
        )
        protocol = "ws"
        logging.info(f"WebSocket server started on ws://{host}:{ws_port}")
    
    # Start HTTP server
    app = web.Application(middlewares=[logging_middleware])
    app.router.add_get('/health', health_handler)
    
    # Add explicit routes for all HTTP methods
    app.router.add_route('GET', '/{path:.*}', http_handler)
    app.router.add_route('POST', '/{path:.*}', http_handler)
    app.router.add_route('PUT', '/{path:.*}', http_handler)
    app.router.add_route('DELETE', '/{path:.*}', http_handler)
    app.router.add_route('PATCH', '/{path:.*}', http_handler)
    app.router.add_route('HEAD', '/{path:.*}', http_handler)
    app.router.add_route('OPTIONS', '/{path:.*}', http_handler)
    
    # Add a catch-all route for any other methods
    app.router.add_route('*', '/{path:.*}', http_handler)
    
    if use_ssl and ssl_context:
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, http_port, ssl_context=ssl_context)
        await site.start()
        protocol = "https"
        logging.info(f"Secure HTTP server started on https://{host}:{http_port}")
    else:
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, host, http_port)
        await site.start()
        protocol = "http"
        logging.info(f"HTTP server started on http://{host}:{http_port}")
    
    logging.info(f"PyTunnel server is running!")
    logging.info(f"WebSocket: {protocol}://{host}:{ws_port}")
    logging.info(f"HTTP: {protocol}://{host}:{http_port}")
    
    # Keep the server running
    try:
        await asyncio.Future()  # Run forever
    except KeyboardInterrupt:
        logging.info("Shutting down server...")
        ws_server.close()
        await ws_server.wait_closed()
        await runner.cleanup()

if __name__ == "__main__":
    try:
        asyncio.run(start_server())
    except KeyboardInterrupt:
        logging.info("Server stopped")
    except Exception as e:
        logging.error(f"Server error: {e}")
