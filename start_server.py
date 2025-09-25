#!/usr/bin/env python3
"""
Startup script for Render - handles the $ issue
"""

import os
import sys
import subprocess

def main():
    """Start the server using Gunicorn"""
    port = os.getenv('PORT', '10000')
    
    # Build the gunicorn command
    cmd = [
        'gunicorn',
        'your_application:wsgi_application',
        '--bind', f'0.0.0.0:{port}',
        '--workers', '1',
        '--worker-class', 'aiohttp.GunicornWebWorker',
        '--timeout', '120'
    ]
    
    print(f"Starting server with command: {' '.join(cmd)}")
    
    # Run gunicorn
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"Gunicorn failed: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("Server stopped by user")
        sys.exit(0)

if __name__ == '__main__':
    main()
