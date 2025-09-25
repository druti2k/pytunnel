#!/usr/bin/env python3
"""
Startup script for Render - uses uvicorn for better aiohttp support
"""

import os
import sys
import subprocess

def main():
    """Start the server using uvicorn"""
    port = os.getenv('PORT', '10000')
    
    # Build the uvicorn command
    cmd = [
        'uvicorn',
        'server_render_optimized:app',
        '--host', '0.0.0.0',
        '--port', port,
        '--workers', '1'
    ]
    
    print(f"Starting server with command: {' '.join(cmd)}")
    
    # Run uvicorn
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Uvicorn failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("Server stopped by user")
        sys.exit(0)

if __name__ == '__main__':
    main()
