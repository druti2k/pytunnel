"""
Integration tests for Python LocalTunnel
"""

import pytest
import asyncio
import tempfile
import os
import time
from unittest.mock import patch, MagicMock
import httpx

# Import the module to test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from server import start_server
from client import tunnel_client


class TestTunnelIntegration:
    """Integration tests for tunnel functionality"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_basic_tunnel_flow(self):
        """Test basic tunnel flow from client to server"""
        # This is a high-level integration test
        # In a real scenario, you'd start the server and client in separate processes
        
        # Mock the server startup
        with patch('server.start_server') as mock_server:
            mock_server.return_value = None
            
            # Mock the client connection
            with patch('client.tunnel_client') as mock_client:
                mock_client.return_value = None
                
                # Test that both can be called without errors
                await start_server(use_ssl=False)
                await tunnel_client(use_ssl=False)
                
                mock_server.assert_called_once()
                mock_client.assert_called_once()
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_ssl_tunnel_flow(self):
        """Test SSL tunnel flow"""
        # Mock certificate generation
        with patch('cert_utils.CertificateManager') as mock_cert_manager_class, \
             patch('server.start_server') as mock_server, \
             patch('client.tunnel_client') as mock_client:
            
            mock_cert_manager = MagicMock()
            mock_cert_manager_class.return_value = mock_cert_manager
            mock_cert_manager.create_ssl_context.return_value = MagicMock()
            
            mock_server.return_value = None
            mock_client.return_value = None
            
            # Test SSL tunnel
            await start_server(use_ssl=True)
            await tunnel_client(use_ssl=True)
            
            mock_server.assert_called_once()
            mock_client.assert_called_once()


class TestCertificateIntegration:
    """Integration tests for certificate functionality"""
    
    @pytest.mark.integration
    def test_certificate_generation_integration(self):
        """Test full certificate generation workflow"""
        from cert_utils import CertificateManager
        
        with tempfile.TemporaryDirectory() as temp_dir:
            cert_manager = CertificateManager(temp_dir)
            
            # Generate all certificate types
            ca_cert, ca_key = cert_manager.generate_ca_certificate()
            server_cert, server_key = cert_manager.generate_self_signed_certificate()
            wildcard_cert, wildcard_key = cert_manager.generate_wildcard_certificate()
            
            # Verify all files exist
            assert os.path.exists(ca_cert)
            assert os.path.exists(ca_key)
            assert os.path.exists(server_cert)
            assert os.path.exists(server_key)
            assert os.path.exists(wildcard_cert)
            assert os.path.exists(wildcard_key)
            
            # Test SSL context creation
            ssl_context = cert_manager.create_ssl_context()
            assert ssl_context is not None
    
    @pytest.mark.integration
    def test_certificate_info_integration(self):
        """Test certificate information retrieval"""
        from cert_utils import CertificateManager
        
        with tempfile.TemporaryDirectory() as temp_dir:
            cert_manager = CertificateManager(temp_dir)
            
            # Generate a certificate
            cert_file, key_file = cert_manager.generate_self_signed_certificate()
            
            # Get certificate info
            info = cert_manager.get_certificate_info()
            
            # Verify info structure
            assert info is not None
            assert 'subject' in info
            assert 'issuer' in info
            assert 'not_valid_before' in info
            assert 'not_valid_after' in info
            assert 'serial_number' in info


class TestCLIIntegration:
    """Integration tests for CLI functionality"""
    
    @pytest.mark.integration
    def test_cli_certificate_generation_integration(self):
        """Test CLI certificate generation workflow"""
        from click.testing import CliRunner
        from pytunnel import cli
        
        runner = CliRunner()
        
        with patch('pytunnel.check_dependencies', return_value=True), \
             patch('pytunnel.create_development_certificates') as mock_certs:
            
            mock_cert_manager = MagicMock()
            mock_cert_manager.cert_dir = "/tmp/certs"
            mock_certs.return_value = mock_cert_manager
            
            # Test certs command
            result = runner.invoke(cli, ['certs'])
            
            assert result.exit_code == 0
            assert "SSL certificates generated successfully" in result.output
            mock_certs.assert_called_once()
    
    @pytest.mark.integration
    def test_cli_server_startup_integration(self):
        """Test CLI server startup workflow"""
        from click.testing import CliRunner
        from pytunnel import cli
        
        runner = CliRunner()
        
        with patch('pytunnel.check_dependencies', return_value=True), \
             patch('pytunnel.asyncio.run') as mock_run:
            
            # Test server command
            result = runner.invoke(cli, ['server', '--no-ssl'])
            
            assert result.exit_code == 0
            mock_run.assert_called_once()
    
    @pytest.mark.integration
    def test_cli_tunnel_startup_integration(self):
        """Test CLI tunnel startup workflow"""
        from click.testing import CliRunner
        from pytunnel import cli
        
        runner = CliRunner()
        
        with patch('pytunnel.check_dependencies', return_value=True), \
             patch('pytunnel.asyncio.run') as mock_run:
            
            # Test tunnel command
            result = runner.invoke(cli, ['tunnel', '--port', '3000', '--no-ssl'])
            
            assert result.exit_code == 0
            mock_run.assert_called_once()


class TestErrorHandlingIntegration:
    """Integration tests for error handling"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_server_startup_error_handling(self):
        """Test server startup error handling"""
        with patch('server.CertificateManager') as mock_cert_manager_class:
            mock_cert_manager = MagicMock()
            mock_cert_manager_class.return_value = mock_cert_manager
            mock_cert_manager.create_ssl_context.side_effect = Exception("SSL Error")
            
            # Server should fall back to non-SSL mode
            with patch('server.websockets.serve') as mock_ws_serve, \
                 patch('server.web.Application') as mock_app_class, \
                 patch('server.web.AppRunner') as mock_runner_class, \
                 patch('server.web.TCPSite') as mock_site_class, \
                 patch('asyncio.Future') as mock_future:
                
                mock_app = MagicMock()
                mock_app_class.return_value = mock_app
                
                mock_runner = MagicMock()
                mock_runner_class.return_value = mock_runner
                mock_runner.setup = asyncio.coroutine(lambda: None)
                
                mock_site = MagicMock()
                mock_site_class.return_value = mock_site
                mock_site.start = asyncio.coroutine(lambda: None)
                
                mock_future.return_value = asyncio.Future()
                mock_future.return_value.set_result(None)
                
                # Should not raise an exception
                await start_server(use_ssl=True)
                
                # Should have fallen back to non-SSL
                mock_ws_serve.assert_called_once()
                call_args = mock_ws_serve.call_args
                assert 'ssl' not in call_args[1]
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_client_connection_error_handling(self):
        """Test client connection error handling"""
        with patch('client.websockets.connect', side_effect=Exception("Connection failed")):
            # Mock asyncio.sleep to prevent infinite loop
            with patch('asyncio.sleep', side_effect=StopAsyncIteration()):
                try:
                    await tunnel_client()
                except StopAsyncIteration:
                    pass
                
                # Should handle the error gracefully and retry


if __name__ == "__main__":
    pytest.main([__file__, "-m", "integration"])
