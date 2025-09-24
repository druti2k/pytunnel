#!/usr/bin/env python3
"""
Startup script for Render.com
Ensures proper environment setup
"""

import os
import sys
import logging

# Set up logging immediately
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    logger.info("=== PyTunnel Render Startup ===")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Environment PORT: {os.getenv('PORT', 'not set')}")
    logger.info(f"Environment PYTHON_VERSION: {os.getenv('PYTHON_VERSION', 'not set')}")
    logger.info(f"Environment LOG_LEVEL: {os.getenv('LOG_LEVEL', 'not set')}")
    
    # Import and run the server
    try:
        from server_render_fixed import main as server_main
        logger.info("Starting PyTunnel server...")
        server_main()
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
