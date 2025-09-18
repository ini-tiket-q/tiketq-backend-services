@echo off
echo Building and starting TiketQ Backend Services with Docker...

echo Stopping any existing containers...
docker-compose down

echo Building Docker images...
docker-compose build

echo Starting all services...
docker-compose up -d

echo Waiting for services to start...
timeout /t 10

echo Checking service status...
docker-compose ps

echo Starting Cloudflare Tunnel...
rem PERINTAH DI BAWAH INI SUDAH DIPERBAIKI DENGAN MENAMBAHKAN UUID TUNNEL
start "Cloudflare Tunnel" cloudflared tunnel --config "%USERPROFILE%\.cloudflared\config.yml" run 16d1dcd7-5c43-4c42-aac5-fc05a0cf2c5f

echo.
echo All services started! Your sites should be live in a moment.
echo.
pause