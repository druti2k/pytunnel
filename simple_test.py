#!/usr/bin/env python3
"""
Simple test script for Python LocalTunnel
Tests basic connectivity without SSL complications
"""

import socket
import json
import websockets
import asyncio
import sys

def test_tcp_connection(host, port):
    """Test basic TCP connection"""
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(5)
        result = sock.connect_ex((host, port))
        sock.close()
        return result == 0
    except Exception as e:
        print(f"❌ TCP connection test failed: {e}")
        return False

def test_websocket_connection():
    """Test WebSocket connection"""
    try:
        async def test():
            uri = "ws://localhost:8765"
            async with websockets.connect(uri) as websocket:
                # Wait for subdomain assignment
                message = await websocket.recv()
                data = json.loads(message)
                
                if data.get('type') == 'subdomain':
                    subdomain = data['subdomain']
                    print(f"✅ WebSocket connected! Subdomain: {subdomain}")
                    return True
                else:
                    print("❌ Failed to get subdomain from WebSocket")
                    return False
        
        return asyncio.run(test())
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")
        return False
    except Exception as e:
        print(f"❌ WebSocket test failed: {e}")
        return False

def main():
    print("🧪 Simple Python LocalTunnel Test")
    print("=" * 40)
    
    # Test 1: TCP connections
    print("\n1️⃣ Testing TCP connections...")
    
    ws_ok = test_tcp_connection('localhost', 8765)
    if ws_ok:
        print("✅ WebSocket port 8765 is accessible")
    else:
        print("❌ WebSocket port 8765 is not accessible")
    
    http_ok = test_tcp_connection('localhost', 8081)
    if http_ok:
        print("✅ HTTP port 8081 is accessible")
    else:
        print("❌ HTTP port 8081 is not accessible")
    
    # Test 2: WebSocket connection
    print("\n2️⃣ Testing WebSocket connection...")
    ws_connected = test_websocket_connection()
    
    # Summary
    print("\n📊 Test Results:")
    print(f"   WebSocket Port: {'✅' if ws_ok else '❌'}")
    print(f"   HTTP Port: {'✅' if http_ok else '❌'}")
    print(f"   WebSocket Connection: {'✅' if ws_connected else '❌'}")
    
    if ws_ok and http_ok and ws_connected:
        print("\n🎉 All tests passed! The tunnel server is working correctly.")
        return True
    else:
        print("\n❌ Some tests failed. Please check the server configuration.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
