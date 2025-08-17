#!/bin/bash

# Python LocalTunnel Production Deployment Script
set -e

echo "🚀 Deploying Python LocalTunnel to Production"

# Configuration
DOMAIN=${1:-"your-domain.com"}
AUTH_TOKEN=${2:-$(openssl rand -hex 32)}
ENVIRONMENT=${3:-"production"}

echo "📋 Configuration:"
echo "   Domain: $DOMAIN"
echo "   Environment: $ENVIRONMENT"
echo "   Auth Token: $AUTH_TOKEN"

# Create necessary directories
echo "📁 Creating directories..."
mkdir -p certs logs

# Generate SSL certificates if they don't exist
if [ ! -f "certs/server.crt" ] || [ ! -f "certs/server.key" ]; then
    echo "🔐 Generating SSL certificates..."
    python pytunnel.py certs
fi

# Update configuration files
echo "⚙️  Updating configuration..."
sed -i "s/your-domain.com/$DOMAIN/g" docker-compose.yml
sed -i "s/your-secret-token/$AUTH_TOKEN/g" docker-compose.yml
sed -i "s/your-domain.com/$DOMAIN/g" nginx.conf

# Build and start services
echo "🐳 Building and starting Docker services..."
docker-compose build

if [ "$ENVIRONMENT" = "production" ]; then
    echo "🏭 Starting production stack with nginx..."
    docker-compose --profile production up -d
else
    echo "🔧 Starting development stack..."
    docker-compose up -d pytunnel-server
fi

# Wait for services to be ready
echo "⏳ Waiting for services to be ready..."
sleep 10

# Health check
echo "🏥 Running health checks..."
if curl -f http://localhost:8081/health > /dev/null 2>&1; then
    echo "✅ Tunnel server is healthy"
else
    echo "❌ Tunnel server health check failed"
    exit 1
fi

if [ "$ENVIRONMENT" = "production" ]; then
    if curl -f http://localhost/health > /dev/null 2>&1; then
        echo "✅ Nginx is healthy"
    else
        echo "❌ Nginx health check failed"
        exit 1
    fi
fi

echo "🎉 Deployment completed successfully!"
echo ""
echo "📊 Service Status:"
docker-compose ps
echo ""
echo "🔗 Access URLs:"
echo "   WebSocket: wss://$DOMAIN/ws"
echo "   HTTP: https://$DOMAIN"
echo ""
echo "🔑 Auth Token: $AUTH_TOKEN"
echo "   (Save this for client connections)"
echo ""
echo "📝 Next steps:"
echo "   1. Update your DNS to point $DOMAIN to this server"
echo "   2. Use the auth token in your client connections"
echo "   3. Test the tunnel with: python test_tunnel.py"
