# start_services.ps1
$baseDir = "c:\Users\ARTH PATEL\OneDrive\Desktop\ARTH\Sem-6\Blockchain\certificate_verification_system"
$nodeDir = Join-Path $baseDir "chainforge_node"
$backendDir = Join-Path $baseDir "backend"
$frontendDir = Join-Path $baseDir "frontend"
$dataDir = Join-Path $baseDir "data"

# 1. Start Node A
Write-Host "Starting Node A on 8080..."
Start-Process python -ArgumentList "-u", "main.py", "--api-port", "8080", "--port", "5000", "--db-path", "../data/node_a.sqlite" -WorkingDirectory $nodeDir -NoNewWindow -RedirectStandardOutput (Join-Path $dataDir "node_a.log") -RedirectStandardError (Join-Path $dataDir "node_a_err.log")

# 2. Start Node B
Write-Host "Wait 5s for Node A..."
Start-Sleep -s 5
Write-Host "Starting Node B on 8081..."
Start-Process python -ArgumentList "-u", "main.py", "--api-port", "8081", "--port", "5001", "--peers", "127.0.0.1:8080", "--db-path", "../data/node_b.sqlite" -WorkingDirectory $nodeDir -NoNewWindow -RedirectStandardOutput (Join-Path $dataDir "node_b.log") -RedirectStandardError (Join-Path $dataDir "node_b_err.log")

# 3. Start Backend
Write-Host "Wait 5s for Nodes..."
Start-Sleep -s 5
Write-Host "Starting Backend on 8001..."
Start-Process uvicorn -ArgumentList "main:app", "--port", "8001" -WorkingDirectory $backendDir -NoNewWindow -RedirectStandardOutput (Join-Path $dataDir "backend.log") -RedirectStandardError (Join-Path $dataDir "backend_err.log")

# 4. Start Frontend
Write-Host "Starting Frontend on 5174..."
Start-Process npm -ArgumentList "run", "dev", "--", "--port", "5174" -WorkingDirectory $frontendDir -NoNewWindow -RedirectStandardOutput (Join-Path $dataDir "frontend.log") -RedirectStandardError (Join-Path $dataDir "frontend_err.log")

Write-Host "All services started."
