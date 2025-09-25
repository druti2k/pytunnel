#!/usr/bin/env python3
"""
WSGI wrapper for PyTunnel on Render
This allows Render to use Gunicorn if needed
"""

import os
import sys
import logging
from aiohttp import web
from aiohttp_wsgi import WSGIHandler

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import our optimized server
from server_render_optimized import app

# Convert aiohttp app to WSGI
wsgi_handler = WSGIHandler(app)

def application(environ, start_response):
    """WSGI application entry point"""
    return wsgi_handler(environ, start_response)

if __name__ == '__main__':
    # If run directly, use aiohttp
    from server_render_optimized import main
    main()
