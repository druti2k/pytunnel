"""
Tests for the CLI interface
"""

import pytest
import tempfile
import os
from unittest.mock import patch, MagicMock
from click.testing import CliRunner

# Import the module to test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from pytunnel import cli, validate_port, validate_host, check_dependencies


class TestCLIValidation:
    """Test CLI validation functions"""
    
    def test_validate_port_valid(self):
        """Test valid port validation"""
        ctx = MagicMock()
        param = MagicMock()
        
        # Test valid ports
        assert validate_port(ctx, param, 3000) == 3000
        assert validate_port(ctx, param, 1) == 1
        assert validate_port(ctx, param, 65535) == 65535
    
    def test_validate_port_invalid(self):
        """Test invalid port validation"""
        ctx = MagicMock()
        param = MagicMock()
        
        # Test invalid ports
        with pytest.raises(Exception, match="Port must be between 1 and 65535"):
            validate_port(ctx, param, 0)
        
        with pytest.raises(Exception, match="Port must be between 1 and 65535"):
            validate_port(ctx, param, 65536)
        
        with pytest.raises(Exception, match="Port must be between 1 and 65535"):
            validate_port(ctx, param, -1)
    
    def test_validate_host_valid(self):
        """Test valid host validation"""
        ctx = MagicMock()
        param = MagicMock()
        
        # Test valid hosts
        assert validate_host(ctx, param, "localhost") == "localhost"
        assert validate_host(ctx, param, "127.0.0.1") == "127.0.0.1"
        assert validate_host(ctx, param, "0.0.0.0") == "0.0.0.0"
        assert validate_host(ctx, param, "127.1.2.3") == "127.1.2.3"
    
    def test_validate_host_invalid(self):
        """Test invalid host validation"""
        ctx = MagicMock()
        param = MagicMock()
        
        # Test invalid hosts
        with pytest.raises(Exception, match="Host must be localhost, 127.x.x.x, or 0.x.x.x"):
            validate_host(ctx, param, "example.com")
        
        with pytest.raises(Exception, match="Host must be localhost, 127.x.x.x, or 0.x.x.x"):
            validate_host(ctx, param, "192.168.1.1")
    
    def test_check_dependencies_success(self):
        """Test dependency check success"""
        with patch('pytunnel.importlib.import_module'):
            assert check_dependencies() is True
    
    def test_check_dependencies_failure(self):
        """Test dependency check failure"""
        with patch('pytunnel.importlib.import_module', side_effect=ImportError("No module named 'test'")):
            assert check_dependencies() is False


class TestCLICommands:
    """Test CLI commands"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()
    
    def test_cli_help(self):
        """Test CLI help command"""
        result = self.runner.invoke(cli, ['--help'])
        assert result.exit_code == 0
        assert "Python LocalTunnel" in result.output
        assert "Commands:" in result.output
    
    def test_cli_version(self):
        """Test CLI version command"""
        with patch('pytunnel.check_dependencies', return_value=True):
            result = self.runner.invoke(cli, ['version'])
            assert result.exit_code == 0
            assert "Python LocalTunnel" in result.output
            assert "Version: 1.0.0" in result.output
    
    def test_cli_init(self):
        """Test CLI init command"""
        with patch('pytunnel.check_dependencies', return_value=True), \
             patch('pytunnel.subprocess.run') as mock_run:
            
            mock_run.return_value.returncode = 0
            
            result = self.runner.invoke(cli, ['init'])
            assert result.exit_code == 0
            assert "Database initialized successfully" in result.output
            mock_run.assert_called_once()
    
    def test_cli_init_failure(self):
        """Test CLI init command failure"""
        with patch('pytunnel.check_dependencies', return_value=True), \
             patch('pytunnel.subprocess.run') as mock_run:
            
            mock_run.side_effect = Exception("Database error")
            
            result = self.runner.invoke(cli, ['init'])
            assert result.exit_code == 1
            assert "Failed to initialize database" in result.output
    
    def test_cli_certs(self):
        """Test CLI certs command"""
        with patch('pytunnel.check_dependencies', return_value=True), \
             patch('pytunnel.create_development_certificates') as mock_certs:
            
            mock_cert_manager = MagicMock()
            mock_cert_manager.cert_dir = "/tmp/certs"
            mock_certs.return_value = mock_cert_manager
            
            result = self.runner.invoke(cli, ['certs'])
            assert result.exit_code == 0
            assert "SSL certificates generated successfully" in result.output
            mock_certs.assert_called_once()
    
    def test_cli_certs_missing_dependency(self):
        """Test CLI certs command with missing dependency"""
        with patch('pytunnel.check_dependencies', return_value=True), \
             patch('pytunnel.create_development_certificates', side_effect=ImportError("No module named 'cryptography'")):
            
            result = self.runner.invoke(cli, ['certs'])
            assert result.exit_code == 1
            assert "Missing dependency" in result.output
    
    def test_cli_server_help(self):
        """Test CLI server help"""
        with patch('pytunnel.check_dependencies', return_value=True):
            result = self.runner.invoke(cli, ['server', '--help'])
            assert result.exit_code == 0
            assert "Start the tunnel server" in result.output
            assert "--ssl" in result.output
            assert "--no-ssl" in result.output
    
    def test_cli_tunnel_help(self):
        """Test CLI tunnel help"""
        with patch('pytunnel.check_dependencies', return_value=True):
            result = self.runner.invoke(cli, ['tunnel', '--help'])
            assert result.exit_code == 0
            assert "Create a tunnel to expose your local server" in result.output
            assert "--port" in result.output
            assert "--ssl" in result.output
            assert "--no-ssl" in result.output


class TestCLIServerCommand:
    """Test CLI server command"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()
    
    def test_cli_server_basic(self):
        """Test basic server command"""
        with patch('pytunnel.check_dependencies', return_value=True), \
             patch('pytunnel.asyncio.run') as mock_run:
            
            result = self.runner.invoke(cli, ['server'])
            assert result.exit_code == 0
            mock_run.assert_called_once()
    
    def test_cli_server_with_ssl(self):
        """Test server command with SSL"""
        with patch('pytunnel.check_dependencies', return_value=True), \
             patch('pytunnel.asyncio.run') as mock_run:
            
            result = self.runner.invoke(cli, ['server', '--ssl'])
            assert result.exit_code == 0
            mock_run.assert_called_once()
    
    def test_cli_server_without_ssl(self):
        """Test server command without SSL"""
        with patch('pytunnel.check_dependencies', return_value=True), \
             patch('pytunnel.asyncio.run') as mock_run:
            
            result = self.runner.invoke(cli, ['server', '--no-ssl'])
            assert result.exit_code == 0
            mock_run.assert_called_once()
    
    def test_cli_server_with_custom_certificates(self):
        """Test server command with custom certificates"""
        with patch('pytunnel.check_dependencies', return_value=True), \
             patch('pytunnel.asyncio.run') as mock_run:
            
            result = self.runner.invoke(cli, [
                'server', 
                '--ssl', 
                '--cert-file', 'custom.crt', 
                '--key-file', 'custom.key'
            ])
            assert result.exit_code == 0
            mock_run.assert_called_once()
    
    def test_cli_server_with_custom_ports(self):
        """Test server command with custom ports"""
        with patch('pytunnel.check_dependencies', return_value=True), \
             patch('pytunnel.asyncio.run') as mock_run:
            
            result = self.runner.invoke(cli, [
                'server', 
                '--ws-port', '8766', 
                '--http-port', '8082'
            ])
            assert result.exit_code == 0
            mock_run.assert_called_once()


class TestCLITunnelCommand:
    """Test CLI tunnel command"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.runner = CliRunner()
    
    def test_cli_tunnel_basic(self):
        """Test basic tunnel command"""
        with patch('pytunnel.check_dependencies', return_value=True), \
             patch('pytunnel.asyncio.run') as mock_run:
            
            result = self.runner.invoke(cli, ['tunnel', '--port', '3000'])
            assert result.exit_code == 0
            mock_run.assert_called_once()
    
    def test_cli_tunnel_with_ssl(self):
        """Test tunnel command with SSL"""
        with patch('pytunnel.check_dependencies', return_value=True), \
             patch('pytunnel.asyncio.run') as mock_run:
            
            result = self.runner.invoke(cli, ['tunnel', '--port', '3000', '--ssl'])
            assert result.exit_code == 0
            mock_run.assert_called_once()
    
    def test_cli_tunnel_without_ssl(self):
        """Test tunnel command without SSL"""
        with patch('pytunnel.check_dependencies', return_value=True), \
             patch('pytunnel.asyncio.run') as mock_run:
            
            result = self.runner.invoke(cli, ['tunnel', '--port', '3000', '--no-ssl'])
            assert result.exit_code == 0
            mock_run.assert_called_once()
    
    def test_cli_tunnel_with_verify_ssl(self):
        """Test tunnel command with SSL verification"""
        with patch('pytunnel.check_dependencies', return_value=True), \
             patch('pytunnel.asyncio.run') as mock_run:
            
            result = self.runner.invoke(cli, ['tunnel', '--port', '3000', '--verify-ssl'])
            assert result.exit_code == 0
            mock_run.assert_called_once()
    
    def test_cli_tunnel_with_custom_server(self):
        """Test tunnel command with custom server"""
        with patch('pytunnel.check_dependencies', return_value=True), \
             patch('pytunnel.asyncio.run') as mock_run:
            
            result = self.runner.invoke(cli, [
                'tunnel', 
                '--port', '3000', 
                '--server-host', 'example.com', 
                '--server-port', '8766'
            ])
            assert result.exit_code == 0
            mock_run.assert_called_once()
    
    def test_cli_tunnel_invalid_port(self):
        """Test tunnel command with invalid port"""
        with patch('pytunnel.check_dependencies', return_value=True):
            result = self.runner.invoke(cli, ['tunnel', '--port', '70000'])
            assert result.exit_code == 2  # Click error
            assert "Port must be between 1 and 65535" in result.output


if __name__ == "__main__":
    pytest.main([__file__])
