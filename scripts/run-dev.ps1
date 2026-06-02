param(
    [int]$BackendPort = 8010,
    [int]$FrontendPort = 3000,
    [switch]$SkipMigrations
)

$ErrorActionPreference = "Stop"

$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$BackendDir = Join-Path $Root "backend"
$FrontendDir = Join-Path $Root "frontend"
$Python = Join-Path $BackendDir "venv\Scripts\python.exe"
$Npm = (Get-Command npm.cmd).Source

function Ensure-FileFromExample {
    param(
        [string]$Target,
        [string]$Example
    )

    if (-not (Test-Path $Target) -and (Test-Path $Example)) {
        Copy-Item $Example $Target
        Write-Host "Created $Target"
    }
}

function Start-DevProcess {
    param(
        [string]$Name,
        [string]$FileName,
        [string]$Arguments,
        [string]$WorkingDirectory
    )

    $psi = New-Object System.Diagnostics.ProcessStartInfo
    $psi.FileName = $FileName
    $psi.Arguments = $Arguments
    $psi.WorkingDirectory = $WorkingDirectory
    $psi.UseShellExecute = $false
    $psi.RedirectStandardOutput = $true
    $psi.RedirectStandardError = $true
    $psi.CreateNoWindow = $true

    $process = New-Object System.Diagnostics.Process
    $process.StartInfo = $psi
    $process.EnableRaisingEvents = $true

    Register-ObjectEvent -InputObject $process -EventName OutputDataReceived -Action {
        if ($EventArgs.Data) {
            Write-Host "[$($Event.MessageData)] $($EventArgs.Data)"
        }
    } -MessageData $Name | Out-Null

    Register-ObjectEvent -InputObject $process -EventName ErrorDataReceived -Action {
        if ($EventArgs.Data) {
            Write-Host "[$($Event.MessageData)] $($EventArgs.Data)"
        }
    } -MessageData $Name | Out-Null

    [void]$process.Start()
    $process.BeginOutputReadLine()
    $process.BeginErrorReadLine()
    return $process
}

function Assert-PortFree {
    param([int]$Port)

    $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if ($connections) {
        $owners = ($connections | Select-Object -ExpandProperty OwningProcess -Unique) -join ", "
        throw "Port $Port is already in use by process id(s): $owners. Stop them or choose another port."
    }
}

if (-not (Test-Path $Python)) {
    throw "Backend virtualenv not found: $Python"
}

Ensure-FileFromExample `
    -Target (Join-Path $BackendDir ".env") `
    -Example (Join-Path $BackendDir ".env.example")

$frontendEnv = Join-Path $FrontendDir ".env.local"
if (-not (Test-Path $frontendEnv)) {
    Set-Content -Path $frontendEnv -Value "NEXT_PUBLIC_API_BASE_URL=http://localhost:$BackendPort"
    Write-Host "Created $frontendEnv"
}

Assert-PortFree -Port $BackendPort
Assert-PortFree -Port $FrontendPort

if (-not $SkipMigrations) {
    Write-Host "Applying backend migrations..."
    Push-Location $BackendDir
    try {
        & $Python -m alembic upgrade head
    }
    finally {
        Pop-Location
    }
}

Write-Host "Starting backend on http://localhost:$BackendPort"
$backend = Start-DevProcess `
    -Name "backend" `
    -FileName $Python `
    -Arguments "-m uvicorn app.main:app --host 127.0.0.1 --port $BackendPort --reload" `
    -WorkingDirectory $BackendDir

Write-Host "Starting frontend on http://localhost:$FrontendPort"
$frontend = Start-DevProcess `
    -Name "frontend" `
    -FileName $Npm `
    -Arguments "run dev -- --hostname 127.0.0.1 --port $FrontendPort" `
    -WorkingDirectory $FrontendDir

Write-Host ""
Write-Host "Backend health: http://localhost:$BackendPort/api/health"
Write-Host "Frontend:       http://localhost:$FrontendPort"
Write-Host "Press Ctrl+C to stop both services."

try {
    while (-not $backend.HasExited -and -not $frontend.HasExited) {
        Start-Sleep -Seconds 1
    }

    if ($backend.HasExited) {
        throw "Backend process exited with code $($backend.ExitCode)."
    }
    if ($frontend.HasExited) {
        throw "Frontend process exited with code $($frontend.ExitCode)."
    }
}
finally {
    foreach ($process in @($backend, $frontend)) {
        if ($process -and -not $process.HasExited) {
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        }
    }
}
