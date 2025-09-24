#!/usr/bin/env python3
"""
Debug script for Render deployment
Helps identify what's going wrong
"""

import os
import sys
import time

def main():
    print("=== Render Debug Script ===")
    print(f"Python version: {sys.version}")
    print(f"Python executable: {sys.executable}")
    print(f"Current working directory: {os.getcwd()}")
    print(f"Environment variables:")
    
    # Print all environment variables
    for key, value in os.environ.items():
        if 'PORT' in key or 'PYTHON' in key or 'LOG' in key:
            print(f"  {key}: {value}")
    
    print(f"\nFiles in current directory:")
    try:
        for file in os.listdir('.'):
            print(f"  {file}")
    except Exception as e:
        print(f"  Error listing files: {e}")
    
    print(f"\nTesting imports:")
    try:
        import aiohttp
        print(f"  ✅ aiohttp: {aiohttp.__version__}")
    except Exception as e:
        print(f"  ❌ aiohttp: {e}")
    
    try:
        from aiohttp import web
        print(f"  ✅ aiohttp.web: OK")
    except Exception as e:
        print(f"  ❌ aiohttp.web: {e}")
    
    print(f"\nTesting server startup:")
    try:
        from server_minimal import main as server_main
        print(f"  ✅ server_minimal import: OK")
        
        # Try to start server briefly
        print(f"  Attempting to start server...")
        # We won't actually start it here, just test the import
        
    except Exception as e:
        print(f"  ❌ server_minimal: {e}")
    
    print(f"\nDebug complete!")

if __name__ == '__main__':
    main()
