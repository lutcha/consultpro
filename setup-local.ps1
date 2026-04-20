#!/usr/bin/env pwsh
# Setup script for local development (no Docker required)
# Uses SQLite instead of PostgreSQL

$ErrorActionPreference = "Stop"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ConsultPro Backend - Local Setup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Check Python
$pythonVersion = python --version 2>&1
Write-Host "Python version: $pythonVersion"

# Create virtual environment
if (-not (Test-Path ".venv")) {
    Write-Host "`nCreating virtual environment..." -ForegroundColor Yellow
    python -m venv .venv
}

# Activate virtual environment
Write-Host "`nActivating virtual environment..." -ForegroundColor Yellow
& .\.venv\Scripts\Activate.ps1

# Upgrade pip
Write-Host "`nUpgrading pip..." -ForegroundColor Yellow
python -m pip install --upgrade pip

# Install requirements
Write-Host "`nInstalling dependencies..." -ForegroundColor Yellow
pip install -r requirements/local.txt

# Create .env if not exists
if (-not (Test-Path ".env")) {
    Write-Host "`nCreating .env file..." -ForegroundColor Yellow
    Copy-Item ".env.example" ".env"
}

# Set Django settings module for local
$env:DJANGO_SETTINGS_MODULE = "config.settings.local"

# Run migrations
Write-Host "`nRunning migrations..." -ForegroundColor Yellow
python manage.py migrate

# Load fixtures
Write-Host "`nLoading fixtures..." -ForegroundColor Yellow
python manage.py loaddata fixtures/initial_data.json

# Create media directory
if (-not (Test-Path "media")) {
    New-Item -ItemType Directory -Path "media" | Out-Null
}

Write-Host "`n========================================" -ForegroundColor Green
Write-Host "  Setup complete!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "`nTo start the server, run:" -ForegroundColor Cyan
Write-Host "  .\.venv\Scripts\Activate.ps1" -ForegroundColor White
Write-Host "  `$env:DJANGO_SETTINGS_MODULE = 'config.settings.local'" -ForegroundColor White
Write-Host "  python manage.py runserver" -ForegroundColor White
Write-Host "`nAPI will be available at: http://127.0.0.1:8000" -ForegroundColor Cyan
Write-Host "Swagger docs at: http://127.0.0.1:8000/api/docs/" -ForegroundColor Cyan
Write-Host "`nDefault login credentials:" -ForegroundColor Yellow
Write-Host "  ana.silva@consultpro.com / password123" -ForegroundColor White
Write-Host "  carlos.mendes@consultpro.com / password123" -ForegroundColor White
Write-Host "  maria.santos@consultpro.com / password123" -ForegroundColor White
