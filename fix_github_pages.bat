@echo off
echo Fixing GitHub Pages deployment...
echo.

REM Check if we're in a git repository
if not exist ".git" (
    echo [ERROR] Not in a git repository
    pause
    exit /b 1
)

REM Check if docs directory exists
if not exist "docs" (
    echo [ERROR] docs directory not found
    pause
    exit /b 1
)

echo [INFO] Switching to gh-pages branch...
git checkout gh-pages

echo [INFO] Removing all files from gh-pages branch...
git rm -rf . 2>nul

echo [INFO] Copying documentation files...
xcopy /E /I /Y "docs" .

echo [INFO] Adding all files...
git add .

echo [INFO] Committing changes...
git commit -m "Update documentation site" 2>nul || echo [INFO] No changes to commit

echo [INFO] Pushing to gh-pages branch...
git push origin gh-pages

echo [INFO] Switching back to main branch...
git checkout main

echo [SUCCESS] GitHub Pages branch updated!
echo [INFO] Your site should be available at: https://druti2k.github.io/pytunnel/
echo [INFO] It may take a few minutes to update.
echo.
pause
