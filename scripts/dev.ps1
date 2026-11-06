# Start the API and the dashboard on loopback. Requires Python 3.11+ and Node 22.
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (-not (Test-Path ".env")) {
  $secret = python -c "import secrets; print(secrets.token_urlsafe(32))"
  $password = python -c "import secrets; print(secrets.token_urlsafe(12))"
  @"
QUBIT_SECRET_KEY=$secret
QUBIT_ADMIN_USERNAME=admin
QUBIT_ADMIN_PASSWORD=$password
QUBIT_HOST=127.0.0.1
QUBIT_PORT=8000
QUBIT_LOG_LEVEL=INFO
"@ | Set-Content -Path ".env" -Encoding ascii
  Write-Host "Wrote .env"
  Write-Host "Administrator username: admin"
  Write-Host "Administrator password: $password"
}

if (-not (Test-Path "backend\.venv\Scripts\python.exe")) {
  python -m venv "backend\.venv"
}
& "backend\.venv\Scripts\python.exe" -m pip install --upgrade pip
& "backend\.venv\Scripts\python.exe" -m pip install -r "backend\requirements.txt"

if (-not (Test-Path "frontend\node_modules")) {
  Push-Location frontend
  npm install
  Pop-Location
}

Get-Content ".env" | ForEach-Object {
  if ($_ -match "^\s*#" -or $_ -notmatch "=") { return }
  $name, $value = $_.Split("=", 2)
  Set-Item -Path "Env:$name" -Value $value
}

Write-Host "API:       http://127.0.0.1:8000/health"
Write-Host "Dashboard: http://127.0.0.1:3000"
$backend = Start-Process -FilePath "backend\.venv\Scripts\python.exe" -ArgumentList "-m","uvicorn","app.main:app","--host","127.0.0.1","--port","8000" -WorkingDirectory "$Root\backend" -PassThru
$frontend = Start-Process -FilePath "npm" -ArgumentList "run","dev" -WorkingDirectory "$Root\frontend" -PassThru
try {
  Wait-Process -Id $backend.Id, $frontend.Id
}
finally {
  if (-not $backend.HasExited) { Stop-Process -Id $backend.Id -Force }
  if (-not $frontend.HasExited) { Stop-Process -Id $frontend.Id -Force }
}
