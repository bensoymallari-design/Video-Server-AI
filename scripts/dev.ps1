# Start the API and the dashboard on loopback.
# Requires Python 3.11+ and Node.js 18+. FFmpeg is required for media inspection.
# Windows PowerShell 5.1 compatible.

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

function Test-WindowsStoreAlias([string]$Path) {
    return $Path -match '\\WindowsApps\\'
}

function Find-RealExecutable([string[]]$Names) {
    foreach ($name in $Names) {
        $cmd = Get-Command $name -ErrorAction SilentlyContinue
        if (-not $cmd) { continue }
        $source = $cmd.Source
        if (Test-WindowsStoreAlias $source) { continue }
        return $source
    }
    return $null
}

function Quote-Literal([string]$Value) {
    return "'" + ($Value -replace "'", "''") + "'"
}

function Invoke-Python([string]$Exe, [string]$Prefix, [string[]]$Arguments) {
    $all = @()
    if ($Prefix) { $all += $Prefix }
    if ($Arguments) { $all += $Arguments }
    $output = & $Exe @all 2>&1
    $text = (($output | ForEach-Object { "$_" }) -join "`n").Trim()
    return @{ Code = $LASTEXITCODE; Text = $text }
}

function Find-Python {
    $attempts = @()

    $py = Find-RealExecutable @("py.exe", "py")
    if ($py) { $attempts += @{ Exe = $py; Prefix = "-3" } }

    foreach ($name in @("python.exe", "python", "python3.exe", "python3")) {
        $exe = Find-RealExecutable @($name)
        if ($exe) { $attempts += @{ Exe = $exe; Prefix = "" } }
    }

    $patterns = @(
        (Join-Path $env:LOCALAPPDATA "Programs\Python\Python3*\python.exe"),
        (Join-Path $env:ProgramFiles "Python3*\python.exe")
    )
    if (${env:ProgramFiles(x86)}) {
        $patterns += (Join-Path ${env:ProgramFiles(x86)} "Python3*\python.exe")
    }
    foreach ($pattern in $patterns) {
        $found = @(Get-Item $pattern -ErrorAction SilentlyContinue | Sort-Object FullName -Descending)
        foreach ($item in $found) {
            $attempts += @{ Exe = $item.FullName; Prefix = "" }
        }
    }

    $seen = @{}
    foreach ($attempt in $attempts) {
        $key = "$($attempt.Exe)|$($attempt.Prefix)"
        if ($seen.ContainsKey($key)) { continue }
        $seen[$key] = $true
        $result = Invoke-Python $attempt.Exe $attempt.Prefix @(
            "-c",
            "import sys; print('%d.%d.%d' % sys.version_info[:3]); raise SystemExit(0 if sys.version_info >= (3, 11) else 2)"
        )
        $versionLine = ""
        foreach ($line in ($result.Text -split "`n")) {
            if ($line.Trim() -match '^\d+\.\d+\.\d+$') { $versionLine = $line.Trim() }
        }
        if ($result.Code -eq 0 -and $versionLine) {
            return @{ Exe = $attempt.Exe; Prefix = [string]$attempt.Prefix; Version = $versionLine }
        }
        if ($result.Code -eq 2) {
            throw "Found $($attempt.Exe) version $($result.Text). Qubit needs Python 3.11 or newer."
        }
    }

    throw @"
Python 3.11 or newer is not installed.

The message 'Python was not found' comes from a Microsoft Store alias, not from Python itself.
Install Python, then open a new terminal so PATH refreshes:

  winget install Python.Python.3.12

Or download the installer from https://www.python.org/downloads/windows/
and enable 'Add python.exe to PATH' plus 'Install launcher for all users'.

If 'python' still opens the Store, turn off the aliases:
Settings > Apps > Advanced app settings > App execution aliases
Disable python.exe and python3.exe.
"@
}

function Find-Node {
    $node = Find-RealExecutable @("node.exe", "node")
    if (-not $node) {
        throw @"
Node.js is not installed. The dashboard needs Node.js 18 or newer.

  winget install OpenJS.NodeJS.LTS

Open a new terminal after the installer finishes.
"@
    }
    $versionText = ((& $node -p "process.versions.node") | Out-String).Trim()
    if ($versionText -notmatch '(\d+)\.\d+\.\d+') {
        throw "Node.js at $node did not report a version."
    }
    $versionText = $Matches[0]
    $major = [int]$Matches[1]
    if ($major -lt 18) {
        throw "Found Node.js $versionText. The dashboard needs Node.js 18 or newer."
    }
    $npm = Find-RealExecutable @("npm.cmd", "npm.exe", "npm")
    if (-not $npm) {
        throw "Node.js was found at $node, but npm was not on PATH."
    }
    return @{ Node = $node; Npm = $npm; Version = $versionText }
}

function Read-DotEnv([string]$Path) {
    $map = @{}
    if (-not (Test-Path $Path)) { return $map }
    foreach ($line in Get-Content -Path $Path) {
        if ($line -match '^\s*#' -or $line -notmatch '=') { continue }
        $parts = $line.Split("=", 2)
        $map[$parts[0].Trim()] = $parts[1]
    }
    return $map
}

$python = Find-Python
$node = Find-Node
Write-Host "Python $($python.Version) at $($python.Exe)"
Write-Host "Node.js $($node.Version)"

$ffmpeg = Find-RealExecutable @("ffmpeg.exe", "ffmpeg")
$ffprobe = Find-RealExecutable @("ffprobe.exe", "ffprobe")
if (-not $ffmpeg -or -not $ffprobe) {
    Write-Warning "FFmpeg was not found on PATH. Display detection can still run. Media upload, thumbnails, and proxies will fail until ffmpeg and ffprobe are installed."
    Write-Warning "Install with: winget install Gyan.FFmpeg"
    Write-Warning "Open a new terminal after installing so PATH includes FFmpeg."
}

$envPath = Join-Path $Root ".env"
$existing = Read-DotEnv $envPath
$password = ""
$secret = ""
if ($existing.ContainsKey("QUBIT_ADMIN_PASSWORD")) { $password = [string]$existing["QUBIT_ADMIN_PASSWORD"] }
if ($existing.ContainsKey("QUBIT_SECRET_KEY")) { $secret = [string]$existing["QUBIT_SECRET_KEY"] }
if (-not (Test-Path $envPath) -or $secret.Length -lt 16 -or $password.Length -lt 8) {
    $secretResult = Invoke-Python $python.Exe $python.Prefix @("-c", "import secrets; print(secrets.token_urlsafe(32))")
    $passwordResult = Invoke-Python $python.Exe $python.Prefix @("-c", "import secrets; print(secrets.token_urlsafe(12))")
    $secret = ($secretResult.Text -split "`n" | Select-Object -Last 1).Trim()
    $password = ($passwordResult.Text -split "`n" | Select-Object -Last 1).Trim()
    if ($passwordResult.Code -ne 0 -or $password.Length -lt 8) {
        throw "Could not generate the administrator password with $($python.Exe)."
    }
    @"
QUBIT_SECRET_KEY=$secret
QUBIT_ADMIN_USERNAME=admin
QUBIT_ADMIN_PASSWORD=$password
QUBIT_HOST=127.0.0.1
QUBIT_PORT=8000
QUBIT_LOG_LEVEL=INFO
"@ | Set-Content -Path $envPath -Encoding ascii
    Write-Host "Wrote $envPath"
    Write-Host "Administrator username: admin"
    Write-Host "Administrator password: $password"
} else {
    Write-Host "Using the existing .env"
}

$venvPython = Join-Path $Root "backend\.venv\Scripts\python.exe"
$venvDir = Join-Path $Root "backend\.venv"
if (-not (Test-Path -LiteralPath $venvPython)) {
    if (Test-Path -LiteralPath $venvDir) {
        Remove-Item -LiteralPath $venvDir -Recurse -Force
    }
    $venvResult = Invoke-Python $python.Exe $python.Prefix @("-m", "venv", $venvDir)
    if ($venvResult.Code -ne 0 -or -not (Test-Path -LiteralPath $venvPython)) {
        if ($venvResult.Text) { Write-Host $venvResult.Text }
        throw "The virtual environment was not created at $venvPython"
    }
}

& $venvPython -m pip install --upgrade pip
if ($LASTEXITCODE -ne 0) { throw "pip could not be upgraded inside the virtual environment." }
& $venvPython -m pip install -r (Join-Path $Root "backend\requirements.txt")
if ($LASTEXITCODE -ne 0) { throw "Python dependencies failed to install." }

$nodeModules = Join-Path $Root "frontend\node_modules"
if (-not (Test-Path -LiteralPath $nodeModules)) {
    Push-Location (Join-Path $Root "frontend")
    try {
        & $node.Npm install
        if ($LASTEXITCODE -ne 0) { throw "npm install failed." }
    } finally {
        Pop-Location
    }
}

foreach ($line in Get-Content -Path $envPath) {
    if ($line -match '^\s*#' -or $line -notmatch '=') { continue }
    $parts = $line.Split("=", 2)
    Set-Item -Path ("Env:" + $parts[0].Trim()) -Value $parts[1]
}

$backendDir = Join-Path $Root "backend"
$frontendDir = Join-Path $Root "frontend"
$apiCommand = "Set-Location -LiteralPath $(Quote-Literal $backendDir); & $(Quote-Literal $venvPython) -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
$webCommand = "Set-Location -LiteralPath $(Quote-Literal $frontendDir); & $(Quote-Literal $node.Npm) run dev"

Write-Host ""
Write-Host "API:       http://127.0.0.1:8000/health"
Write-Host "Dashboard: http://127.0.0.1:3000"
Write-Host "Two windows will stay open. Close both windows to stop the servers."

Start-Process -FilePath "powershell.exe" -WorkingDirectory $backendDir -ArgumentList @(
    "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $apiCommand
)
Start-Process -FilePath "powershell.exe" -WorkingDirectory $frontendDir -ArgumentList @(
    "-NoExit", "-ExecutionPolicy", "Bypass", "-Command", $webCommand
)
