#!/usr/bin/env python3
"""
Simple WebSocket server for testing
"""

import asyncio
import websockets
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Store connected clients
clients = {}

async def handler(websocket, path):
    """Handle WebSocket connections"""
    client_id = f"client_{len(clients) + 1}"
    clients[client_id] = websocket
    
    logger.info(f"Client {client_id} connected")
    
    try:
        # Send welcome message
        await websocket.send(json.dumps({
            'type': 'welcome',
            'client_id': client_id,
            'message': 'Connected to tunnel server'
        }))
        
        async for message in websocket:
            try:
                data = json.loads(message)
                logger.info(f"Received from {client_id}: {data}")
                
                # Echo back the message
                await websocket.send(json.dumps({
                    'type': 'echo',
                    'data': data
                }))
                
            except json.JSONDecodeError:
                logger.error(f"Invalid JSON from {client_id}")
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Error handling client {client_id}: {e}")
    finally:
        if client_id in clients:
            del clients[client_id]

async def main():
    """Start the WebSocket server"""
    logger.info("Starting WebSocket server on ws://localhost:8765")
    
    async with websockets.serve(handler, "localhost", 8765):
        logger.info("Server is running. Press Ctrl+C to stop.")
        await asyncio.Future()  # Run forever

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Server stopped")
