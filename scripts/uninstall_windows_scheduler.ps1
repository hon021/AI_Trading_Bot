$ErrorActionPreference = "Stop"
$taskName = "AI Trading Bot - Local Scheduler"

Unregister-ScheduledTask -TaskName $taskName -Confirm:$false
Write-Output "Task removed: $taskName"
