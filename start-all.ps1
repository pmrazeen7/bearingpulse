param(
    [switch]$Detach
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $projectRoot

function Write-Step {
    param([string]$Message)
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Test-DockerCompose {
    try {
        docker compose version | Out-Null
        return $true
    }
    catch {
        return $false
    }
}

function Invoke-Compose {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Args
    )

    if (Test-DockerCompose) {
        & docker compose @Args
    }
    else {
        & docker-compose @Args
    }
}

function Wait-ForApp {
    param(
        [string]$Url,
        [int]$MaxAttempts = 60
    )

    for ($attempt = 1; $attempt -le $MaxAttempts; $attempt++) {
        try {
            Invoke-WebRequest -Uri $Url -Method Get -UseBasicParsing -TimeoutSec 5 | Out-Null
            return
        }
        catch {
            Start-Sleep -Seconds 3
        }
    }

    throw "App did not become ready in time: $Url"
}

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example." -ForegroundColor Yellow
    Write-Host "Edit .env and replace every 'replace-with-...' value (API_KEY, POSTGRES_PASSWORD, DATABASE_URL, FLOWER_BASIC_AUTH), then run this script again." -ForegroundColor Yellow
    exit 1
}
if (Select-String -Path ".env" -Pattern "replace-with" -Quiet) {
    Write-Host ".env still contains 'replace-with-...' placeholders. Set real secrets first." -ForegroundColor Red
    exit 1
}

Write-Step "Starting Docker services"
$composeArgs = @("up", "--build")
if ($Detach) {
    $composeArgs += "-d"
}
Invoke-Compose @composeArgs

if (-not $Detach) {
    Write-Host ""
    Write-Host "Services are running in the foreground." -ForegroundColor Yellow
    Write-Host "Open a new PowerShell window and run:" -ForegroundColor Yellow
    Write-Host "  .\start-all.ps1 -Detach" -ForegroundColor White
    exit 0
}

Write-Step "Waiting for API container to become ready"
Wait-ForApp -Url "http://localhost:8000/api/health"
# Migrations run automatically when the app container starts.

Write-Step "Project is ready"
Write-Host "Frontend : http://localhost:3000" -ForegroundColor Green
Write-Host "API      : http://localhost:8000/api/health" -ForegroundColor Green
Write-Host "Flower   : http://localhost:5555" -ForegroundColor Green
