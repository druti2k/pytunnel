#!/usr/bin/env python3
"""
Test script for Python LocalTunnel
Tests the complete tunnel functionality
"""

import asyncio
import aiohttp
import websockets
import json
import time
import subprocess
import sys
import os
from http.server import HTTPServer, BaseHTTPRequestHandler
import threading
import requests

class TestHTTPHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        self.wfile.write(b"<h1>Test Server Running!</h1><p>If you can see this, the tunnel is working!</p>")
    
    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = {"status": "success", "received": post_data.decode()}
        self.wfile.write(json.dumps(response).encode())

def start_test_server(port=3000):
    """Start a simple HTTP server for testing"""
    server = HTTPServer(('localhost', port), TestHTTPHandler)
    thread = threading.Thread(target=server.serve_forever)
    thread.daemon = True
    thread.start()
    print(f"✅ Test server started on http://localhost:{port}")
    return server

async def test_tunnel():
    """Test the complete tunnel functionality"""
    print("🚀 Starting tunnel test...")
    
    # Start test server
    test_server = start_test_server(3000)
    
    try:
        # Wait a moment for server to start
        await asyncio.sleep(1)
        
        # Test local server directly
        print("📡 Testing local server...")
        response = requests.get("http://localhost:3000", timeout=5)
        if response.status_code == 200:
            print("✅ Local server is working")
        else:
            print("❌ Local server test failed")
            return False
        
        # Test tunnel connection
        print("🔗 Testing tunnel connection...")
        
        # Connect to WebSocket server
        uri = "ws://localhost:8765"
        async with websockets.connect(uri) as websocket:
            # Wait for subdomain assignment
            message = await websocket.recv()
            data = json.loads(message)
            
            if data.get('type') == 'subdomain':
                subdomain = data['subdomain']
                print(f"✅ Tunnel connected! Subdomain: {subdomain}")
                
                # Test HTTP request through tunnel
                tunnel_url = f"http://{subdomain}.localhost:8081"
                print(f"🌐 Testing tunnel URL: {tunnel_url}")
                
                # Send a test request through the tunnel
                test_data = {"test": "data", "timestamp": time.time()}
                
                async with aiohttp.ClientSession() as session:
                    # Test GET request
                    async with session.get(tunnel_url) as response:
                        if response.status == 200:
                            content = await response.text()
                            if "Test Server Running" in content:
                                print("✅ GET request through tunnel successful!")
                            else:
                                print("❌ GET request failed - unexpected content")
                                return False
                        else:
                            print(f"❌ GET request failed - status {response.status}")
                            return False
                    
                    # Test POST request
                    async with session.post(tunnel_url, json=test_data) as response:
                        if response.status == 200:
                            content = await response.json()
                            if content.get('status') == 'success':
                                print("✅ POST request through tunnel successful!")
                            else:
                                print("❌ POST request failed - unexpected response")
                                return False
                        else:
                            print(f"❌ POST request failed - status {response.status}")
                            return False
                
                print("🎉 All tunnel tests passed!")
                return True
            else:
                print("❌ Failed to get subdomain from tunnel")
                return False
                
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        return False
    finally:
        # Clean up
        test_server.shutdown()
        test_server.server_close()

def run_tests():
    """Run all tests"""
    print("🧪 Running Python LocalTunnel Tests")
    print("=" * 50)
    
    # Test 1: Check if server is running
    print("\n1️⃣ Checking if tunnel server is running...")
    try:
        response = requests.get("http://localhost:8081", timeout=5)
        print("✅ Tunnel server is responding")
    except:
        print("❌ Tunnel server is not running. Please start it first:")
        print("   python pytunnel.py server")
        return False
    
    # Test 2: Check WebSocket connection
    print("\n2️⃣ Testing WebSocket connection...")
    try:
        response = requests.get("http://localhost:8765", timeout=5)
        print("✅ WebSocket server is accessible")
    except:
        print("❌ WebSocket server is not accessible")
        return False
    
    # Test 3: Run tunnel functionality test
    print("\n3️⃣ Testing tunnel functionality...")
    result = asyncio.run(test_tunnel())
    
    if result:
        print("\n🎉 All tests passed! The tunnel is working correctly.")
        return True
    else:
        print("\n❌ Some tests failed. Please check the tunnel setup.")
        return False

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
