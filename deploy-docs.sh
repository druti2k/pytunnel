#!/bin/bash

# PyTunnel Documentation Site Deployment Script
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Function to show usage
show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -p, --platform PLATFORM    Deployment platform (netlify, vercel, github-pages, s3)"
    echo "  -d, --domain DOMAIN        Custom domain for the site"
    echo "  -h, --help                 Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 --platform netlify"
    echo "  $0 --platform vercel --domain docs.pytunnel.com"
    echo "  $0 --platform github-pages"
    echo ""
    echo "Supported platforms:"
    echo "  - netlify: Deploy to Netlify (free hosting)"
    echo "  - vercel: Deploy to Vercel (free hosting)"
    echo "  - github-pages: Deploy to GitHub Pages"
    echo "  - s3: Deploy to AWS S3 + CloudFront"
}

# Default values
PLATFORM=""
DOMAIN=""
BUILD_DIR="docs"

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -p|--platform)
            PLATFORM="$2"
            shift 2
            ;;
        -d|--domain)
            DOMAIN="$2"
            shift 2
            ;;
        -h|--help)
            show_usage
            exit 0
            ;;
        *)
            print_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
    esac
done

# Check if platform is specified
if [[ -z "$PLATFORM" ]]; then
    print_error "Platform must be specified"
    show_usage
    exit 1
fi

# Check if docs directory exists
if [[ ! -d "$BUILD_DIR" ]]; then
    print_error "Documentation directory '$BUILD_DIR' not found"
    exit 1
fi

print_status "Starting deployment to $PLATFORM..."

case $PLATFORM in
    netlify)
        deploy_netlify
        ;;
    vercel)
        deploy_vercel
        ;;
    github-pages)
        deploy_github_pages
        ;;
    s3)
        deploy_s3
        ;;
    *)
        print_error "Unsupported platform: $PLATFORM"
        exit 1
        ;;
esac

# Function to deploy to Netlify
deploy_netlify() {
    print_status "Deploying to Netlify..."
    
    if ! command_exists netlify; then
        print_status "Installing Netlify CLI..."
        npm install -g netlify-cli
    fi
    
    # Create netlify.toml if it doesn't exist
    if [[ ! -f "netlify.toml" ]]; then
        cat > netlify.toml << EOF
[build]
  publish = "docs"
  command = "echo 'No build command needed'"

[build.environment]
  NODE_VERSION = "18"

[[redirects]]
  from = "/*"
  to = "/index.html"
  status = 200
EOF
        print_status "Created netlify.toml configuration"
    fi
    
    # Deploy
    if [[ -n "$DOMAIN" ]]; then
        netlify deploy --prod --dir="$BUILD_DIR" --site="$DOMAIN"
    else
        netlify deploy --prod --dir="$BUILD_DIR"
    fi
    
    print_success "Successfully deployed to Netlify!"
}

# Function to deploy to Vercel
deploy_vercel() {
    print_status "Deploying to Vercel..."
    
    if ! command_exists vercel; then
        print_status "Installing Vercel CLI..."
        npm install -g vercel
    fi
    
    # Create vercel.json if it doesn't exist
    if [[ ! -f "vercel.json" ]]; then
        cat > vercel.json << EOF
{
  "version": 2,
  "builds": [
    {
      "src": "docs/**/*",
      "use": "@vercel/static"
    }
  ],
  "routes": [
    {
      "src": "/(.*)",
      "dest": "/docs/index.html"
    }
  ]
}
EOF
        print_status "Created vercel.json configuration"
    fi
    
    # Deploy
    if [[ -n "$DOMAIN" ]]; then
        vercel --prod --cwd="$BUILD_DIR" --name="$DOMAIN"
    else
        vercel --prod --cwd="$BUILD_DIR"
    fi
    
    print_success "Successfully deployed to Vercel!"
}

# Function to deploy to GitHub Pages
deploy_github_pages() {
    print_status "Deploying to GitHub Pages..."
    
    if ! command_exists git; then
        print_error "Git is required for GitHub Pages deployment"
        exit 1
    fi
    
    # Check if we're in a git repository
    if [[ ! -d ".git" ]]; then
        print_error "Not in a git repository. Please initialize git first."
        exit 1
    fi
    
    # Create gh-pages branch and deploy
    git checkout -b gh-pages 2>/dev/null || git checkout gh-pages
    
    # Copy docs to root
    cp -r "$BUILD_DIR"/* .
    
    # Commit and push
    git add .
    git commit -m "Deploy documentation site" || true
    git push origin gh-pages
    
    # Go back to main branch
    git checkout main
    
    print_success "Successfully deployed to GitHub Pages!"
    print_status "Enable GitHub Pages in your repository settings and select gh-pages branch"
}

# Function to deploy to AWS S3
deploy_s3() {
    print_status "Deploying to AWS S3..."
    
    if ! command_exists aws; then
        print_error "AWS CLI is required for S3 deployment"
        print_status "Install from: https://aws.amazon.com/cli/"
        exit 1
    fi
    
    # Check AWS credentials
    if ! aws sts get-caller-identity >/dev/null 2>&1; then
        print_error "AWS credentials not configured"
        print_status "Run: aws configure"
        exit 1
    fi
    
    # Get bucket name from user
    read -p "Enter S3 bucket name: " BUCKET_NAME
    
    if [[ -z "$BUCKET_NAME" ]]; then
        print_error "Bucket name is required"
        exit 1
    fi
    
    # Sync files to S3
    aws s3 sync "$BUILD_DIR" "s3://$BUCKET_NAME" --delete
    
    # Configure bucket for static website hosting
    aws s3 website "s3://$BUCKET_NAME" --index-document index.html --error-document index.html
    
    print_success "Successfully deployed to S3!"
    print_status "Website URL: http://$BUCKET_NAME.s3-website-$(aws configure get region).amazonaws.com"
    
    if [[ -n "$DOMAIN" ]]; then
        print_status "Configure CloudFront for custom domain: $DOMAIN"
    fi
}

print_success "Deployment completed successfully!"
print_status "Your documentation site is now live!"
