# Riverview Read-Only MCP Relay Schema Contract Sweep Repair
# Version: 0.9.14
# Purpose: Repair diagnostic evidence projection and sweep all bounded MCP reads before full RV-004.4 acceptance.
# Updated: 2026-08-14

[CmdletBinding()]
param([string]$RepositoryPath='A:\Riverview\standalone')

CLS
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest

$ToolVersion='0.9.14'
$ExpectedHead='c496b01f86ccdf21b3b1a0914c5e48d9bf300043'
$CheckpointId='RIV-MCP-0007'
$ReportLines=[Collections.Generic.List[string]]::new()

function Add-Line {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Text,[ConsoleColor]$Color='Gray')
    $ReportLines.Add($Text)
    Write-Host $Text -ForegroundColor $Color
}
function Add-Section {
    param([Parameter(Mandatory)][string]$Title)
    Add-Line ''
    Add-Line "=== $Title ===" Cyan
}
function Write-Utf8NoBom {
    param([Parameter(Mandatory)][string]$Path,[Parameter(Mandatory)][AllowEmptyString()][string]$Content)
    $Encoding=New-Object System.Text.UTF8Encoding($false)
    [System.IO.File]::WriteAllText($Path,$Content,$Encoding)
}
function Save-Report {
    $Directory=Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\mcp-relay'
    New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    $Path=Join-Path $Directory "ReadOnly-MCP-Relay-Schema-Sweep-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
    $Report=($ReportLines -join [Environment]::NewLine)+[Environment]::NewLine
    Write-Utf8NoBom -Path $Path -Content $Report
    try {
        if(Get-Command Set-Clipboard -ErrorAction SilentlyContinue){ Set-Clipboard $Report }
        else { $Report | clip.exe }
        Write-Host "`nComplete report copied to the Windows clipboard." -ForegroundColor Cyan
    } catch {
        Write-Host "`nClipboard copy failed: $($_.Exception.Message)" -ForegroundColor Yellow
    }
    Write-Host "Durable report: $Path" -ForegroundColor Green
}
function Invoke-Captured {
    param(
        [Parameter(Mandatory)][string]$FilePath,
        [Parameter(Mandatory)][string[]]$ArgumentList,
        [Parameter(Mandatory)][string]$Label
    )
    $Capture=Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\mcp-relay\completion-capture'
    New-Item -ItemType Directory -Path $Capture -Force | Out-Null
    $Stamp=Get-Date -Format 'yyyyMMdd-HHmmssfff'
    $Out=Join-Path $Capture "$Label-$Stamp.stdout.txt"
    $Err=Join-Path $Capture "$Label-$Stamp.stderr.txt"
    $Process=Start-Process -FilePath $FilePath -ArgumentList $ArgumentList -WorkingDirectory $RepositoryPath -RedirectStandardOutput $Out -RedirectStandardError $Err -Wait -PassThru
    if(Test-Path $Out){ foreach($Line in @(Get-Content $Out -Encoding UTF8)){ Add-Line $Line } }
    if(Test-Path $Err){ foreach($Line in @(Get-Content $Err -Encoding UTF8)){ Add-Line $Line $(if($Process.ExitCode -eq 0){'Yellow'}else{'Red'}) } }
    if($Process.ExitCode -ne 0){ throw "${CheckpointId}: $Label failed with exit code $($Process.ExitCode)." }
}

try {
    Add-Section 'RIVERVIEW READ-ONLY MCP RELAY SCHEMA CONTRACT SWEEP'

    $RepositoryPath=(Resolve-Path $RepositoryPath).Path
    $Head=(git.exe -C $RepositoryPath rev-parse HEAD).Trim()
    $Branch=(git.exe -C $RepositoryPath branch --show-current).Trim()
    $Python=Join-Path $RepositoryPath '.venv\Scripts\python.exe'

    Add-Line "Repository: $RepositoryPath" Green
    Add-Line "Branch: $Branch"
    Add-Line "Local HEAD: $Head"
    Add-Line "Repair version: $ToolVersion"

    Add-Section 'CHARTER AND RV-004.4 SCOPE ANCHOR'
    Add-Line 'Mission: preserve and extend the Estate while making Riverview explicit, diagnosable, resumable, and simpler.'
    Add-Line 'Current dependency-ready waypoint: RV-004.4 - Read-only MCP Relay.'
    Add-Line 'Exact action: repair diagnostic evidence projection, sweep all safely invokable bounded reads, then execute full local acceptance.'
    Add-Line 'No enqueue, arbitrary SQL surface, filesystem/process authority in MCP, secrets, credentials, Undercurrent access, remote exposure, unified supervisor, commit, or push.'

    if($Branch -ne 'main'){ throw "${CheckpointId}: Expected branch main, observed $Branch." }
    if($Head -ne $ExpectedHead){ throw "${CheckpointId}: Expected HEAD $ExpectedHead, observed $Head." }
    if(-not(Test-Path $Python)){ throw 'RIV-BLD-0006: Riverview virtual environment not found.' }

    Add-Section 'SELF-INSTALLATION'
    $Canonical=Join-Path $RepositoryPath 'tools\powershell\mcp\Repair-RiverviewReadOnlyMCPRelay.ps1'
    if([System.IO.Path]::GetFullPath($PSCommandPath) -ne [System.IO.Path]::GetFullPath($Canonical)){
        Copy-Item $PSCommandPath $Canonical -Force
        Add-Line "Installed repair tool: $Canonical" Green
    }

    Add-Section 'PRE-REPAIR WORKING TREE'
    foreach($Line in @(git.exe -C $RepositoryPath status --porcelain=v1 --untracked-files=all)){ Add-Line $Line Yellow }
    if(@(git.exe -C $RepositoryPath diff --cached --name-only).Count -ne 0){ throw "${CheckpointId}: staged files exist." }

    $Runtime=Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\mcp-relay\completion-runtime'
    New-Item -ItemType Directory -Path $Runtime -Force | Out-Null

    Add-Section 'DIAGNOSTIC PROJECTION REPAIR'
    $Patch=Join-Path $Runtime 'patch_diagnostics_0914.py'
    $PatchText=[System.Text.Encoding]::UTF8.GetString([Convert]::FromBase64String('CmZyb20gX19mdXR1cmVfXyBpbXBvcnQgYW5ub3RhdGlvbnMKCmltcG9ydCBhc3QKZnJvbSBwYXRobGliIGltcG9ydCBQYXRoCgpST09UID0gUGF0aChyIl9fUk9PVF9fIikKCmRlZiB3cml0ZShwYXRoOiBQYXRoLCB0ZXh0OiBzdHIpIC0+IE5vbmU6CiAgICBwYXRoLndyaXRlX3RleHQodGV4dCwgZW5jb2Rpbmc9InV0Zi04IiwgbmV3bGluZT0iXG4iKQogICAgcHJpbnQoZiJVUERBVEVEICAge3BhdGgucmVsYXRpdmVfdG8oUk9PVCl9IikKCmRlZiBwYXRjaF9yZWFkX21vZGVsKHBhdGg6IFBhdGgpIC0+IE5vbmU6CiAgICB0ZXh0ID0gcGF0aC5yZWFkX3RleHQoZW5jb2Rpbmc9InV0Zi04IikKICAgIHRyZWUgPSBhc3QucGFyc2UodGV4dCkKICAgIHRhcmdldCA9IE5vbmUKICAgIGZvciBub2RlIGluIGFzdC53YWxrKHRyZWUpOgogICAgICAgIGlmIG5vdCBpc2luc3RhbmNlKG5vZGUsIGFzdC5DYWxsKToKICAgICAgICAgICAgY29udGludWUKICAgICAgICBpZiBub3QgaXNpbnN0YW5jZShub2RlLmZ1bmMsIGFzdC5BdHRyaWJ1dGUpIG9yIG5vZGUuZnVuYy5hdHRyICE9ICJleGVjdXRlIjoKICAgICAgICAgICAgY29udGludWUKICAgICAgICBpZiBub3Qgbm9kZS5hcmdzOgogICAgICAgICAgICBjb250aW51ZQogICAgICAgIGZpcnN0ID0gbm9kZS5hcmdzWzBdCiAgICAgICAgaWYgaXNpbnN0YW5jZShmaXJzdCwgYXN0LkNvbnN0YW50KSBhbmQgaXNpbnN0YW5jZShmaXJzdC52YWx1ZSwgc3RyKToKICAgICAgICAgICAgaWYgIkZST00gZGlhZ25vc3RpY19ldmVudHMiIGluIGZpcnN0LnZhbHVlOgogICAgICAgICAgICAgICAgdGFyZ2V0ID0gbm9kZQogICAgICAgICAgICAgICAgYnJlYWsKICAgIGlmIHRhcmdldCBpcyBOb25lOgogICAgICAgIHJhaXNlIFJ1bnRpbWVFcnJvcigiUklWLU1DUC0wMDA3OiBkaWFnbm9zdGljX2V2ZW50cyByZWFkIHF1ZXJ5IG5vdCBmb3VuZC4iKQoKICAgIHNxbCA9IHRhcmdldC5hcmdzWzBdLnZhbHVlCiAgICBpZiAiZXZpZGVuY2VfcmVmcyBBUyBldmlkZW5jZSIgaW4gc3FsOgogICAgICAgIHByaW50KCJkaWFnbm9zdGljcyBxdWVyeSBhbHJlYWR5IHJlcGFpcmVkIikKICAgICAgICByZXR1cm4KICAgIGlmICJldmlkZW5jZSIgbm90IGluIHNxbDoKICAgICAgICByYWlzZSBSdW50aW1lRXJyb3IoIlJJVi1NQ1AtMDAwNzogZGlhZ25vc3RpY19ldmVudHMgcXVlcnkgaGFzIHVuZXhwZWN0ZWQgZXZpZGVuY2UgcHJvamVjdGlvbi4iKQoKICAgIHJlcGFpcmVkX3NxbCA9IHNxbC5yZXBsYWNlKCJzdW1tYXJ5LGV2aWRlbmNlLCIsICJzdW1tYXJ5LGV2aWRlbmNlX3JlZnMgQVMgZXZpZGVuY2UsIikKICAgIGlmIHJlcGFpcmVkX3NxbCA9PSBzcWw6CiAgICAgICAgcmVwYWlyZWRfc3FsID0gc3FsLnJlcGxhY2UoInN1bW1hcnksIGV2aWRlbmNlLCIsICJzdW1tYXJ5LCBldmlkZW5jZV9yZWZzIEFTIGV2aWRlbmNlLCIpCiAgICBpZiByZXBhaXJlZF9zcWwgPT0gc3FsOgogICAgICAgIHJhaXNlIFJ1bnRpbWVFcnJvcigiUklWLU1DUC0wMDA3OiBjb3VsZCBub3QgcmVwYWlyIGRpYWdub3N0aWMgZXZpZGVuY2UgcHJvamVjdGlvbiBzYWZlbHkuIikKCiAgICBsaW5lcyA9IHRleHQuc3BsaXRsaW5lcyhrZWVwZW5kcz1UcnVlKQogICAgc3RhcnQgPSB0YXJnZXQubGluZW5vIC0gMQogICAgZW5kID0gdGFyZ2V0LmVuZF9saW5lbm8KICAgIGluZGVudCA9IGxpbmVzW3N0YXJ0XVs6IGxlbihsaW5lc1tzdGFydF0pIC0gbGVuKGxpbmVzW3N0YXJ0XS5sc3RyaXAoKSldCgogICAgY2FsbCA9ICgKICAgICAgICBmJ3tpbmRlbnR9Y3Vyc29yLmV4ZWN1dGUoXG4nCiAgICAgICAgZid7aW5kZW50fSAgICB7cmVwYWlyZWRfc3FsIXJ9LFxuJwogICAgICAgIGYne2luZGVudH0gICAgKGxpbWl0LCksXG4nCiAgICAgICAgZid7aW5kZW50fSlcbicKICAgICkKICAgIG5ld190ZXh0ID0gIiIuam9pbihsaW5lc1s6c3RhcnRdKSArIGNhbGwgKyAiIi5qb2luKGxpbmVzW2VuZDpdKQogICAgbmV3X3RleHQgPSBuZXdfdGV4dC5yZXBsYWNlKCJWZXJzaW9uOiAwLjkuMTAiLCAiVmVyc2lvbjogMC45LjE0IikKICAgIHdyaXRlKHBhdGgsIG5ld190ZXh0KQoKZGVmIHBhdGNoX2luc3RhbGxlcihwYXRoOiBQYXRoKSAtPiBOb25lOgogICAgdGV4dCA9IHBhdGgucmVhZF90ZXh0KGVuY29kaW5nPSJ1dGYtOCIpCiAgICBiZWZvcmUgPSB0ZXh0CiAgICB0ZXh0ID0gdGV4dC5yZXBsYWNlKCJzdW1tYXJ5LGV2aWRlbmNlLHJlY292ZXJ5X3N0YXRlIiwgInN1bW1hcnksZXZpZGVuY2VfcmVmcyBBUyBldmlkZW5jZSxyZWNvdmVyeV9zdGF0ZSIpCiAgICB0ZXh0ID0gdGV4dC5yZXBsYWNlKCJzdW1tYXJ5LCBldmlkZW5jZSwgcmVjb3Zlcnlfc3RhdGUiLCAic3VtbWFyeSwgZXZpZGVuY2VfcmVmcyBBUyBldmlkZW5jZSwgcmVjb3Zlcnlfc3RhdGUiKQogICAgdGV4dCA9IHRleHQucmVwbGFjZSgiIyBWZXJzaW9uOiAwLjkuMTAiLCAiIyBWZXJzaW9uOiAwLjkuMTQiLCAxKQogICAgdGV4dCA9IHRleHQucmVwbGFjZSgiJFRvb2xWZXJzaW9uPScwLjkuMTAnIiwgIiRUb29sVmVyc2lvbj0nMC45LjE0JyIsIDEpCiAgICBpZiB0ZXh0ID09IGJlZm9yZToKICAgICAgICBpZiAiZXZpZGVuY2VfcmVmcyBBUyBldmlkZW5jZSIgaW4gdGV4dDoKICAgICAgICAgICAgcHJpbnQoImluc3RhbGxlciBkaWFnbm9zdGljcyBxdWVyeSBhbHJlYWR5IHJlcGFpcmVkIikKICAgICAgICAgICAgcmV0dXJuCiAgICAgICAgcmFpc2UgUnVudGltZUVycm9yKCJSSVYtTUNQLTAwMDc6IGNhbm9uaWNhbCBpbnN0YWxsZXIgZGlhZ25vc3RpYyBwcm9qZWN0aW9uIHNlYW0gbm90IGZvdW5kLiIpCiAgICB3cml0ZShwYXRoLCB0ZXh0KQoKcGF0Y2hfcmVhZF9tb2RlbChST09UIC8gInNyYy9yaXZlcnZpZXcvbWNwL3JlYWRfbW9kZWwucHkiKQpwYXRjaF9pbnN0YWxsZXIoUk9PVCAvICJ0b29scy9wb3dlcnNoZWxsL21jcC9JbnN0YWxsLVJpdmVydmlld1JlYWRPbmx5TUNQUmVsYXkucHMxIikK')).Replace('__ROOT__',$RepositoryPath.Replace('\','\\'))
    Write-Utf8NoBom -Path $Patch -Content $PatchText
    Invoke-Captured -FilePath $Python -ArgumentList @($Patch) -Label 'patch_diagnostics'

    Add-Section 'FULL STATIC ACCEPTANCE'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','compileall','-q','src\riverview\mcp','src\riverview\mcp_health.py') -Label 'python_compile'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','ruff','check','src\riverview\mcp','src\riverview\mcp_health.py','tests\test_mcp_readonly.py','tests\test_mcp_transport.py') -Label 'ruff_full'
    Add-Line 'Full static acceptance passed.' Green

    Add-Section 'BOUNDED READ-SURFACE SWEEP'
    $Sweep=Join-Path $Runtime 'read_surface_sweep_0914.py'
    [System.IO.File]::WriteAllBytes($Sweep,[Convert]::FromBase64String('CmZyb20gX19mdXR1cmVfXyBpbXBvcnQgYW5ub3RhdGlvbnMKCmltcG9ydCBpbnNwZWN0CmltcG9ydCBqc29uCgpmcm9tIHJpdmVydmlldy5tY3AucmVhZF9tb2RlbCBpbXBvcnQgUmVhZE9ubHlSZWxheQoKcmVsYXkgPSBSZWFkT25seVJlbGF5KCkKcmVzdWx0cyA9IHt9Cgpmb3IgbmFtZSBpbiBzb3J0ZWQoZGlyKHJlbGF5KSk6CiAgICBpZiBuYW1lLnN0YXJ0c3dpdGgoIl8iKToKICAgICAgICBjb250aW51ZQogICAgbWVtYmVyID0gZ2V0YXR0cihyZWxheSwgbmFtZSkKICAgIGlmIG5vdCBjYWxsYWJsZShtZW1iZXIpOgogICAgICAgIGNvbnRpbnVlCgogICAgc2lnID0gaW5zcGVjdC5zaWduYXR1cmUobWVtYmVyKQogICAgcGFyYW1zID0gbGlzdChzaWcucGFyYW1ldGVycy52YWx1ZXMoKSkKCiAgICB0cnk6CiAgICAgICAgaWYgbm90IHBhcmFtczoKICAgICAgICAgICAgdmFsdWUgPSBtZW1iZXIoKQogICAgICAgIGVsaWYgbGVuKHBhcmFtcykgPT0gMSBhbmQgcGFyYW1zWzBdLm5hbWUgPT0gImxpbWl0IjoKICAgICAgICAgICAgdmFsdWUgPSBtZW1iZXIoMSkKICAgICAgICBlbGlmIGFsbCgKICAgICAgICAgICAgcC5kZWZhdWx0IGlzIG5vdCBpbnNwZWN0LlBhcmFtZXRlci5lbXB0eQogICAgICAgICAgICBvciBwLmtpbmQgaW4gKGluc3BlY3QuUGFyYW1ldGVyLlZBUl9QT1NJVElPTkFMLCBpbnNwZWN0LlBhcmFtZXRlci5WQVJfS0VZV09SRCkKICAgICAgICAgICAgZm9yIHAgaW4gcGFyYW1zCiAgICAgICAgKToKICAgICAgICAgICAgdmFsdWUgPSBtZW1iZXIoKQogICAgICAgIGVsc2U6CiAgICAgICAgICAgIHJlc3VsdHNbbmFtZV0gPSB7InN0YXR1cyI6ICJza2lwcGVkIiwgInNpZ25hdHVyZSI6IHN0cihzaWcpfQogICAgICAgICAgICBjb250aW51ZQoKICAgICAgICBpZiBpc2luc3RhbmNlKHZhbHVlLCBsaXN0KToKICAgICAgICAgICAgc3VtbWFyeSA9IHsidHlwZSI6ICJsaXN0IiwgImNvdW50IjogbGVuKHZhbHVlKX0KICAgICAgICBlbGlmIGlzaW5zdGFuY2UodmFsdWUsIGRpY3QpOgogICAgICAgICAgICBzdW1tYXJ5ID0geyJ0eXBlIjogImRpY3QiLCAia2V5cyI6IHNvcnRlZCh2YWx1ZS5rZXlzKCkpWzoyMF19CiAgICAgICAgZWxzZToKICAgICAgICAgICAgc3VtbWFyeSA9IHsidHlwZSI6IHR5cGUodmFsdWUpLl9fbmFtZV9ffQogICAgICAgIHJlc3VsdHNbbmFtZV0gPSB7InN0YXR1cyI6ICJoZWFsdGh5IiwgInNpZ25hdHVyZSI6IHN0cihzaWcpLCAicmVzdWx0Ijogc3VtbWFyeX0KICAgIGV4Y2VwdCBFeGNlcHRpb24gYXMgZXhjOgogICAgICAgIHJlc3VsdHNbbmFtZV0gPSB7CiAgICAgICAgICAgICJzdGF0dXMiOiAiZmFpbGVkIiwKICAgICAgICAgICAgInNpZ25hdHVyZSI6IHN0cihzaWcpLAogICAgICAgICAgICAiZXJyb3JfdHlwZSI6IHR5cGUoZXhjKS5fX25hbWVfXywKICAgICAgICAgICAgImVycm9yIjogc3RyKGV4YyksCiAgICAgICAgfQoKcHJpbnQoanNvbi5kdW1wcyhyZXN1bHRzLCBpbmRlbnQ9Miwgc29ydF9rZXlzPVRydWUsIGRlZmF1bHQ9c3RyKSkKCmZhaWxlZCA9IFtuYW1lIGZvciBuYW1lLCBpdGVtIGluIHJlc3VsdHMuaXRlbXMoKSBpZiBpdGVtWyJzdGF0dXMiXSA9PSAiZmFpbGVkIl0KaWYgZmFpbGVkOgogICAgcmFpc2UgUnVudGltZUVycm9yKGYiUklWLU1DUC0wMDA3OiBib3VuZGVkIHJlYWQtc3VyZmFjZSBzd2VlcCBmYWlsdXJlczoge2ZhaWxlZH0iKQo='))
    Invoke-Captured -FilePath $Python -ArgumentList @($Sweep) -Label 'read_surface_sweep'
    Add-Line 'Bounded read-surface sweep passed.' Green

    Add-Section 'COOKBOOK SYNCHRONIZATION'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','riverview.mcp.cookbook_sync') -Label 'cookbook_sync'
    Add-Line 'Cookbook synchronization passed.' Green

    Add-Section 'MCP HEALTH'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','riverview.mcp_health') -Label 'mcp_health'
    Add-Line 'MCP health passed.' Green

    Add-Section 'MCP CONTRACT TESTS'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','pytest','-q','tests\test_mcp_readonly.py','tests\test_mcp_transport.py') -Label 'mcp_tests'
    Add-Line 'MCP contract tests passed.' Green

    Add-Section 'LIVE STDIO MCP ACCEPTANCE'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','riverview.mcp.live_acceptance') -Label 'live_stdio_acceptance'
    Add-Line 'Live stdio MCP protocol acceptance passed.' Green

    Add-Section 'POST-ACCEPTANCE DATABASE VERIFICATION'
    $Verify=Join-Path $Runtime 'database_verify_0914.py'
    [System.IO.File]::WriteAllBytes($Verify,[Convert]::FromBase64String('CmZyb20gcml2ZXJ2aWV3LmRhdGFiYXNlIGltcG9ydCBjb25uZWN0Cgp3aXRoIGNvbm5lY3QoKSBhcyBjb25uZWN0aW9uLCBjb25uZWN0aW9uLmN1cnNvcigpIGFzIGN1cnNvcjoKICAgIGN1cnNvci5leGVjdXRlKAogICAgICAgICJTRUxFQ1QgY2hlY2twb2ludF9pZCxjb21wb25lbnQsdmFsaWRhdGlvbl9zdGF0ZSxhcHBsaWNhYmlsaXR5ICIKICAgICAgICAiRlJPTSBjb29rYm9va19lbnRyaWVzIFdIRVJFIGNoZWNrcG9pbnRfaWQgTElLRSAnUklWLU1DUC0lJyBPUkRFUiBCWSBjaGVja3BvaW50X2lkIgogICAgKQogICAgcm93cyA9IGN1cnNvci5mZXRjaGFsbCgpCiAgICBpZiBsZW4ocm93cykgPCA2OgogICAgICAgIHJhaXNlIFJ1bnRpbWVFcnJvcihmIlJJVi1NQ1AtMDAwNDogZXhwZWN0ZWQgPj02IFJWLU1DUCBlbnRyaWVzLCBvYnNlcnZlZCB7bGVuKHJvd3MpfSIpCiAgICBmb3IgY2hlY2twb2ludF9pZCwgY29tcG9uZW50LCBzdGF0ZSwgYXBwbGljYWJpbGl0eSBpbiByb3dzOgogICAgICAgIGlmIGNvbXBvbmVudCAhPSAicml2ZXJ2aWV3Lm1jcC5yZWFkb25seSI6CiAgICAgICAgICAgIHJhaXNlIFJ1bnRpbWVFcnJvcihmIntjaGVja3BvaW50X2lkfTogd3JvbmcgY29tcG9uZW50IHtjb21wb25lbnQhcn0iKQogICAgICAgIGlmIHN0YXRlICE9ICJ2YWxpZGF0ZWQiOgogICAgICAgICAgICByYWlzZSBSdW50aW1lRXJyb3IoZiJ7Y2hlY2twb2ludF9pZH06IHZhbGlkYXRpb24gc3RhdGUge3N0YXRlIXJ9IikKICAgICAgICBpZiBhcHBsaWNhYmlsaXR5LmdldCgiYXV0aG9yaXR5IikgIT0gInJlYWRfb25seSI6CiAgICAgICAgICAgIHJhaXNlIFJ1bnRpbWVFcnJvcihmIntjaGVja3BvaW50X2lkfTogYXV0aG9yaXR5IGlzIG5vdCByZWFkX29ubHkiKQogICAgY3Vyc29yLmV4ZWN1dGUoIlNFTEVDVCBDT1VOVCgqKSBGUk9NIGNvb2tib29rX2VudHJpZXMgV0hFUkUgY2hlY2twb2ludF9pZCBMSUtFICdSSVYtRElBLSUnIikKICAgIGRpYSA9IGN1cnNvci5mZXRjaG9uZSgpWzBdCiAgICBpZiBkaWEgPCAyOgogICAgICAgIHJhaXNlIFJ1bnRpbWVFcnJvcigiUklWLU1DUC0wMDA0OiBwcmUtZXhpc3RpbmcgZGlhZ25vc3RpYyBDb29rYm9vayByb3dzIHdlcmUgbm90IHByZXNlcnZlZCIpCiAgICBwcmludChmImRiX3ZlcmlmeT1oZWFsdGh5IHJ2X21jcF9lbnRyaWVzPXtsZW4ocm93cyl9IHByZWV4aXN0aW5nX2RpYWdub3N0aWNfZW50cmllcz17ZGlhfSBhdXRob3JpdHk9cmVhZF9vbmx5IikKICAgIGNvbm5lY3Rpb24ucm9sbGJhY2soKQo='))
    Invoke-Captured -FilePath $Python -ArgumentList @($Verify) -Label 'database_verification'
    Add-Line 'Authoritative PostgreSQL verification passed.' Green

    Add-Section 'FINAL WORKING TREE'
    foreach($Line in @(git.exe -C $RepositoryPath status --porcelain=v1 --untracked-files=all)){ Add-Line $Line Yellow }

    Add-Section 'RV-004.4 LOCAL COMPLETION RESULT'
    Add-Line 'Diagnostic projection now matches authoritative diagnostic_events.evidence_refs.' Green
    Add-Line 'All safely invokable bounded read surfaces passed the schema-contract sweep.' Green
    Add-Line 'Cookbook sync, MCP health, tests, live stdio acceptance, and PostgreSQL verification passed.' Green
    Add-Line 'No prohibited authority was added. No commit or push was performed.' Green
    Add-Line 'RV-004.4 is locally acceptance-complete. Next stage: exact-scope publication.' Green

    Save-Report
}
catch {
    Add-Section 'RV-004.4 SCHEMA CONTRACT SWEEP BLOCKED'
    $Message=$_.Exception.Message
    if([string]::IsNullOrWhiteSpace($Message)){ $Message=$_.ToString() }
    Add-Line $Message Red
    Add-Line 'The same report contains any additional read-surface failure discovered by the sweep.' Yellow
    Add-Line 'No commit or push was performed.' Yellow
    Save-Report
    throw
}
