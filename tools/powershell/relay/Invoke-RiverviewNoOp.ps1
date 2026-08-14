# Riverview Registered No-Op Action
# Version: 0.5.0
# Purpose: Acceptance-only action proving bounded runner execution.

[CmdletBinding()]
param([ValidateRange(1,5)][int]$DelaySeconds=2)

CLS
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
Start-Sleep -Seconds $DelaySeconds
[ordered]@{status='succeeded';action='relay.noop';version='0.5.0';delay_seconds=$DelaySeconds}|ConvertTo-Json -Compress