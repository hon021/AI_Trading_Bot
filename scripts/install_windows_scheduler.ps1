# Registers the local market scheduler in Windows Task Scheduler.

$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$pythonPath = Join-Path $projectRoot ".venv\Scripts\python.exe"
$taskName = "AI Trading Bot - Local Scheduler"

if (-not (Test-Path $pythonPath)) {
    throw "Virtual environment Python not found: $pythonPath"
}

$action = New-ScheduledTaskAction `
    -Execute $pythonPath `
    -Argument "-m scripts.local_scheduler" `
    -WorkingDirectory $projectRoot

$trigger = New-ScheduledTaskTrigger `
    -Weekly `
    -DaysOfWeek Monday,Tuesday,Wednesday,Thursday,Friday `
    -At "09:00"

$settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew

$principal = New-ScheduledTaskPrincipal `
    -UserId ([System.Security.Principal.WindowsIdentity]::GetCurrent().Name) `
    -LogonType Interactive `
    -RunLevel Limited

Register-ScheduledTask `
    -TaskName $taskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Principal $principal `
    -Description "Starts the AI Trading Bot local weekday analysis scheduler." `
    -Force | Out-Null

Write-Output "Task registered: $taskName"
Write-Output "Schedule: Monday-Friday at 09:00 local Windows time"
Write-Output "Project: $projectRoot"
Write-Output "Python: $pythonPath"
Write-Output "Use Task Scheduler or the commands below to control it:"
Write-Output "  Start-ScheduledTask -TaskName '$taskName'"
Write-Output "  Stop-ScheduledTask -TaskName '$taskName'"
