#!/usr/bin/env python3
"""
Python LocalTunnel - A minimal LocalTunnel-like tool written in Python
"""

import click
import asyncio
import os
import sys
from pathlib import Path
from rich.console import Console
from rich.panel import Panel
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Confirm
import subprocess
import signal
import threading
import time

# Import our existing modules
from server import start_server
from client import tunnel_client

console = Console()

def print_banner():
    """Print the LocalTunnel banner"""
    banner = Text("🐍 Python LocalTunnel", style="bold blue")
    subtitle = Text("Expose your localhost to the world", style="dim")
    
    panel = Panel(
        f"{banner}\n{subtitle}",
        border_style="blue",
        padding=(1, 2)
    )
    console.print(panel)

def check_dependencies():
    """Check if required dependencies are installed"""
    try:
        import websockets
        import aiohttp
        import click
        import rich
        return True
    except ImportError as e:
        console.print(f"[red]Missing dependency: {e}[/red]")
        console.print("[yellow]Please install dependencies with: pip install -r requerments.txt[/yellow]")
        return False

def validate_port(ctx, param, value):
    """Validate port number"""
    if not (1 <= value <= 65535):
        raise click.BadParameter("Port must be between 1 and 65535")
    return value

def validate_host(ctx, param, value):
    """Validate host parameter"""
    if value and not (value == "localhost" or value.startswith("127.") or value.startswith("0.")):
        raise click.BadParameter("Host must be localhost, 127.x.x.x, or 0.x.x.x")
    return value

@click.group(invoke_without_command=True)
@click.pass_context
def cli(ctx):
    """Python LocalTunnel - Expose your localhost to the world"""
    if ctx.invoked_subcommand is None:
        print_banner()
        click.echo(ctx.get_help())

@cli.command()
@click.option('--port', '-p', default=3000, type=int, callback=validate_port,
              help='Port of your local server (default: 3000)')
@click.option('--host', '-h', default='localhost', callback=validate_host,
              help='Host of your local server (default: localhost)')
@click.option('--server-host', default='localhost',
              help='Tunnel server host (default: localhost)')
@click.option('--server-port', default=8765, type=int,
              help='Tunnel server port (default: 8765)')
@click.option('--subdomain', '-s',
              help='Request a specific subdomain (optional)')
@click.option('--ssl/--no-ssl', default=True,
              help='Use SSL/TLS for secure connections (default: enabled)')
@click.option('--verify-ssl', is_flag=True,
              help='Verify SSL certificates (default: disabled)')
@click.option('--verbose', '-v', is_flag=True,
              help='Enable verbose logging')
def tunnel(port, host, server_host, server_port, subdomain, ssl, verify_ssl, verbose):
    """Create a tunnel to expose your local server"""
    
    if not check_dependencies():
        sys.exit(1)
    
    print_banner()
    
    # Update client configuration
    local_server = f"http://{host}:{port}"
    
    console.print(f"[green]🚀 Starting tunnel...[/green]")
    console.print(f"[dim]Local server: {local_server}[/dim]")
    
    # Determine the correct protocol based on SSL setting
    protocol = "wss" if ssl else "ws"
    console.print(f"[dim]Tunnel server: {protocol}://{server_host}:{server_port}[/dim]")
    
    if subdomain:
        console.print(f"[dim]Requested subdomain: {subdomain}[/dim]")
    
    # Start the tunnel client
    try:
        # Import and modify client configuration
        import client
        client.LOCAL_SERVER = local_server
        client.USE_SSL = ssl
        client.SSL_VERIFY = verify_ssl
        
        # Update logging level
        if verbose:
            import logging
            logging.getLogger().setLevel(logging.DEBUG)
        
        # Run the tunnel client
        asyncio.run(client.tunnel_client(server_host, server_port, ssl))
        
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Tunnel stopped by user[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)

@cli.command()
@click.option('--host', default='0.0.0.0',
              help='Host to bind the server to (default: 0.0.0.0)')
@click.option('--ws-port', default=8765, type=int,
              help='WebSocket server port (default: 8765)')
@click.option('--http-port', default=8081, type=int,
              help='HTTP server port (default: 8081)')
@click.option('--ssl/--no-ssl', default=True,
              help='Use SSL/TLS for secure connections (default: enabled)')
@click.option('--cert-file',
              help='Path to SSL certificate file (default: certs/server.crt)')
@click.option('--key-file',
              help='Path to SSL private key file (default: certs/server.key)')
@click.option('--verbose', '-v', is_flag=True,
              help='Enable verbose logging')
def server(host, ws_port, http_port, ssl, cert_file, key_file, verbose):
    """Start the tunnel server"""
    
    if not check_dependencies():
        sys.exit(1)
    
    print_banner()
    
    console.print(f"[green]🖥️  Starting tunnel server...[/green]")
    console.print(f"[dim]WebSocket: ws://{host}:{ws_port}[/dim]")
    console.print(f"[dim]HTTP: http://{host}:{http_port}[/dim]")
    
    # Update server configuration
    import server as tunnel_server
    
    # Update logging level
    if verbose:
        import logging
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Update server configuration
    if cert_file:
        tunnel_server.SSL_CERT_FILE = cert_file
    if key_file:
        tunnel_server.SSL_KEY_FILE = key_file
    
    # Start the server
    try:
        asyncio.run(tunnel_server.start_server(host, ws_port, http_port, ssl))
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠️  Server stopped by user[/yellow]")
    except Exception as e:
        console.print(f"[red]❌ Error: {e}[/red]")
        sys.exit(1)

@cli.command()
def version():
    """Show version information"""
    print_banner()
    console.print("[dim]Version: 1.0.0[/dim]")
    console.print("[dim]Python LocalTunnel MVP[/dim]")

@cli.command()
def init():
    """Initialize the tunnel server database"""
    if not check_dependencies():
        sys.exit(1)
    
    print_banner()
    
    try:
        # Run the database initialization
        subprocess.run([sys.executable, "init_db.py"], check=True)
        console.print("[green]✅ Database initialized successfully[/green]")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ Failed to initialize database: {e}[/red]")
        sys.exit(1)

@cli.command()
@click.option('--domain', default='localhost',
              help='Domain for the certificate (default: localhost)')
@click.option('--days', default=365, type=int,
              help='Certificate validity in days (default: 365)')
def certs(domain, days):
    """Generate SSL/TLS certificates for development"""
    if not check_dependencies():
        sys.exit(1)
    
    print_banner()
    
    try:
        # Import certificate utilities
        from cert_utils import create_development_certificates
        
        console.print(f"[green]🔐 Generating SSL certificates for {domain}...[/green]")
        
        # Generate certificates
        cert_manager = create_development_certificates()
        
        console.print("[green]✅ SSL certificates generated successfully![/green]")
        console.print(f"[dim]📁 Certificate directory: {cert_manager.cert_dir}[/dim]")
        console.print("[yellow]⚠️  These are self-signed certificates for development only[/yellow]")
        
    except ImportError as e:
        console.print(f"[red]❌ Missing dependency: {e}[/red]")
        console.print("[yellow]Please install SSL dependencies: pip install cryptography pyOpenSSL[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]❌ Failed to generate certificates: {e}[/red]")
        sys.exit(1)

if __name__ == '__main__':
    cli()
