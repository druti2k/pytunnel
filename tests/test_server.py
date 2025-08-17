"""
Tests for the tunnel server
"""

import pytest
import asyncio
import json
import tempfile
import os
from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path

# Import the module to test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from server import (
    generate_subdomain, 
    find_available_port, 
    websocket_handler, 
    http_handler,
    start_server
)


class TestServerUtils:
    """Test server utility functions"""
    
    def test_generate_subdomain(self):
        """Test subdomain generation"""
        subdomain = generate_subdomain()
        
        # Check that subdomain is a string
        assert isinstance(subdomain, str)
        
        # Check that it's 8 characters long
        assert len(subdomain) == 8
        
        # Check that it only contains lowercase letters and digits
        assert subdomain.isalnum()
        assert subdomain.islower()
    
    def test_generate_subdomain_uniqueness(self):
        """Test that generated subdomains are unique"""
        subdomains = set()
        for _ in range(100):
            subdomain = generate_subdomain()
            assert subdomain not in subdomains
            subdomains.add(subdomain)
    
    def test_find_available_port(self):
        """Test finding available port"""
        # Mock socket to simulate port availability
        with patch('server.socket') as mock_socket:
            mock_socket.socket.return_value.__enter__.return_value.bind.return_value = None
            
            port = find_available_port(8081, 8081)
            assert port == 8081
    
    def test_find_available_port_no_ports(self):
        """Test finding available port when none are available"""
        # Mock socket to simulate all ports busy
        with patch('server.socket') as mock_socket:
            mock_socket.socket.return_value.__enter__.return_value.bind.side_effect = OSError("Port in use")
            
            with pytest.raises(OSError, match="No available ports found"):
                find_available_port(8081, 8081)


class TestWebSocketHandler:
    """Test WebSocket handler"""
    
    @pytest.mark.asyncio
    async def test_websocket_handler_connection(self):
        """Test WebSocket connection handling"""
        # Create a mock WebSocket
        mock_websocket = AsyncMock()
        mock_websocket.send = AsyncMock()
        mock_websocket.recv = AsyncMock()
        mock_websocket.__aiter__ = lambda self: self
        mock_websocket.__anext__ = AsyncMock(side_effect=StopAsyncIteration())
        
        # Mock the server state
        with patch('server.tunnels', {}), \
             patch('server.subdomains', {}), \
             patch('server.pending_responses', {}):
            
            # Call the handler
            await websocket_handler(mock_websocket, "/")
            
            # Check that subdomain was sent
            mock_websocket.send.assert_called_once()
            sent_data = json.loads(mock_websocket.send.call_args[0][0])
            assert sent_data['type'] == 'subdomain'
            assert 'subdomain' in sent_data
    
    @pytest.mark.asyncio
    async def test_websocket_handler_http_response(self):
        """Test WebSocket handler with HTTP response"""
        # Create a mock WebSocket
        mock_websocket = AsyncMock()
        mock_websocket.send = AsyncMock()
        
        # Create a mock response message
        response_message = json.dumps({
            'type': 'http-response',
            'request_id': '1234',
            'status': 200,
            'body': 'Hello World'
        })
        
        # Mock the server state
        with patch('server.tunnels', {}), \
             patch('server.subdomains', {}), \
             patch('server.pending_responses', {}) as mock_pending:
            
            # Set up a mock future
            mock_future = asyncio.Future()
            mock_future.set_result(None)
            mock_pending.__getitem__.return_value.__getitem__.return_value = mock_future
            
            # Mock the websocket to return the response message then stop
            mock_websocket.recv = AsyncMock(side_effect=[response_message, StopAsyncIteration()])
            mock_websocket.__aiter__ = lambda self: self
            mock_websocket.__anext__ = AsyncMock(side_effect=[response_message, StopAsyncIteration()])
            
            # Call the handler
            await websocket_handler(mock_websocket, "/")


class TestHTTPHandler:
    """Test HTTP handler"""
    
    @pytest.mark.asyncio
    async def test_http_handler_tunnel_not_found(self):
        """Test HTTP handler when tunnel is not found"""
        # Create a mock request
        mock_request = MagicMock()
        mock_request.headers = {'Host': 'nonexistent.localhost:8081'}
        mock_request.method = 'GET'
        mock_request.path = '/'
        mock_request.text = AsyncMock(return_value='')
        
        # Mock the server state with no tunnels
        with patch('server.tunnels', {}):
            response = await http_handler(mock_request)
            
            # Check that we get a 404 response
            assert response.status == 404
            assert 'not found' in response.text.lower()
    
    @pytest.mark.asyncio
    async def test_http_handler_success(self):
        """Test HTTP handler with successful tunnel"""
        # Create a mock request
        mock_request = MagicMock()
        mock_request.headers = {'Host': 'test.localhost:8081'}
        mock_request.method = 'GET'
        mock_request.path = '/'
        mock_request.text = AsyncMock(return_value='')
        
        # Create a mock WebSocket
        mock_websocket = AsyncMock()
        mock_websocket.send = AsyncMock()
        
        # Mock the server state
        with patch('server.tunnels', {'test': mock_websocket}), \
             patch('server.pending_responses', {}) as mock_pending:
            
            # Set up a mock future for the response
            mock_future = asyncio.Future()
            mock_future.set_result({
                'type': 'http-response',
                'request_id': '1234',
                'status': 200,
                'body': 'Hello World'
            })
            mock_pending.__getitem__.return_value.__getitem__.return_value = mock_future
            
            # Call the handler
            response = await http_handler(mock_request)
            
            # Check that we get a successful response
            assert response.status == 200
            assert response.text == 'Hello World'
            
            # Check that request was sent to WebSocket
            mock_websocket.send.assert_called_once()


class TestStartServer:
    """Test server startup"""
    
    @pytest.mark.asyncio
    async def test_start_server_with_ssl(self):
        """Test server startup with SSL"""
        with patch('server.CertificateManager') as mock_cert_manager_class, \
             patch('server.websockets.serve') as mock_ws_serve, \
             patch('server.web.Application') as mock_app_class, \
             patch('server.web.AppRunner') as mock_runner_class, \
             patch('server.web.TCPSite') as mock_site_class:
            
            # Set up mocks
            mock_cert_manager = MagicMock()
            mock_cert_manager_class.return_value = mock_cert_manager
            mock_cert_manager.create_ssl_context.return_value = MagicMock()
            
            mock_app = MagicMock()
            mock_app_class.return_value = mock_app
            
            mock_runner = MagicMock()
            mock_runner_class.return_value = mock_runner
            mock_runner.setup = AsyncMock()
            
            mock_site = MagicMock()
            mock_site_class.return_value = mock_site
            mock_site.start = AsyncMock()
            
            # Mock asyncio.Future to prevent infinite loop
            with patch('asyncio.Future') as mock_future:
                mock_future.return_value = asyncio.Future()
                mock_future.return_value.set_result(None)
                
                # Call start_server
                await start_server(use_ssl=True)
                
                # Check that SSL context was created
                mock_cert_manager.create_ssl_context.assert_called_once()
                
                # Check that WebSocket server was started with SSL
                mock_ws_serve.assert_called_once()
                call_args = mock_ws_serve.call_args
                assert 'ssl' in call_args[1]
    
    @pytest.mark.asyncio
    async def test_start_server_without_ssl(self):
        """Test server startup without SSL"""
        with patch('server.websockets.serve') as mock_ws_serve, \
             patch('server.web.Application') as mock_app_class, \
             patch('server.web.AppRunner') as mock_runner_class, \
             patch('server.web.TCPSite') as mock_site_class:
            
            # Set up mocks
            mock_app = MagicMock()
            mock_app_class.return_value = mock_app
            
            mock_runner = MagicMock()
            mock_runner_class.return_value = mock_runner
            mock_runner.setup = AsyncMock()
            
            mock_site = MagicMock()
            mock_site_class.return_value = mock_site
            mock_site.start = AsyncMock()
            
            # Mock asyncio.Future to prevent infinite loop
            with patch('asyncio.Future') as mock_future:
                mock_future.return_value = asyncio.Future()
                mock_future.return_value.set_result(None)
                
                # Call start_server
                await start_server(use_ssl=False)
                
                # Check that WebSocket server was started without SSL
                mock_ws_serve.assert_called_once()
                call_args = mock_ws_serve.call_args
                assert 'ssl' not in call_args[1]


if __name__ == "__main__":
    pytest.main([__file__])
