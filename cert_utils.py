#!/usr/bin/env python3
"""
Certificate utilities for Python LocalTunnel
Handles SSL/TLS certificate generation and management
"""

import os
import ssl
import tempfile
import ipaddress
from pathlib import Path
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class CertificateManager:
    """Manages SSL/TLS certificates for the tunnel server"""
    
    def __init__(self, cert_dir="certs"):
        self.cert_dir = Path(cert_dir)
        self.cert_dir.mkdir(exist_ok=True)
        
        self.cert_file = self.cert_dir / "server.crt"
        self.key_file = self.cert_dir / "server.key"
        self.ca_cert_file = self.cert_dir / "ca.crt"
        self.ca_key_file = self.cert_dir / "ca.key"
    
    def generate_self_signed_certificate(self, common_name="localhost", days_valid=365):
        """Generate a self-signed certificate for development"""
        logger.info(f"Generating self-signed certificate for {common_name}")
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Create certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Development"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "LocalTunnel"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Python LocalTunnel"),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=days_valid)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(common_name),
                x509.DNSName("localhost"),
                x509.DNSName("127.0.0.1"),
                x509.IPAddress(ipaddress.IPv4Address("127.0.0.1")),
                x509.IPAddress(ipaddress.IPv6Address("::1")),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        # Save certificate and key
        with open(self.cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        with open(self.key_file, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        logger.info(f"Certificate saved to {self.cert_file}")
        logger.info(f"Private key saved to {self.key_file}")
        
        return str(self.cert_file), str(self.key_file)
    
    def generate_ca_certificate(self, common_name="Python LocalTunnel CA", days_valid=3650):
        """Generate a Certificate Authority for signing other certificates"""
        logger.info(f"Generating CA certificate: {common_name}")
        
        # Generate CA private key
        ca_private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Create CA certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Development"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "LocalTunnel"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Python LocalTunnel"),
            x509.NameAttribute(NameOID.COMMON_NAME, common_name),
        ])
        
        ca_cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            ca_private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=days_valid)
        ).add_extension(
            x509.BasicConstraints(ca=True, path_length=None),
            critical=True,
        ).add_extension(
            x509.KeyUsage(
                digital_signature=True,
                key_encipherment=True,
                key_cert_sign=True,
                crl_sign=True,
                content_commitment=False,
                data_encipherment=False,
                key_agreement=False,
                encipher_only=False,
                decipher_only=False,
            ),
            critical=True,
        ).sign(ca_private_key, hashes.SHA256())
        
        # Save CA certificate and key
        with open(self.ca_cert_file, "wb") as f:
            f.write(ca_cert.public_bytes(serialization.Encoding.PEM))
        
        with open(self.ca_key_file, "wb") as f:
            f.write(ca_private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        logger.info(f"CA certificate saved to {self.ca_cert_file}")
        logger.info(f"CA private key saved to {self.ca_key_file}")
        
        return str(self.ca_cert_file), str(self.ca_key_file)
    
    def generate_wildcard_certificate(self, domain="*.localtunnel.me", days_valid=365):
        """Generate a wildcard certificate for subdomains"""
        logger.info(f"Generating wildcard certificate for {domain}")
        
        # Generate private key
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
        )
        
        # Create certificate
        subject = issuer = x509.Name([
            x509.NameAttribute(NameOID.COUNTRY_NAME, "US"),
            x509.NameAttribute(NameOID.STATE_OR_PROVINCE_NAME, "Development"),
            x509.NameAttribute(NameOID.LOCALITY_NAME, "LocalTunnel"),
            x509.NameAttribute(NameOID.ORGANIZATION_NAME, "Python LocalTunnel"),
            x509.NameAttribute(NameOID.COMMON_NAME, domain),
        ])
        
        cert = x509.CertificateBuilder().subject_name(
            subject
        ).issuer_name(
            issuer
        ).public_key(
            private_key.public_key()
        ).serial_number(
            x509.random_serial_number()
        ).not_valid_before(
            datetime.utcnow()
        ).not_valid_after(
            datetime.utcnow() + timedelta(days=days_valid)
        ).add_extension(
            x509.SubjectAlternativeName([
                x509.DNSName(domain),
                x509.DNSName("*.localtunnel.me"),
                x509.DNSName("localtunnel.me"),
            ]),
            critical=False,
        ).sign(private_key, hashes.SHA256())
        
        # Save certificate and key
        wildcard_cert_file = self.cert_dir / "wildcard.crt"
        wildcard_key_file = self.cert_dir / "wildcard.key"
        
        with open(wildcard_cert_file, "wb") as f:
            f.write(cert.public_bytes(serialization.Encoding.PEM))
        
        with open(wildcard_key_file, "wb") as f:
            f.write(private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            ))
        
        logger.info(f"Wildcard certificate saved to {wildcard_cert_file}")
        logger.info(f"Wildcard private key saved to {wildcard_key_file}")
        
        return str(wildcard_cert_file), str(wildcard_key_file)
    
    def create_ssl_context(self, cert_file=None, key_file=None, ca_cert_file=None):
        """Create SSL context for the server"""
        if cert_file is None:
            cert_file = self.cert_file
        if key_file is None:
            key_file = self.key_file
        
        # Check if certificates exist
        if not os.path.exists(cert_file) or not os.path.exists(key_file):
            logger.warning("Certificate files not found, generating new ones...")
            self.generate_self_signed_certificate()
        
        # Create SSL context
        ssl_context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        
        # Load certificate and key
        ssl_context.load_cert_chain(cert_file, key_file)
        
        # Add CA certificate if provided
        if ca_cert_file and os.path.exists(ca_cert_file):
            ssl_context.load_verify_locations(ca_cert_file)
        
        return ssl_context
    
    def get_certificate_info(self, cert_file=None):
        """Get information about a certificate"""
        if cert_file is None:
            cert_file = self.cert_file
        
        if not os.path.exists(cert_file):
            return None
        
        with open(cert_file, "rb") as f:
            cert_data = f.read()
        
        cert = x509.load_pem_x509_certificate(cert_data)
        
        return {
            "subject": dict(cert.subject),
            "issuer": dict(cert.issuer),
            "not_valid_before": cert.not_valid_before,
            "not_valid_after": cert.not_valid_after,
            "serial_number": cert.serial_number,
        }

def create_development_certificates():
    """Create development certificates for LocalTunnel"""
    cert_manager = CertificateManager()
    
    # Generate CA certificate
    ca_cert, ca_key = cert_manager.generate_ca_certificate()
    
    # Generate server certificate
    server_cert, server_key = cert_manager.generate_self_signed_certificate()
    
    # Generate wildcard certificate for subdomains
    wildcard_cert, wildcard_key = cert_manager.generate_wildcard_certificate()
    
    print("✅ Development certificates generated successfully!")
    print(f"📁 Certificate directory: {cert_manager.cert_dir}")
    print(f"🔐 Server certificate: {server_cert}")
    print(f"🔑 Server private key: {server_key}")
    print(f"🏛️  CA certificate: {ca_cert}")
    print(f"🌟 Wildcard certificate: {wildcard_cert}")
    
    return cert_manager

if __name__ == "__main__":
    create_development_certificates()
