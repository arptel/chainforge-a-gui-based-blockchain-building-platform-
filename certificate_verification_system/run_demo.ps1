# PowerShell Script to Launch the ChainForge Certificate Demo
# Run this from the certificate_verification_system directory

Write-Host "=========================================" -ForegroundColor Cyan
Write-Host " Starting ChainForge Demo Ecosystem..." -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan

$CurrentDir = Get-Location

# 1. Start Blockchain Node A (College A)
Write-Host "`n[1/4] Starting ChainForge Node A (College A)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$CurrentDir\chainforge_node'; Write-Host 'Installing Node Dependencies...'; pip install -q -r requirements.txt; Write-Host 'Starting Node A on port 8080 / 5000...'; python main.py --api-port 8080 --port 5000 --db-path ../data/node_a.sqlite"

# Wait a moment for the first node to bind before starting the second
Start-Sleep -Seconds 4

# 2. Start Blockchain Node B (College B)
Write-Host "[2/4] Starting ChainForge Node B (College B)..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$CurrentDir\chainforge_node'; Write-Host 'Starting Node B on port 8081 / 5001 peered to Node A...'; python main.py --api-port 8081 --port 5001 --peers 127.0.0.1:8080 --db-path ../data/node_b.sqlite"

# Wait a moment for Node B to connect
Start-Sleep -Seconds 3

# 3. Start Backend API
Write-Host "[3/4] Starting FastAPI Backend Middleware..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$CurrentDir\backend'; Write-Host 'Installing Backend Dependencies...'; pip install -q fastapi uvicorn pydantic pyjwt httpx; Write-Host 'Starting Backend on port 8001...'; uvicorn main:app --reload --port 8001"

# Wait a moment for backend to initialize
Start-Sleep -Seconds 2

# 4. Start Frontend UI
Write-Host "[4/4] Starting React Web Portal..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$CurrentDir\frontend'; Write-Host 'Installing Frontend Dependencies...'; npm install; Write-Host 'Starting Vite Frontend on port 5174...'; npm run dev -- --port 5174"

Write-Host "`n=========================================" -ForegroundColor Green
Write-Host " Success! All 4 services are booting up." -ForegroundColor Green
Write-Host " - ChainForge Node A API:   http://127.0.0.1:8080" -ForegroundColor DarkGray
Write-Host " - ChainForge Node B API:   http://127.0.0.1:8081" -ForegroundColor DarkGray
Write-Host " - Backend Middleware API:  http://127.0.0.1:8001" -ForegroundColor DarkGray
Write-Host " - Frontend Web Portal:     http://localhost:5174" -ForegroundColor White
Write-Host "=========================================" -ForegroundColor Green
Write-Host "`nOpen http://localhost:5174 in your browser to begin the demo!" -ForegroundColor Cyan
