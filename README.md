# 🧪 Python LocalTunnel MVP

A minimal LocalTunnel-like tool written in Python using `websockets` and `socket`. This tool allows you to expose your local development server (e.g., on `localhost:3000`) to the internet through a public tunnel server.

---

## 🚀 Features

- **Tunnel server** using WebSockets
- **Tunnel client** to forward local TCP traffic
- **Professional CLI** interface with rich output
- **HTTPS/TLS support** with automatic certificate generation
- **SSL/TLS encryption** for secure connections
- **Self-signed certificates** for development
- **HTTP proxy capabilities**
- **Cross-platform** support (Windows, macOS, Linux)
- **Simple and minimal** - easy to understand and modify

---

## 🛠️ Tech Stack

- **`asyncio`** – for asynchronous event loops
- **`websockets`** – for real-time communication between client and server
- **`aiohttp`** – for HTTP server and proxy functionality
- **`click`** – for professional CLI interface
- **`rich`** – for beautiful terminal output
- **`cryptography`** – for SSL/TLS certificate generation
- **`pyOpenSSL`** – for SSL/TLS support
- **SQLite** – for authentication database

---

## 📂 Project Structure

```
.
├── pytunnel.py        # CLI entry point (main interface)
├── server.py          # Main tunnel server implementation
├── client.py          # Tunnel client for forwarding traffic
├── cert_utils.py      # SSL/TLS certificate management
├── auth_utils.py      # Authentication utilities
├── init_db.py         # Database initialization script
├── auth.db           # SQLite database for authentication
├── requerments.txt   # Project dependencies (note: filename has typo)
├── setup.py          # Package installation script
├── pytunnel.bat      # Windows CLI wrapper
├── pytunnel.sh       # Unix CLI wrapper
├── certs/            # SSL certificates directory
└── .venv/            # Virtual environment directory
```

## 🚀 Getting Started

### **Option 1: Using the CLI (Recommended)**

1. **Activate the virtual environment**:
   
   **Windows (PowerShell)**:
   ```powershell
   .venv\Scripts\Activate.ps1
   ```
   
   **Windows (Command Prompt)**:
   ```cmd
   .venv\Scripts\activate.bat
   ```
   
   **macOS/Linux**:
   ```bash
   source .venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requerments.txt
   ```

3. **Initialize the database**:
   ```bash
   python pytunnel.py init
   ```

4. **Start the tunnel server**:
   ```bash
   python pytunnel.py server
   ```

5. **Create a tunnel** (in a new terminal):
   ```bash

   ```

### **Option 2: Manual Setup**

1. **Activate the virtual environment** (same as above)

2. **Install dependencies**:
   ```bash
   pip install -r requerments.txt
   ```

3. **Initialize the database**:
   ```bash
   python init_db.py
   ```

4. **Start the tunnel server**:
   ```bash
   python server.py
   ```

5. **Start the tunnel client** (in a new terminal):
   ```bash
   python client.py
   ```

### **CLI Usage Examples**

```bash
# Basic tunnel to port 3000 (with SSL enabled by default)
python pytunnel.py tunnel --port 3000

# Using the Windows batch file
.\pytunnel.bat tunnel --port 3000

# Tunnel without SSL
python pytunnel.py tunnel --port 3000 --no-ssl

# Tunnel with SSL verification
python pytunnel.py tunnel --port 3000 --verify-ssl

# Tunnel with custom host
python pytunnel.py tunnel --port 8000 --host 127.0.0.1

# Verbose logging
python pytunnel.py tunnel --port 3000 --verbose

# Custom server
python pytunnel.py tunnel --port 3000 --server-host my-server.com --server-port 8765

# Start server with SSL (default)
python pytunnel.py server --ssl --verbose

# Start server without SSL
python pytunnel.py server --no-ssl

# Start server with custom SSL certificates
python pytunnel.py server --ssl --cert-file my-cert.crt --key-file my-key.key

# Generate SSL certificates
python pytunnel.py certs

# Generate certificates for custom domain
python pytunnel.py certs --domain mydomain.com --days 730

# Quick start with SSL (Windows)
.\pytunnel.bat certs
.\pytunnel.bat server --ssl
# In another terminal:
.\pytunnel.bat tunnel --port 3000

# Show help
python pytunnel.py --help
python pytunnel.py tunnel --help
python pytunnel.py server --help
```

## 🔒 Security

- **SSL/TLS encryption** for all connections (enabled by default)
- **Self-signed certificates** automatically generated for development
- **Certificate management** with custom domain support
- **Secure WebSocket connections** (WSS) when SSL is enabled
- **HTTPS support** for tunnel endpoints
- **Certificate verification** options for production use

## ⚙️ Configuration

- **WebSocket server**: 8765 (WSS when SSL enabled)
- **HTTP server**: 8081 (HTTPS when SSL enabled)
- **SSL/TLS**: Enabled by default, can be disabled with `--no-ssl`
- **Certificate generation**: Automatic self-signed certificates
- **Custom certificates**: Support for custom cert/key files
- **Environment variables**: `USE_SSL`, `SSL_CERT_FILE`, `SSL_KEY_FILE`

---

## 📝 Next Steps

1. ✅ **Professional CLI interface** - Complete
2. ✅ **HTTPS/TLS support** - Complete
3. **Docker containerization** - Easy deployment
4. **Testing framework** - Unit and integration tests
5. **Better error handling** - Robust connection management
6. **Monitoring & metrics** - Health checks and analytics
7. **Production deployment** - Cloud infrastructure setup

---

## 👨‍💻 Credits

### **Created by:**
[@druti2k](https://github.com/druti2k)

### **Inspired by:**
[Localtunnel](https://localtunnel.me/) - Created by [@defunctzombie](https://github.com/defunctzombie)

### **Support this project:**
- ⭐ **Star the repository** on [GitHub](https://github.com/druti2k/pytunnel)
- 🐛 **Report issues** and suggest features
- 🔧 **Contribute** to the codebase
- 📢 **Share** with other developers

---

**PyTunnel** - *View the project on [GitHub](https://github.com/druti2k/pytunnel)*

