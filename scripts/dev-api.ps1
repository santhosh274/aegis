# Starts the AEGIS FastAPI backend detached from the calling process so it is
# NOT killed when the launching shell/session (or a dev tool's job object) exits.
#
# Usage:
#   powershell -ExecutionPolicy Bypass -File scripts\dev-api.ps1
#
# If port 8000 is already listening, it exits without doing anything.

$Root = Join-Path $PSScriptRoot ".."
$LogDir = Join-Path $Root "logs"
$LogFile = Join-Path $LogDir "api.log"
$Port = 8000
$HostAddr = "127.0.0.1"
$Py = "python"

if (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue) {
    ${apiPid} = (Get-NetTCPConnection -LocalPort $Port -State Listen).OwningProcess
    Write-Host "AEGIS API already running on ${HostAddr}:${Port} (pid ${apiPid})."
    exit 0
}

New-Item -ItemType Directory -Path $LogDir -Force | Out-Null

# Spawn via WMI so the process is owned by the WMI provider, not this shell's
# job object. Output is redirected to logs\api.log.
$CommandLine = "cmd /c ""$Py -m uvicorn api.main:app --host ${HostAddr} --port ${Port} > ""$LogFile"" 2>&1"""
$Created = Invoke-CimMethod -ClassName Win32_Process -MethodName Create -Arguments @{
    CommandLine      = $CommandLine
    CurrentDirectory = $Root
}
if ($Created.ReturnValue -ne 0) {
    Write-Host "Failed to start AEGIS API (Win32_Process.Create returned $($Created.ReturnValue))."
    exit 1
}
Write-Host "AEGIS API launching detached (pid $($Created.ProcessId), log: $LogFile)."

# Poll /health until the API is up.
for ($i = 0; $i -lt 30; $i++) {
    try {
        $health = Invoke-RestMethod "http://${HostAddr}:${Port}/health" -TimeoutSec 5 -ErrorAction Stop
    } catch {
        $health = $null
    }
    if ($health -and $health.ok) {
        ${apiPid} = (Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue).OwningProcess
        Write-Host "AEGIS API is healthy on ${HostAddr}:${Port} (pid ${apiPid})."
        exit 0
    }
    Start-Sleep -Milliseconds 700
}

Write-Host "AEGIS API did not become healthy in time - check $LogFile."
exit 1
