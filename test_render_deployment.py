#!/usr/bin/env python3
"""
Simple test client for PyTunnel Render deployment
"""

import asyncio
import websockets
import json
import time

async def test_tunnel():
    """Test tunnel connection"""
    try:
        # Connect to WebSocket
        uri = "wss://your-render-app.onrender.com/ws"
        print(f"Connecting to {uri}...")
        
        async with websockets.connect(uri) as websocket:
            print("Connected!")
            
            # Send connect message
            connect_msg = {
                "type": "connect",
                "client_id": f"test_client_{int(time.time())}",
                "subdomain": "test123"
            }
            
            await websocket.send(json.dumps(connect_msg))
            print("Sent connect message")
            
            # Wait for response
            response = await websocket.recv()
            data = json.loads(response)
            print(f"Received: {data}")
            
            if data.get('type') == 'connected':
                print(f"✅ Tunnel created successfully!")
                print(f"Tunnel ID: {data.get('tunnel_id')}")
                print(f"Subdomain: {data.get('subdomain')}")
                
                # Send heartbeat
                heartbeat_msg = {"type": "heartbeat"}
                await websocket.send(json.dumps(heartbeat_msg))
                print("Sent heartbeat")
                
                # Wait for heartbeat ack
                ack = await websocket.recv()
                print(f"Heartbeat ACK: {ack}")
                
                print("✅ Test completed successfully!")
            else:
                print(f"❌ Failed to create tunnel: {data}")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    print("🧪 Testing PyTunnel Render deployment...")
    print("Make sure to update the URI with your actual Render app URL")
    asyncio.run(test_tunnel())
