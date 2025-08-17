# 🚀 PyTunnel Public Deployment Guide

## 🌐 **Deployment Options**

### **Option A: DigitalOcean Droplet (Recommended for MVP)**
- **Cost**: $6-12/month
- **Ease**: Beginner-friendly
- **Performance**: Good for starting out

### **Option B: AWS EC2**
- **Cost**: $10-20/month
- **Ease**: More complex but scalable
- **Performance**: Enterprise-grade

### **Option C: Google Cloud Platform**
- **Cost**: $10-15/month
- **Ease**: Medium complexity
- **Performance**: Excellent

## 🎯 **Recommended: DigitalOcean Deployment**

### **Step 1: Create Droplet**
```bash
# 1. Sign up at digitalocean.com
# 2. Create new droplet
# 3. Choose Ubuntu 22.04 LTS
# 4. Select Basic plan ($6/month)
# 5. Choose datacenter close to your users
# 6. Add SSH key for security
```

### **Step 2: Server Setup**
```bash
# SSH into your server
ssh root@your-server-ip

# Update system
apt update && apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Docker Compose
apt install docker-compose -y

# Create user (optional but recommended)
adduser pytunnel
usermod -aG docker pytunnel
```

### **Step 3: Deploy PyTunnel**
```bash
# Clone your repository
git clone https://github.com/druti2k/pytunnel.git
cd pytunnel

# Set up environment
cp env.production.example .env.production
nano .env.production  # Edit with your domain

# Build and start
docker-compose -f docker-compose.prod.yml up -d
```

### **Step 4: Domain & SSL Setup**
```bash
# 1. Buy domain (e.g., pytunnel.com)
# 2. Point DNS to your server IP
# 3. Set up SSL with Let's Encrypt
# 4. Configure nginx for domain routing
```

## 🔒 **Security Setup**

### **Firewall Configuration**
```bash
# Allow only necessary ports
ufw allow 22    # SSH
ufw allow 80    # HTTP
ufw allow 443   # HTTPS
ufw enable
```

### **SSL Certificate Setup**
```bash
# Install Certbot
apt install certbot python3-certbot-nginx

# Get SSL certificate
certbot --nginx -d pytunnel.yourdomain.com
```

## 📊 **Monitoring & Maintenance**

### **Health Checks**
```bash
# Check service status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Monitor resources
htop
df -h
```

### **Backup Strategy**
```bash
# Backup configuration
tar -czf pytunnel-backup-$(date +%Y%m%d).tar.gz .env.production certs/ logs/

# Backup database (if using)
docker exec pytunnel-server sqlite3 /app/auth.db .dump > backup.sql
```

## 💰 **Cost Breakdown**

### **Monthly Costs (DigitalOcean)**
- **Droplet**: $6-12/month
- **Domain**: $10-15/year
- **SSL**: Free (Let's Encrypt)
- **Total**: ~$7-13/month

### **Scaling Costs**
- **More users**: Upgrade to $24/month droplet
- **Multiple regions**: Add more droplets
- **CDN**: $10-20/month for global performance

## 🚀 **Go-Live Checklist**

- [ ] Server deployed and running
- [ ] Domain configured and pointing to server
- [ ] SSL certificate installed
- [ ] Firewall configured
- [ ] Monitoring set up
- [ ] Documentation site ready
- [ ] User registration system (optional)
- [ ] Rate limiting configured
- [ ] Backup system in place
- [ ] Support contact information ready

## 🔧 **Troubleshooting**

### **Common Issues**
1. **Port conflicts**: Check if ports 80/443 are free
2. **SSL errors**: Verify domain DNS settings
3. **Performance**: Monitor server resources
4. **Security**: Regular security updates

### **Support Resources**
- GitHub Issues: Report bugs
- Documentation: User guides
- Community: Discord/Slack (future)
