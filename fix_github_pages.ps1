Write-Host "Fixing GitHub Pages deployment..." -ForegroundColor Green
Write-Host ""

# Check if we're in a git repository
if (-not (Test-Path ".git")) {
    Write-Host "[ERROR] Not in a git repository" -ForegroundColor Red
    Read-Host "Press Enter to continue"
    exit 1
}

# Check if docs directory exists
if (-not (Test-Path "docs")) {
    Write-Host "[ERROR] docs directory not found" -ForegroundColor Red
    Read-Host "Press Enter to continue"
    exit 1
}

Write-Host "[INFO] Switching to gh-pages branch..." -ForegroundColor Yellow
git checkout gh-pages

Write-Host "[INFO] Removing all files from gh-pages branch..." -ForegroundColor Yellow
git rm -rf . 2>$null

Write-Host "[INFO] Copying documentation files..." -ForegroundColor Yellow
# Use PowerShell Copy-Item instead of xcopy
Copy-Item -Path "docs\*" -Destination "." -Recurse -Force

Write-Host "[INFO] Adding all files..." -ForegroundColor Yellow
git add .

Write-Host "[INFO] Committing changes..." -ForegroundColor Yellow
git commit -m "Update documentation site" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[INFO] No changes to commit" -ForegroundColor Yellow
}

Write-Host "[INFO] Pushing to gh-pages branch..." -ForegroundColor Yellow
git push origin gh-pages

Write-Host "[INFO] Switching back to main branch..." -ForegroundColor Yellow
git checkout main

Write-Host "[SUCCESS] GitHub Pages branch updated!" -ForegroundColor Green
Write-Host "[INFO] Your site should be available at: https://druti2k.github.io/pytunnel/" -ForegroundColor Cyan
Write-Host "[INFO] It may take a few minutes to update." -ForegroundColor Yellow
Write-Host ""
Read-Host "Press Enter to continue"
