# client.py
import asyncio
import websockets
import json
import logging
import aiohttp
from aiohttp import web
import traceback

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Changed to DEBUG for more detailed logs
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Configuration
LOCAL_SERVER = "http://localhost:3000"  # Your local server

async def handle_local_request(data):
    """Forward the request to the local server"""
    async with aiohttp.ClientSession() as session:
        try:
            # Construct the URL for the local server
            url = f"{LOCAL_SERVER}{data.get('path', '/')}"
            logging.debug(f"Forwarding request to local server: {url}")
            
            # Forward the request to the local server
            async with session.request(
                method=data.get('method', 'GET'),
                url=url,
                headers=data.get('headers', {}),
                data=data.get('body')
            ) as response:
                # Get the response
                body = await response.text()
                logging.debug(f"Received response from local server: {response.status}")
                return {
                    'type': 'http-response',
                    'request_id': data.get('request_id'),
                    'status': response.status,
                    'headers': dict(response.headers),
                    'body': body
                }
        except Exception as e:
            logging.error(f"Error forwarding request: {e}\n{traceback.format_exc()}")
            return {
                'type': 'http-response',
                'request_id': data.get('request_id'),
                'status': 500,
                'body': f"Error: {str(e)}"
            }

async def tunnel_client():
    """Connect to the tunnel server and handle requests"""
    uri = "ws://localhost:8765"
    logging.info(f"Connecting to tunnel server at {uri}")

    while True:
        try:
            async with websockets.connect(uri) as websocket:
                # Wait for subdomain assignment
                message = await websocket.recv()
                data = json.loads(message)
                if data.get('type') == 'subdomain':
                    subdomain = data['subdomain']
                    logging.info(f"Assigned subdomain: {subdomain}")
                    logging.info(f"Your tunnel is available at: http://{subdomain}.localhost:8081")

                while True:
                    try:
                        # Wait for a message from the server
                        message = await websocket.recv()
                        logging.debug(f"Received message from server: {message}")
                        data = json.loads(message)
                        
                        if data.get('type') == 'http-request':
                            logging.debug(f"Processing HTTP request: {data}")
                            # Forward the request to the local server
                            response = await handle_local_request(data)
                            logging.debug(f"Sending response to server: {response}")
                            # Send the response back to the server
                            await websocket.send(json.dumps(response))
                    except json.JSONDecodeError as e:
                        logging.error(f"Invalid JSON message: {e}")
                    except websockets.exceptions.ConnectionClosed:
                        logging.info("Connection closed")
                        break
                    except Exception as e:
                        logging.error(f"Error: {e}\n{traceback.format_exc()}")
                        break

        except Exception as e:
            logging.error(f"Connection failed: {e}\n{traceback.format_exc()}")
            logging.info("Retrying in 5 seconds...")
            await asyncio.sleep(5)

if __name__ == "__main__":
    try:
        asyncio.run(tunnel_client())
    except KeyboardInterrupt:
        logging.info("Client stopped")
