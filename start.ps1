#!/usr/bin/env pwsh
# Launch backend (port 8000) and frontend (port 5173) in separate PowerShell windows.
# Run from the repo root:  .\start.ps1

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

# Backend
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$root\backend'; uvicorn app.main:app --reload --host 127.0.0.1 --port 8000"
)

# Frontend
Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-Command",
    "Set-Location '$root\frontend'; npm run dev"
)

Write-Host ""
Write-Host "Backend:  http://127.0.0.1:8000" -ForegroundColor Green
Write-Host "Frontend: http://localhost:5173"  -ForegroundColor Green
Write-Host ""
Write-Host "Close the two spawned PowerShell windows to stop the servers."
