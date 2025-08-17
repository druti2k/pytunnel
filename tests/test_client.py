"""
Tests for the tunnel client
"""

import pytest
import asyncio
import json
import os
from unittest.mock import patch, MagicMock, AsyncMock

# Import the module to test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from client import handle_local_request, tunnel_client, handle_websocket_connection


class TestHandleLocalRequest:
    """Test local request handling"""
    
    @pytest.mark.asyncio
    async def test_handle_local_request_success(self):
        """Test successful local request handling"""
        # Mock aiohttp session
        mock_session = AsyncMock()
        mock_response = AsyncMock()
        mock_response.status = 200
        mock_response.text = AsyncMock(return_value="Hello World")
        mock_response.headers = {"Content-Type": "text/plain"}
        
        mock_session.request.return_value.__aenter__.return_value = mock_response
        
        # Test data
        test_data = {
            'method': 'GET',
            'path': '/test',
            'headers': {'User-Agent': 'test'},
            'body': '',
            'request_id': '1234'
        }
        
        with patch('client.aiohttp.ClientSession', return_value=mock_session):
            result = await handle_local_request(test_data)
            
            # Check that session was used correctly
            mock_session.request.assert_called_once_with(
                method='GET',
                url='http://localhost:3000/test',
                headers={'User-Agent': 'test'},
                data=''
            )
            
            # Check response format
            assert result['type'] == 'http-response'
            assert result['request_id'] == '1234'
            assert result['status'] == 200
            assert result['body'] == 'Hello World'
            assert result['headers'] == {"Content-Type": "text/plain"}
    
    @pytest.mark.asyncio
    async def test_handle_local_request_error(self):
        """Test local request handling with error"""
        # Mock aiohttp session to raise an exception
        mock_session = AsyncMock()
        mock_session.request.side_effect = Exception("Connection failed")
        
        # Test data
        test_data = {
            'method': 'GET',
            'path': '/test',
            'headers': {},
            'body': '',
            'request_id': '1234'
        }
        
        with patch('client.aiohttp.ClientSession', return_value=mock_session):
            result = await handle_local_request(test_data)
            
            # Check error response format
            assert result['type'] == 'http-response'
            assert result['request_id'] == '1234'
            assert result['status'] == 500
            assert 'Error:' in result['body']


class TestTunnelClient:
    """Test tunnel client functionality"""
    
    @pytest.mark.asyncio
    async def test_tunnel_client_with_ssl(self):
        """Test tunnel client with SSL enabled"""
        # Mock websockets.connect
        mock_websocket = AsyncMock()
        mock_websocket.recv = AsyncMock(side_effect=StopAsyncIteration())
        
        with patch('client.websockets.connect', return_value=mock_websocket) as mock_connect:
            # Mock asyncio.sleep to prevent infinite loop
            with patch('asyncio.sleep', side_effect=StopAsyncIteration()):
                try:
                    await tunnel_client(use_ssl=True)
                except StopAsyncIteration:
                    pass
                
                # Check that websockets.connect was called with SSL
                mock_connect.assert_called_once()
                call_args = mock_connect.call_args
                assert 'ssl' in call_args[1]
    
    @pytest.mark.asyncio
    async def test_tunnel_client_without_ssl(self):
        """Test tunnel client without SSL"""
        # Mock websockets.connect
        mock_websocket = AsyncMock()
        mock_websocket.recv = AsyncMock(side_effect=StopAsyncIteration())
        
        with patch('client.websockets.connect', return_value=mock_websocket) as mock_connect:
            # Mock asyncio.sleep to prevent infinite loop
            with patch('asyncio.sleep', side_effect=StopAsyncIteration()):
                try:
                    await tunnel_client(use_ssl=False)
                except StopAsyncIteration:
                    pass
                
                # Check that websockets.connect was called without SSL
                mock_connect.assert_called_once()
                call_args = mock_connect.call_args
                assert 'ssl' not in call_args[1]
    
    @pytest.mark.asyncio
    async def test_tunnel_client_connection_error(self):
        """Test tunnel client with connection error"""
        # Mock websockets.connect to raise an exception
        with patch('client.websockets.connect', side_effect=Exception("Connection failed")):
            # Mock asyncio.sleep to prevent infinite loop
            with patch('asyncio.sleep', side_effect=StopAsyncIteration()):
                try:
                    await tunnel_client()
                except StopAsyncIteration:
                    pass
                
                # The function should handle the error gracefully and retry


class TestHandleWebSocketConnection:
    """Test WebSocket connection handling"""
    
    @pytest.mark.asyncio
    async def test_handle_websocket_connection_subdomain(self):
        """Test WebSocket connection with subdomain assignment"""
        # Create a mock WebSocket
        mock_websocket = AsyncMock()
        
        # Mock the subdomain message
        subdomain_message = json.dumps({
            'type': 'subdomain',
            'subdomain': 'test123'
        })
        
        # Mock the websocket to return subdomain then stop
        mock_websocket.recv = AsyncMock(side_effect=[subdomain_message, StopAsyncIteration()])
        
        # Mock handle_local_request
        with patch('client.handle_local_request', new_callable=AsyncMock) as mock_handle_request:
            await handle_websocket_connection(mock_websocket)
            
            # Check that subdomain message was received
            assert mock_websocket.recv.call_count >= 1
    
    @pytest.mark.asyncio
    async def test_handle_websocket_connection_http_request(self):
        """Test WebSocket connection with HTTP request"""
        # Create a mock WebSocket
        mock_websocket = AsyncMock()
        
        # Mock the subdomain message
        subdomain_message = json.dumps({
            'type': 'subdomain',
            'subdomain': 'test123'
        })
        
        # Mock the HTTP request message
        http_request_message = json.dumps({
            'type': 'http-request',
            'request_id': '1234',
            'method': 'GET',
            'path': '/test',
            'headers': {},
            'body': ''
        })
        
        # Mock the websocket to return messages then stop
        mock_websocket.recv = AsyncMock(side_effect=[
            subdomain_message, 
            http_request_message, 
            StopAsyncIteration()
        ])
        mock_websocket.send = AsyncMock()
        
        # Mock handle_local_request
        mock_response = {
            'type': 'http-response',
            'request_id': '1234',
            'status': 200,
            'body': 'Hello World'
        }
        
        with patch('client.handle_local_request', new_callable=AsyncMock, return_value=mock_response):
            await handle_websocket_connection(mock_websocket)
            
            # Check that response was sent back
            mock_websocket.send.assert_called_once()
            sent_data = json.loads(mock_websocket.send.call_args[0][0])
            assert sent_data['type'] == 'http-response'
            assert sent_data['request_id'] == '1234'
    
    @pytest.mark.asyncio
    async def test_handle_websocket_connection_invalid_json(self):
        """Test WebSocket connection with invalid JSON"""
        # Create a mock WebSocket
        mock_websocket = AsyncMock()
        
        # Mock the subdomain message
        subdomain_message = json.dumps({
            'type': 'subdomain',
            'subdomain': 'test123'
        })
        
        # Mock the websocket to return valid message then invalid JSON then stop
        mock_websocket.recv = AsyncMock(side_effect=[
            subdomain_message, 
            "invalid json", 
            StopAsyncIteration()
        ])
        
        # Mock handle_local_request
        with patch('client.handle_local_request', new_callable=AsyncMock):
            await handle_websocket_connection(mock_websocket)
            
            # Should handle invalid JSON gracefully


class TestClientConfiguration:
    """Test client configuration"""
    
    def test_client_configuration_defaults(self):
        """Test default client configuration"""
        from client import LOCAL_SERVER, USE_SSL, SSL_VERIFY
        
        assert LOCAL_SERVER == "http://localhost:3000"
        assert USE_SSL is True  # Should be True by default
        assert SSL_VERIFY is False  # Should be False by default
    
    def test_client_configuration_environment_variables(self):
        """Test client configuration with environment variables"""
        with patch.dict(os.environ, {
            'USE_SSL': 'false',
            'SSL_VERIFY': 'true'
        }):
            # Reload the module to pick up environment variables
            import importlib
            import client
            importlib.reload(client)
            
            assert client.USE_SSL is False
            assert client.SSL_VERIFY is True


if __name__ == "__main__":
    pytest.main([__file__])
