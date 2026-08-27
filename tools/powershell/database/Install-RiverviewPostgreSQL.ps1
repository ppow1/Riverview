# Riverview Native PostgreSQL Installer
# Version: 0.1.0
# Purpose: Discover or install PostgreSQL 18 natively on Windows and verify its service boundary.
# Updated: 2026-08-14

[CmdletBinding()]
param(
    [Parameter()]
    [ValidateNotNullOrEmpty()]
    [string]$RepositoryPath = 'A:\Riverview\standalone',

    [Parameter()]
    [ValidateRange(1, 65535)]
    [int]$Port = 5432,

    [Parameter()]
    [ValidateRange(14, 18)]
    [int]$MajorVersion = 18
)

CLS
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$ToolVersion = [version]'0.1.0'
$PackageId = "PostgreSQL.PostgreSQL.$MajorVersion"
$CanonicalToolName = 'Install-RiverviewPostgreSQL.ps1'
$CanonicalToolDirectory = 'tools\powershell\database'
$ReportLines = [System.Collections.Generic.List[string]]::new()

function Add-ReportLine {
    param(
        [Parameter(Mandatory)][AllowEmptyString()][string]$Text,
        [ConsoleColor]$Color = [ConsoleColor]::Gray
    )
    $ReportLines.Add($Text)
    Write-Host $Text -ForegroundColor $Color
}

function Add-Section {
    param([Parameter(Mandatory)][string]$Title)
    Add-ReportLine -Text ''
    Add-ReportLine -Text "=== $Title ===" -Color Cyan
}

function Test-Administrator {
    $Identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $Principal = [Security.Principal.WindowsPrincipal]::new($Identity)
    return $Principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-HeaderVersion {
    param([Parameter(Mandatory)][string]$Path)
    $Line = Get-Content -LiteralPath $Path -TotalCount 12 |
        Where-Object { $_ -match '^#\s*Version:\s*(?<Version>\d+\.\d+\.\d+)' } |
        Select-Object -First 1
    if (-not $Line) { throw "No version header found in: $Path" }
    return [version]([regex]::Match($Line, 'Version:\s*(?<Version>\d+\.\d+\.\d+)').Groups['Version'].Value)
}

function Install-Self {
    param([Parameter(Mandatory)][string]$Root)
    if (-not $PSCommandPath) { throw 'Run this installer from a saved .ps1 file.' }
    $Source = (Resolve-Path -LiteralPath $PSCommandPath).Path
    $Directory = Join-Path $Root $CanonicalToolDirectory
    $Destination = Join-Path $Directory $CanonicalToolName
    New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    $SourceVersion = Get-HeaderVersion -Path $Source
    if ($SourceVersion -ne $ToolVersion) { throw 'Installer header/runtime version mismatch.' }

    if ($Source -ieq $Destination) { return $Destination }
    if (Test-Path -LiteralPath $Destination -PathType Leaf) {
        $InstalledVersion = Get-HeaderVersion -Path $Destination
        $SourceHash = (Get-FileHash -LiteralPath $Source -Algorithm SHA256).Hash
        $InstalledHash = (Get-FileHash -LiteralPath $Destination -Algorithm SHA256).Hash
        if ($InstalledVersion -gt $SourceVersion) { throw "A newer installer exists: $Destination" }
        if (($InstalledVersion -eq $SourceVersion) -and ($SourceHash -ne $InstalledHash)) {
            throw "Installer differs at the same version: $Destination"
        }
        if ($SourceHash -eq $InstalledHash) { return $Destination }
        Copy-Item -LiteralPath $Destination -Destination "$Destination.pre-$SourceVersion.bak" -Force
    }
    Copy-Item -LiteralPath $Source -Destination $Destination -Force
    return $Destination
}

function Find-PostgreSQLPsql {
    $Command = Get-Command psql.exe -ErrorAction SilentlyContinue
    if ($Command) { return $Command.Source }

    $Candidates = @(
        Get-ChildItem -LiteralPath 'C:\Program Files\PostgreSQL' -Filter psql.exe -File -Recurse -ErrorAction SilentlyContinue |
            Sort-Object FullName -Descending
    )
    if ($Candidates.Count -gt 0) { return $Candidates[0].FullName }
    return $null
}

function Save-Report {
    param([Parameter(Mandatory)][string]$Root)
    $WorkspaceRoot = Split-Path -Parent $Root
    $Directory = Join-Path $WorkspaceRoot 'runtime\diagnostics\postgresql'
    $Path = Join-Path $Directory "Riverview-PostgreSQL-Install-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
    $Report = ($ReportLines -join [Environment]::NewLine) + [Environment]::NewLine
    New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    Set-Content -LiteralPath $Path -Value $Report -Encoding utf8NoBOM -NoNewline
    if (Get-Command Set-Clipboard -ErrorAction SilentlyContinue) { Set-Clipboard -Value $Report }
    elseif (Get-Command clip.exe -ErrorAction SilentlyContinue) { $Report | & clip.exe }
    Write-Host "`nComplete report copied to the Windows clipboard." -ForegroundColor Cyan
    Write-Host "Durable report: $Path" -ForegroundColor Green
}

try {
    Add-Section -Title 'RIVERVIEW POSTGRESQL DISCOVERY'
    if (-not (Test-Path -LiteralPath $RepositoryPath -PathType Container)) {
        throw "Repository not found: $RepositoryPath"
    }
    $RepositoryPath = (Resolve-Path -LiteralPath $RepositoryPath).Path
    if (-not (Test-Path -LiteralPath (Join-Path $RepositoryPath '.git') -PathType Container)) {
        throw "Git metadata not found: $RepositoryPath"
    }
    $InstalledTool = Install-Self -Root $RepositoryPath
    Add-ReportLine -Text "Reusable installer: $InstalledTool" -Color Green

    $PsqlPath = Find-PostgreSQLPsql
    $Services = @(Get-Service -Name 'postgresql*' -ErrorAction SilentlyContinue)

    if (-not $PsqlPath) {
        Add-ReportLine -Text 'PostgreSQL command-line tools were not found.' -Color Yellow
        if (-not (Get-Command winget.exe -ErrorAction SilentlyContinue)) {
            throw 'winget.exe is unavailable; native PostgreSQL installation cannot continue automatically.'
        }
        if (-not (Test-Administrator)) {
            Add-ReportLine -Text 'Administrator elevation is required. A Windows elevation prompt will open.' -Color Yellow
            $Arguments = @(
                '-NoProfile',
                '-ExecutionPolicy', 'Bypass',
                '-File', "`"$PSCommandPath`"",
                '-RepositoryPath', "`"$RepositoryPath`"",
                '-Port', "$Port",
                '-MajorVersion', "$MajorVersion"
            )
            $Elevated = Start-Process -FilePath 'pwsh.exe' -Verb RunAs -ArgumentList $Arguments -Wait -PassThru
            if ($Elevated.ExitCode -ne 0) { throw "Elevated installer exited with code $($Elevated.ExitCode)." }
            return
        }

        Add-Section -Title 'NATIVE INSTALLATION'
        Add-ReportLine -Text "Installing official Windows package: $PackageId" -Color Cyan
        Add-ReportLine -Text 'The EDB installer will open. Keep server and command-line tools enabled.' -Color Yellow
        Add-ReportLine -Text "Use port $Port and create a strong postgres superuser password. Do not paste that password into chat." -Color Yellow
        Add-ReportLine -Text 'pgAdmin is optional. StackBuilder is not required for Riverview.' -Color Yellow

        & winget.exe show --id $PackageId --exact --accept-source-agreements | Out-Null
        if ($LASTEXITCODE -ne 0) { throw "winget could not resolve package $PackageId." }

        & winget.exe install --id $PackageId --exact --interactive --accept-package-agreements --accept-source-agreements
        if ($LASTEXITCODE -ne 0) { throw "PostgreSQL installation failed with exit code $LASTEXITCODE." }

        $MachinePath = [Environment]::GetEnvironmentVariable('Path', 'Machine')
        $UserPath = [Environment]::GetEnvironmentVariable('Path', 'User')
        $env:Path = "$MachinePath;$UserPath"
        $PsqlPath = Find-PostgreSQLPsql
        $Services = @(Get-Service -Name 'postgresql*' -ErrorAction SilentlyContinue)
    }

    Add-Section -Title 'POST-INSTALL VERIFICATION'
    if (-not $PsqlPath) { throw 'RIV-DB-0001: PostgreSQL installed but psql.exe was not discovered.' }
    Add-ReportLine -Text "psql: $PsqlPath" -Color Green
    $VersionOutput = & $PsqlPath --version 2>&1
    if ($LASTEXITCODE -ne 0) { throw 'RIV-DB-0002: psql version probe failed.' }
    Add-ReportLine -Text ($VersionOutput -join ' ') -Color Green

    if ($Services.Count -eq 0) { throw 'RIV-DB-0003: No PostgreSQL Windows service was discovered.' }
    foreach ($Service in $Services) {
        Add-ReportLine -Text "Service $($Service.Name): $($Service.Status)" -Color $(if ($Service.Status -eq 'Running') { 'Green' } else { 'Yellow' })
    }
    if (-not ($Services | Where-Object Status -eq 'Running')) {
        throw 'RIV-DB-0004: PostgreSQL is installed but no PostgreSQL service is running.'
    }

    $Listener = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue
    if (-not $Listener) { throw "RIV-DB-0005: No PostgreSQL listener was found on port $Port." }
    Add-ReportLine -Text "Listener verified: 127.0.0.1:$Port or local equivalent" -Color Green

    Add-Section -Title 'INSTALLATION RESULT'
    Add-ReportLine -Text 'Native PostgreSQL installation is operationally visible.' -Color Green
    Add-ReportLine -Text 'Database and Riverview role provisioning remain intentionally separate.'
    Add-ReportLine -Text "Installer version: $ToolVersion"
    Save-Report -Root $RepositoryPath
}
catch {
    Add-Section -Title 'INSTALLATION BLOCKED'
    Add-ReportLine -Text $_.Exception.Message -Color Red
    Add-ReportLine -Text 'No database provisioning was attempted.' -Color Yellow
    if (Test-Path -LiteralPath $RepositoryPath -PathType Container) { Save-Report -Root $RepositoryPath }
    throw
}
