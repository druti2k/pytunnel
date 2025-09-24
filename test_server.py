#!/usr/bin/env python3
"""
Quick test script for PyTunnel server
"""

import asyncio
import aiohttp
import json
import time

async def test_server():
    """Test the server endpoints"""
    base_url = "http://localhost:8081"
    
    print("🧪 Testing PyTunnel Server...")
    
    async with aiohttp.ClientSession() as session:
        # Test health endpoint
        print("1. Testing health endpoint...")
        try:
            async with session.get(f"{base_url}/health") as resp:
                if resp.status == 200:
                    text = await resp.text()
                    print(f"   ✅ Health check passed: {text.strip()}")
                else:
                    print(f"   ❌ Health check failed: {resp.status}")
        except Exception as e:
            print(f"   ❌ Health check error: {e}")
        
        # Test test endpoint
        print("2. Testing test endpoint...")
        try:
            async with session.get(f"{base_url}/test") as resp:
                if resp.status == 200:
                    text = await resp.text()
                    print(f"   ✅ Test endpoint passed: {text.strip()}")
                else:
                    print(f"   ❌ Test endpoint failed: {resp.status}")
        except Exception as e:
            print(f"   ❌ Test endpoint error: {e}")
        
        # Test root endpoint
        print("3. Testing root endpoint...")
        try:
            async with session.get(f"{base_url}/") as resp:
                if resp.status == 200:
                    text = await resp.text()
                    print(f"   ✅ Root endpoint passed (length: {len(text)})")
                else:
                    print(f"   ❌ Root endpoint failed: {resp.status}")
        except Exception as e:
            print(f"   ❌ Root endpoint error: {e}")
        
        # Test WebSocket connection
        print("4. Testing WebSocket connection...")
        try:
            async with session.ws_connect(f"{base_url.replace('http', 'ws')}/ws") as ws:
                # Send connect message
                await ws.send_json({
                    'type': 'connect',
                    'client_id': 'test_client',
                    'subdomain': 'test'
                })
                
                # Wait for response
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:
                        data = json.loads(msg.data)
                        print(f"   ✅ WebSocket response: {data}")
                        break
                    elif msg.type == aiohttp.WSMsgType.ERROR:
                        print(f"   ❌ WebSocket error: {ws.exception()}")
                        break
                        
        except Exception as e:
            print(f"   ❌ WebSocket error: {e}")

if __name__ == '__main__':
    print("Starting PyTunnel server test...")
    print("Make sure the server is running on localhost:8081")
    print("Run: python server_simple.py")
    print()
    
    try:
        asyncio.run(test_server())
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Test failed: {e}")
