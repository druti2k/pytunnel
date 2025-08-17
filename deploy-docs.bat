@echo off
setlocal enabledelayedexpansion

REM PyTunnel Documentation Site Deployment Script (Windows)
echo 🚀 PyTunnel Documentation Site Deployment Script
echo ================================================
echo.

REM Check if platform is specified
if "%1"=="" (
    echo [ERROR] Platform must be specified
    echo.
    echo Usage: %0 PLATFORM [DOMAIN]
    echo.
    echo Supported platforms:
    echo   netlify     - Deploy to Netlify (free hosting)
    echo   vercel      - Deploy to Vercel (free hosting)
    echo   github-pages - Deploy to GitHub Pages
    echo   s3          - Deploy to AWS S3 + CloudFront
    echo.
    echo Examples:
    echo   %0 netlify
    echo   %0 vercel docs.pytunnel.com
    echo   %0 github-pages
    echo.
    pause
    exit /b 1
)

set PLATFORM=%1
set DOMAIN=%2
set BUILD_DIR=docs

echo [INFO] Starting deployment to %PLATFORM%...
echo.

REM Check if docs directory exists
if not exist "%BUILD_DIR%" (
    echo [ERROR] Documentation directory '%BUILD_DIR%' not found
    pause
    exit /b 1
)

REM Deploy based on platform
if "%PLATFORM%"=="netlify" goto deploy_netlify
if "%PLATFORM%"=="vercel" goto deploy_vercel
if "%PLATFORM%"=="github-pages" goto deploy_github_pages
if "%PLATFORM%"=="s3" goto deploy_s3

echo [ERROR] Unsupported platform: %PLATFORM%
pause
exit /b 1

:deploy_netlify
echo [INFO] Deploying to Netlify...
echo.

REM Check if Netlify CLI is installed
netlify --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing Netlify CLI...
    npm install -g netlify-cli
)

REM Create netlify.toml if it doesn't exist
if not exist "netlify.toml" (
    echo [INFO] Creating netlify.toml configuration...
    (
        echo [build]
        echo   publish = "docs"
        echo   command = "echo 'No build command needed'"
        echo.
        echo [build.environment]
        echo   NODE_VERSION = "18"
        echo.
        echo [[redirects]]
        echo   from = "/*"
        echo   to = "/index.html"
        echo   status = 200
    ) > netlify.toml
)

REM Deploy
if defined DOMAIN (
    netlify deploy --prod --dir="%BUILD_DIR%" --site="%DOMAIN%"
) else (
    netlify deploy --prod --dir="%BUILD_DIR%"
)

if errorlevel 1 (
    echo [ERROR] Netlify deployment failed
    pause
    exit /b 1
)

echo [SUCCESS] Successfully deployed to Netlify!
goto end

:deploy_vercel
echo [INFO] Deploying to Vercel...
echo.

REM Check if Vercel CLI is installed
vercel --version >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing Vercel CLI...
    npm install -g vercel
)

REM Create vercel.json if it doesn't exist
if not exist "vercel.json" (
    echo [INFO] Creating vercel.json configuration...
    (
        echo {
        echo   "version": 2,
        echo   "builds": [
        echo     {
        echo       "src": "docs/**/*",
        echo       "use": "@vercel/static"
        echo     }
        echo   ],
        echo   "routes": [
        echo     {
        echo       "src": "/(.*)",
        echo       "dest": "/docs/index.html"
        echo     }
        echo   ]
        echo }
    ) > vercel.json
)

REM Deploy
if defined DOMAIN (
    vercel --prod --cwd="%BUILD_DIR%" --name="%DOMAIN%"
) else (
    vercel --prod --cwd="%BUILD_DIR%"
)

if errorlevel 1 (
    echo [ERROR] Vercel deployment failed
    pause
    exit /b 1
)

echo [SUCCESS] Successfully deployed to Vercel!
goto end

:deploy_github_pages
echo [INFO] Deploying to GitHub Pages...
echo.

REM Check if git is available
git --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Git is required for GitHub Pages deployment
    echo Please install Git from: https://git-scm.com/
    pause
    exit /b 1
)

REM Check if we're in a git repository
if not exist ".git" (
    echo [ERROR] Not in a git repository. Please initialize git first.
    pause
    exit /b 1
)

echo [INFO] Creating gh-pages branch...
git checkout -b gh-pages 2>nul || git checkout gh-pages

echo [INFO] Copying documentation files...
xcopy /E /I /Y "%BUILD_DIR%" .

echo [INFO] Committing and pushing changes...
git add .
git commit -m "Deploy documentation site" 2>nul || echo [INFO] No changes to commit
git push origin gh-pages

echo [INFO] Returning to main branch...
git checkout main

echo [SUCCESS] Successfully deployed to GitHub Pages!
echo [INFO] Enable GitHub Pages in your repository settings and select gh-pages branch
goto end

:deploy_s3
echo [INFO] Deploying to AWS S3...
echo.

REM Check if AWS CLI is available
aws --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] AWS CLI is required for S3 deployment
    echo Please install from: https://aws.amazon.com/cli/
    pause
    exit /b 1
)

REM Check AWS credentials
aws sts get-caller-identity >nul 2>&1
if errorlevel 1 (
    echo [ERROR] AWS credentials not configured
    echo Please run: aws configure
    pause
    exit /b 1
)

echo [INFO] Enter S3 bucket name:
set /p BUCKET_NAME=

if "!BUCKET_NAME!"=="" (
    echo [ERROR] Bucket name is required
    pause
    exit /b 1
)

echo [INFO] Syncing files to S3...
aws s3 sync "%BUILD_DIR%" "s3://!BUCKET_NAME!" --delete

echo [INFO] Configuring bucket for static website hosting...
aws s3 website "s3://!BUCKET_NAME!" --index-document index.html --error-document index.html

echo [SUCCESS] Successfully deployed to S3!
echo [INFO] Website URL: http://!BUCKET_NAME!.s3-website-$(aws configure get region).amazonaws.com

if defined DOMAIN (
    echo [INFO] Configure CloudFront for custom domain: %DOMAIN%
)
goto end

:end
echo.
echo [SUCCESS] Deployment completed successfully!
echo [INFO] Your documentation site is now live!
echo.
pause
