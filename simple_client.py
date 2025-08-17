#!/usr/bin/env python3
"""
Simple WebSocket client for testing
"""

import asyncio
import websockets
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def client():
    """Connect to the WebSocket server"""
    uri = "ws://localhost:8765"
    logger.info(f"Connecting to {uri}")
    
    try:
        async with websockets.connect(uri) as websocket:
            logger.info("Connected to server!")
            
            # Wait for welcome message
            message = await websocket.recv()
            data = json.loads(message)
            logger.info(f"Received: {data}")
            
            # Send a test message
            test_message = {
                'type': 'test',
                'message': 'Hello from client!'
            }
            await websocket.send(json.dumps(test_message))
            logger.info(f"Sent: {test_message}")
            
            # Wait for response
            response = await websocket.recv()
            response_data = json.loads(response)
            logger.info(f"Received response: {response_data}")
            
            # Keep connection alive for a bit
            await asyncio.sleep(5)
            
    except Exception as e:
        logger.error(f"Connection failed: {e}")

if __name__ == "__main__":
    try:
        asyncio.run(client())
    except KeyboardInterrupt:
        logger.info("Client stopped")
