# 🧪 Python LocalTunnel MVP

A minimal LocalTunnel-like tool written in Python using `websockets` and `socket`. This tool allows you to expose your local development server (e.g., on `localhost:3000`) to the internet through a public tunnel server.

---

## 🚀 Features

- Tunnel server using WebSockets
- Tunnel client to forward local TCP traffic
- Simple, minimal, and hackable
- Built entirely with Python
- Secure authentication system
- SSL/TLS support
- HTTP proxy capabilities

---

## 🛠️ Tech Stack

- `asyncio` – for asynchronous event loops
- `websockets` – for real-time communication between client and server
- `socket` – for raw TCP forwarding
- `aiohttp` – for HTTP server and proxy functionality
- SQLite – for authentication database

---

## 📂 Project Structure

```
.
├── server.py          # Main tunnel server implementation
├── client.py          # Tunnel client for forwarding traffic
├── auth_utils.py      # Authentication utilities
├── init_db.py         # Database initialization script
├── auth.db           # SQLite database for authentication
└── requirements.txt   # Project dependencies
```

## 🚀 Getting Started

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Initialize the database:
   ```bash
   python init_db.py
   ```

3. Start the tunnel server:
   ```bash
   python server.py
   ```

4. Start the tunnel client:
   ```bash
   python client.py
   ```

## 🔒 Security

- Authentication is required for tunnel connections
- SSL/TLS encryption for WebSocket connections
- Token-based authentication system

## ⚙️ Configuration

- Server port: 8765 (WebSocket) and 3000 (HTTP)
- Authentication token can be set via AUTH_TOKEN environment variable
- SSL certificates required for secure connections

---

## 📝 Next Steps

1. Add proper error handling and reconnection logic
2. Implement request/response handling in the HTTP proxy
3. Add support for custom subdomains
4. Create a proper CLI interface
5. Add logging and monitoring capabilities
6. Implement rate limiting and security measures
7. Add tests and documentation

