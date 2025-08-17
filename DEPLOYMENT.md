# Python LocalTunnel - Production Deployment Guide

## 🧪 Testing the Project

### Quick Test (Development)
```bash
# 1. Start the tunnel server
python pytunnel.py server

# 2. In another terminal, run the test suite
python test_tunnel.py

# 3. Manual test - create a tunnel
python pytunnel.py tunnel --port 3000
```

### Comprehensive Testing
```bash
# Run all tests including integration tests
python -m pytest tests/ -v

# Run with coverage
python -m pytest tests/ --cov=. --cov-report=html
```

## 🚀 Production Deployment

### Prerequisites
- Docker and Docker Compose installed
- Domain name pointing to your server
- SSL certificates (or use Let's Encrypt)

### Option 1: Docker Deployment (Recommended)

#### 1. Clone and Setup
```bash
git clone <your-repo>
cd pytunnel
chmod +x deploy.sh
```

#### 2. Deploy
```bash
# Basic deployment
./deploy.sh your-domain.com

# With custom auth token
./deploy.sh your-domain.com your-secret-token

# Development deployment (without nginx)
./deploy.sh localhost dev-token development
```

#### 3. Verify Deployment
```bash
# Check service status
docker-compose ps

# View logs
docker-compose logs -f pytunnel-server

# Test health endpoint
curl http://localhost:8081/health
```

### Option 2: Manual Deployment

#### 1. Install Dependencies
```bash
pip install -r requerments.txt
```

#### 2. Generate SSL Certificates
```bash
python pytunnel.py certs
```

#### 3. Configure Environment
```bash
cp config.production.env .env
# Edit .env with your settings
```

#### 4. Start Server
```bash
python pytunnel.py server
```

### Option 3: Systemd Service

#### 1. Create Service File
```bash
sudo nano /etc/systemd/system/pytunnel.service
```

```ini
[Unit]
Description=Python LocalTunnel Server
After=network.target

[Service]
Type=simple
User=pytunnel
WorkingDirectory=/opt/pytunnel
Environment=PATH=/opt/pytunnel/venv/bin
ExecStart=/opt/pytunnel/venv/bin/python pytunnel.py server
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 2. Enable and Start
```bash
sudo systemctl enable pytunnel
sudo systemctl start pytunnel
sudo systemctl status pytunnel
```

## 🔧 Configuration

### Environment Variables
- `USE_SSL`: Enable SSL/TLS (true/false)
- `PUBLIC_HOST`: Your domain name
- `AUTH_TOKEN`: Secret token for authentication
- `WS_PORT`: WebSocket port (default: 8765)
- `HTTP_PORT`: HTTP port (default: 8081)

### SSL Configuration
```bash
# Generate certificates
python pytunnel.py certs

# Or use Let's Encrypt
certbot certonly --standalone -d your-domain.com
```

## 📊 Monitoring and Logging

### Logs
```bash
# Docker logs
docker-compose logs -f pytunnel-server

# File logs (if configured)
tail -f logs/pytunnel.log
```

### Health Checks
```bash
# Check server health
curl http://localhost:8081/health

# Check nginx health (if using)
curl http://localhost/health
```

### Metrics (Optional)
Enable metrics by setting `ENABLE_METRICS=true` in your environment.

## 🔒 Security Considerations

### 1. Authentication
- Use strong, unique AUTH_TOKEN
- Rotate tokens regularly
- Consider implementing user authentication

### 2. Rate Limiting
- Configure rate limits in nginx
- Monitor for abuse
- Implement IP blocking if needed

### 3. SSL/TLS
- Use valid SSL certificates
- Enable HSTS
- Use strong cipher suites

### 4. Network Security
- Configure firewall rules
- Use VPN for admin access
- Monitor network traffic

## 🚨 Troubleshooting

### Common Issues

#### 1. WebSocket Connection Failed
```bash
# Check if server is running
docker-compose ps

# Check logs
docker-compose logs pytunnel-server

# Test WebSocket port
telnet localhost 8765
```

#### 2. SSL Certificate Issues
```bash
# Regenerate certificates
python pytunnel.py certs

# Check certificate validity
openssl x509 -in certs/server.crt -text -noout
```

#### 3. Port Already in Use
```bash
# Find process using port
lsof -i :8765
lsof -i :8081

# Kill process
kill -9 <PID>
```

#### 4. Docker Issues
```bash
# Rebuild containers
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```

### Performance Tuning

#### 1. Increase Connection Limits
```bash
# In nginx.conf
worker_connections 2048;
```

#### 2. Optimize Python
```bash
# Use uvicorn for better performance
pip install uvicorn
uvicorn server:app --host 0.0.0.0 --port 8081
```

#### 3. Memory Optimization
```bash
# In docker-compose.yml
services:
  pytunnel-server:
    deploy:
      resources:
        limits:
          memory: 512M
        reservations:
          memory: 256M
```

## 📈 Scaling

### Horizontal Scaling
```bash
# Scale the service
docker-compose up -d --scale pytunnel-server=3
```

### Load Balancing
Use nginx or HAProxy for load balancing multiple tunnel servers.

### Database (Optional)
For persistent tunnel management, consider adding a database:
- PostgreSQL for tunnel metadata
- Redis for session management

## 🔄 Updates and Maintenance

### Updating the Application
```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose down
docker-compose build
docker-compose up -d
```

### Backup
```bash
# Backup certificates
tar -czf backup-$(date +%Y%m%d).tar.gz certs/ logs/

# Backup configuration
cp docker-compose.yml backup/
cp nginx.conf backup/
```

### Monitoring
- Set up log aggregation (ELK stack)
- Configure alerts for downtime
- Monitor resource usage
- Track tunnel usage metrics

## 📞 Support

For issues and questions:
1. Check the troubleshooting section
2. Review logs for error messages
3. Test with the provided test suite
4. Create an issue in the repository

## 🎯 Production Checklist

- [ ] SSL certificates configured
- [ ] Domain DNS configured
- [ ] Firewall rules set
- [ ] Monitoring configured
- [ ] Logs configured
- [ ] Backup strategy in place
- [ ] Security measures implemented
- [ ] Performance optimized
- [ ] Documentation updated
- [ ] Team trained on deployment
