# Start GapForge + OntoHarness + Embabel MCP (full agent/HITL stack).
$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (-not (Test-Path ".env")) {
    Write-Error "Copy .env.example to .env and set OPENAI_API_KEY first."
}

foreach ($dir in @("..\ontoharness", "..\embabel-mcp")) {
    if (-not (Test-Path $dir)) {
        Write-Error "Missing $dir — clone sibling repos next to gapforge."
    }
}

docker compose -f docker-compose.full.yml up --build @args
