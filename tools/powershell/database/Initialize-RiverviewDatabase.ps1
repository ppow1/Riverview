# Riverview PostgreSQL Provisioning Tool
# Version: 0.1.0
# Purpose: Create protected local credentials, provision the Riverview database role, and apply migration 0001.
# Updated: 2026-08-14

[CmdletBinding()]
param(
    [string]$RepositoryPath = 'A:\Riverview\repo',
    [string]$HostName = '127.0.0.1',
    [ValidateRange(1, 65535)][int]$Port = 5432,
    [ValidatePattern('^[a-z][a-z0-9_]{0,62}$')][string]$DatabaseName = 'riverview',
    [ValidatePattern('^[a-z][a-z0-9_]{0,62}$')][string]$ApplicationRole = 'riverview_app'
)

CLS
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest

$ToolVersion = [version]'0.1.0'
$CanonicalName = 'Initialize-RiverviewDatabase.ps1'
$ReportLines = [System.Collections.Generic.List[string]]::new()

function Add-Line {
    param([Parameter(Mandatory)][AllowEmptyString()][string]$Text, [ConsoleColor]$Color = 'Gray')
    $ReportLines.Add($Text)
    Write-Host $Text -ForegroundColor $Color
}

function Add-Section {
    param([Parameter(Mandatory)][string]$Title)
    Add-Line ''
    Add-Line "=== $Title ===" Cyan
}

function Find-PostgreSQLTool {
    param([Parameter(Mandatory)][string]$Name)
    $Command = Get-Command "$Name.exe" -ErrorAction SilentlyContinue
    if ($Command) { return $Command.Source }
    $Candidate = Get-ChildItem 'C:\Program Files\PostgreSQL' -Filter "$Name.exe" -File -Recurse -ErrorAction SilentlyContinue |
        Sort-Object FullName -Descending | Select-Object -First 1
    if ($Candidate) { return $Candidate.FullName }
    throw "RIV-DB-0001: $Name.exe was not found."
}

function ConvertTo-PlainText {
    param([Parameter(Mandatory)][Security.SecureString]$SecureValue)
    $Pointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecureValue)
    try { return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($Pointer) }
    finally { [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($Pointer) }
}

function Invoke-Psql {
    param(
        [Parameter(Mandatory)][string]$Executable,
        [Parameter(Mandatory)][string]$User,
        [Parameter(Mandatory)][string]$Database,
        [Parameter(Mandatory)][string]$Password,
        [Parameter(Mandatory)][string]$Sql
    )
    $PreviousPassword = $env:PGPASSWORD
    try {
        $env:PGPASSWORD = $Password
        $Output = @($Sql | & $Executable -X -t -A -h $HostName -p $Port -U $User -d $Database -v ON_ERROR_STOP=1 2>&1 | ForEach-Object { "$_" })
        if ($LASTEXITCODE -ne 0) { throw ($Output -join [Environment]::NewLine) }
        return $Output
    }
    finally {
        if ($null -eq $PreviousPassword) { Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue }
        else { $env:PGPASSWORD = $PreviousPassword }
    }
}

function Save-Report {
    $Root = Split-Path -Parent $RepositoryPath
    $Directory = Join-Path $Root 'runtime\diagnostics\postgresql'
    $Path = Join-Path $Directory "Riverview-Database-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
    $Report = ($ReportLines -join [Environment]::NewLine) + [Environment]::NewLine
    New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    Set-Content -LiteralPath $Path -Value $Report -Encoding utf8NoBOM -NoNewline
    if (Get-Command Set-Clipboard -ErrorAction SilentlyContinue) { Set-Clipboard $Report }
    else { $Report | clip.exe }
    Write-Host "`nComplete report copied to the Windows clipboard." -ForegroundColor Cyan
    Write-Host "Durable report: $Path" -ForegroundColor Green
}

try {
    Add-Section 'RIVERVIEW DATABASE VALIDATION'
    $RepositoryPath = (Resolve-Path $RepositoryPath).Path
    if (-not (Test-Path (Join-Path $RepositoryPath '.git'))) { throw 'Riverview Git repository not found.' }
    $Psql = Find-PostgreSQLTool 'psql'
    $Createdb = Find-PostgreSQLTool 'createdb'
    $Migration = Join-Path $RepositoryPath 'database\migrations\0001_river_foundation.sql'
    if (-not (Test-Path $Migration -PathType Leaf)) { throw 'Migration 0001 was not found.' }
    Add-Line "psql: $Psql" Green
    Add-Line "Migration: $Migration" Green

    Add-Section 'SELF-INSTALLATION'
    if (-not $PSCommandPath) { throw 'Run this tool from a saved .ps1 file.' }
    $ToolDirectory = Join-Path $RepositoryPath 'tools\powershell\database'
    $InstalledTool = Join-Path $ToolDirectory $CanonicalName
    New-Item -ItemType Directory $ToolDirectory -Force | Out-Null
    $SourcePath = [IO.Path]::GetFullPath($PSCommandPath)
    $DestinationPath = [IO.Path]::GetFullPath($InstalledTool)
    if ($SourcePath -ne $DestinationPath) {
        Copy-Item -LiteralPath $SourcePath -Destination $DestinationPath -Force
        Add-Line "Installed reusable tool: $InstalledTool" Green
    }
    else { Add-Line "Running repository tool: $InstalledTool" Green }

    Add-Section 'LOCAL CREDENTIAL STORE'
    $AdminSecure = Read-Host 'Enter the temporary postgres administrator password' -AsSecureString
    $AdminPlain = ConvertTo-PlainText $AdminSecure
    $RandomBytes = [Security.Cryptography.RandomNumberGenerator]::GetBytes(32)
    $ApplicationPlain = [Convert]::ToBase64String($RandomBytes).TrimEnd('=').Replace('+', '-').Replace('/', '_')
    $ApplicationSecure = ConvertTo-SecureString $ApplicationPlain -AsPlainText -Force

    $SecretsDirectory = 'A:\Riverview\data\secrets\postgresql'
    New-Item -ItemType Directory $SecretsDirectory -Force | Out-Null
    $AdminSecretPath = Join-Path $SecretsDirectory 'postgres-admin.dpapi'
    $ApplicationSecretPath = Join-Path $SecretsDirectory 'riverview-app.dpapi'
    $MetadataPath = Join-Path $SecretsDirectory 'credential-metadata.json'
    $AdminSecure | ConvertFrom-SecureString | Set-Content $AdminSecretPath -Encoding ascii
    $ApplicationSecure | ConvertFrom-SecureString | Set-Content $ApplicationSecretPath -Encoding ascii

    $Identity = "$env:USERDOMAIN\$env:USERNAME"
    & icacls.exe $SecretsDirectory /inheritance:r /grant:r "${Identity}:(OI)(CI)F" | Out-Null
    if ($LASTEXITCODE -ne 0) { throw 'RIV-DB-0006: Secret-directory ACL configuration failed.' }

    [ordered]@{
        version = '0.1.0'; host = $HostName; port = $Port; database = $DatabaseName
        application_role = $ApplicationRole; protection = 'Windows DPAPI CurrentUser'
        admin_secret = $AdminSecretPath; application_secret = $ApplicationSecretPath
        created_at = (Get-Date).ToUniversalTime().ToString('o')
    } | ConvertTo-Json | Set-Content $MetadataPath -Encoding utf8NoBOM
    Add-Line "Protected credential metadata: $MetadataPath" Green
    Add-Line 'Credential values were excluded from output.' Green

    Add-Section 'ROLE AND DATABASE PROVISIONING'
    $RoleSql = @"
DO `$riverview`$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = '$ApplicationRole') THEN
        CREATE ROLE $ApplicationRole LOGIN PASSWORD '$ApplicationPlain';
    ELSE
        ALTER ROLE $ApplicationRole WITH LOGIN PASSWORD '$ApplicationPlain';
    END IF;
END
`$riverview`$;
"@
    Invoke-Psql $Psql 'postgres' 'postgres' $AdminPlain $RoleSql | Out-Null
    Add-Line "Application role ready: $ApplicationRole" Green

    $Exists = (Invoke-Psql $Psql 'postgres' 'postgres' $AdminPlain "SELECT 1 FROM pg_database WHERE datname = '$DatabaseName';") -join ''
    if ($Exists.Trim() -ne '1') {
        $PreviousPassword = $env:PGPASSWORD
        try {
            $env:PGPASSWORD = $AdminPlain
            & $Createdb -h $HostName -p $Port -U postgres -O $ApplicationRole $DatabaseName
            if ($LASTEXITCODE -ne 0) { throw 'RIV-DB-0007: Database creation failed.' }
        }
        finally {
            if ($null -eq $PreviousPassword) { Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue }
            else { $env:PGPASSWORD = $PreviousPassword }
        }
        Add-Line "Database created: $DatabaseName" Green
    }
    else { Add-Line "Database already exists: $DatabaseName" Green }

    Add-Section 'MIGRATION AND ACCEPTANCE'
    $TableExists = (Invoke-Psql $Psql $ApplicationRole $DatabaseName $ApplicationPlain "SELECT to_regclass('public.river_events') IS NOT NULL;") -join ''
    if ($TableExists.Trim() -ne 't') {
        $PreviousPassword = $env:PGPASSWORD
        try {
            $env:PGPASSWORD = $ApplicationPlain
            & $Psql -X -h $HostName -p $Port -U $ApplicationRole -d $DatabaseName -v ON_ERROR_STOP=1 -f $Migration | Out-Null
            if ($LASTEXITCODE -ne 0) { throw 'RIV-DB-0008: Migration 0001 failed.' }
        }
        finally {
            if ($null -eq $PreviousPassword) { Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue }
            else { $env:PGPASSWORD = $PreviousPassword }
        }
        $Checksum = (Get-FileHash $Migration -Algorithm SHA256).Hash.ToLowerInvariant()
        Invoke-Psql $Psql $ApplicationRole $DatabaseName $ApplicationPlain "INSERT INTO schema_migrations (migration_id, version, checksum_sha256) VALUES ('0001', '0.1.0', '$Checksum');" | Out-Null
        Add-Line 'Migration 0001 applied and recorded.' Green
    }
    else { Add-Line 'Migration 0001 tables already exist; destructive reapplication skipped.' Yellow }

    $Tables = Invoke-Psql $Psql $ApplicationRole $DatabaseName $ApplicationPlain "SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;"
    foreach ($Table in $Tables) { if ($Table.Trim()) { Add-Line "TABLE $($Table.Trim())" Green } }

    Add-Section 'DATABASE RESULT'
    Add-Line 'Riverview PostgreSQL provisioning and migration acceptance passed.' Green
    Add-Line "Database: $DatabaseName" Green
    Add-Line "Application role: $ApplicationRole" Green
    Add-Line "Credential protection: Windows DPAPI CurrentUser" Green
    Add-Line "Tool version: $ToolVersion"
    Save-Report
}
catch {
    Add-Section 'DATABASE PROVISIONING BLOCKED'
    Add-Line $_.Exception.Message Red
    Add-Line 'Credential values were not copied to the report.' Yellow
    if (Test-Path $RepositoryPath -PathType Container) { Save-Report }
    throw
}
finally {
    $AdminPlain = $null
    $ApplicationPlain = $null
    Remove-Item Env:PGPASSWORD -ErrorAction SilentlyContinue
}
