#!/usr/bin/env python3
"""
WSGI entry point for PyTunnel on Render
Standard wsgi.py file that Render expects
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

# This is what Render will look for
wsgi_application = application

if __name__ == '__main__':
    # If run directly, use aiohttp
    from server_render_optimized import main
    main()
