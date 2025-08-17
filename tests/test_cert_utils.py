"""
Tests for certificate utilities
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the module to test
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from cert_utils import CertificateManager, create_development_certificates


class TestCertificateManager:
    """Test the CertificateManager class"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.cert_manager = CertificateManager(self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_init(self):
        """Test CertificateManager initialization"""
        assert self.cert_manager.cert_dir == Path(self.temp_dir)
        assert self.cert_manager.cert_file == Path(self.temp_dir) / "server.crt"
        assert self.cert_manager.key_file == Path(self.temp_dir) / "server.key"
        assert self.cert_manager.ca_cert_file == Path(self.temp_dir) / "ca.crt"
        assert self.cert_manager.ca_key_file == Path(self.temp_dir) / "ca.key"
    
    def test_generate_self_signed_certificate(self):
        """Test self-signed certificate generation"""
        cert_file, key_file = self.cert_manager.generate_self_signed_certificate()
        
        # Check that files were created
        assert os.path.exists(cert_file)
        assert os.path.exists(key_file)
        
        # Check file sizes (should be reasonable sizes)
        assert os.path.getsize(cert_file) > 1000
        assert os.path.getsize(key_file) > 1000
    
    def test_generate_ca_certificate(self):
        """Test CA certificate generation"""
        ca_cert, ca_key = self.cert_manager.generate_ca_certificate()
        
        # Check that files were created
        assert os.path.exists(ca_cert)
        assert os.path.exists(ca_key)
        
        # Check file sizes
        assert os.path.getsize(ca_cert) > 1000
        assert os.path.getsize(ca_key) > 1000
    
    def test_generate_wildcard_certificate(self):
        """Test wildcard certificate generation"""
        wildcard_cert, wildcard_key = self.cert_manager.generate_wildcard_certificate()
        
        # Check that files were created
        assert os.path.exists(wildcard_cert)
        assert os.path.exists(wildcard_key)
        
        # Check file sizes
        assert os.path.getsize(wildcard_cert) > 1000
        assert os.path.getsize(wildcard_key) > 1000
    
    def test_create_ssl_context_with_existing_certs(self):
        """Test SSL context creation with existing certificates"""
        # Generate certificates first
        self.cert_manager.generate_self_signed_certificate()
        
        # Create SSL context
        ssl_context = self.cert_manager.create_ssl_context()
        
        # Check that SSL context was created
        assert ssl_context is not None
        assert hasattr(ssl_context, 'load_cert_chain')
    
    def test_create_ssl_context_without_certs(self):
        """Test SSL context creation without existing certificates"""
        # Should generate certificates automatically
        ssl_context = self.cert_manager.create_ssl_context()
        
        # Check that SSL context was created
        assert ssl_context is not None
        assert hasattr(ssl_context, 'load_cert_chain')
        
        # Check that certificates were generated
        assert os.path.exists(self.cert_manager.cert_file)
        assert os.path.exists(self.cert_manager.key_file)
    
    def test_get_certificate_info(self):
        """Test certificate info retrieval"""
        # Generate a certificate first
        self.cert_manager.generate_self_signed_certificate()
        
        # Get certificate info
        info = self.cert_manager.get_certificate_info()
        
        # Check that info was retrieved
        assert info is not None
        assert 'subject' in info
        assert 'issuer' in info
        assert 'not_valid_before' in info
        assert 'not_valid_after' in info
        assert 'serial_number' in info
    
    def test_get_certificate_info_nonexistent(self):
        """Test certificate info retrieval for nonexistent certificate"""
        info = self.cert_manager.get_certificate_info("nonexistent.crt")
        assert info is None


class TestCreateDevelopmentCertificates:
    """Test the create_development_certificates function"""
    
    def test_create_development_certificates(self):
        """Test development certificate creation"""
        with tempfile.TemporaryDirectory() as temp_dir:
            with patch('cert_utils.CertificateManager') as mock_manager_class:
                mock_manager = MagicMock()
                mock_manager_class.return_value = mock_manager
                
                # Mock the certificate generation methods
                mock_manager.generate_ca_certificate.return_value = ("ca.crt", "ca.key")
                mock_manager.generate_self_signed_certificate.return_value = ("server.crt", "server.key")
                mock_manager.generate_wildcard_certificate.return_value = ("wildcard.crt", "wildcard.key")
                mock_manager.cert_dir = Path(temp_dir)
                
                # Call the function
                result = create_development_certificates()
                
                # Check that methods were called
                mock_manager.generate_ca_certificate.assert_called_once()
                mock_manager.generate_self_signed_certificate.assert_called_once()
                mock_manager.generate_wildcard_certificate.assert_called_once()
                
                # Check that result is the manager
                assert result == mock_manager


if __name__ == "__main__":
    pytest.main([__file__])
