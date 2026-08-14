# Riverview RV-005.2 Replay-Key Structural Repair
# Version: 0.2.7
# Date: 2026-08-14
# Purpose: Repair malformed DEFAULT_KEY declarations structurally, validate actual AST assignments, repair the reusable installer generator, and run full RV-005.2 acceptance.
#
# Checkpoint: RIV-GRC-0002
# No commit, push, roadmap mutation, or migration rewrite is permitted.

[CmdletBinding()]
param([string]$RepositoryPath='A:\Riverview\repo')

CLS
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest

$ToolVersion='0.2.7'
$ExpectedHead='34b672f2acb7dd60ea2536505ff3bd39b93ce40b'
$CheckpointId='RIV-GRC-0002'
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
    $Directory=Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\grace'
    New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    $Path=Join-Path $Directory "RV-005.2-Replay-Key-Structural-Repair-$(Get-Date -Format 'yyyyMMdd-HHmmss').txt"
    $Report=($ReportLines -join [Environment]::NewLine)+[Environment]::NewLine
    Write-Utf8NoBom -Path $Path -Content $Report
    try {
        if(Get-Command Set-Clipboard -ErrorAction SilentlyContinue){ Set-Clipboard $Report }
        else { $Report | clip.exe }
        Write-Host "`nComplete repair report copied to the Windows clipboard." -ForegroundColor Cyan
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
    $Capture=Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\grace\repair-capture'
    New-Item -ItemType Directory -Path $Capture -Force | Out-Null
    $Stamp=Get-Date -Format 'yyyyMMdd-HHmmssfff'
    $Out=Join-Path $Capture "$Label-$Stamp.stdout.txt"
    $Err=Join-Path $Capture "$Label-$Stamp.stderr.txt"
    $Process=Start-Process -FilePath $FilePath -ArgumentList $ArgumentList -WorkingDirectory $RepositoryPath -RedirectStandardOutput $Out -RedirectStandardError $Err -Wait -PassThru
    if(Test-Path $Out){ foreach($Line in @(Get-Content $Out -Encoding UTF8)){ Add-Line $Line } }
    if(Test-Path $Err){ foreach($Line in @(Get-Content $Err -Encoding UTF8)){ Add-Line $Line $(if($Process.ExitCode -eq 0){'Yellow'}else{'Red'}) } }
    if($Process.ExitCode -ne 0){ throw "${CheckpointId}: $Label failed with exit code $($Process.ExitCode)." }
}
function Backup-File {
    param([Parameter(Mandatory)][string]$Path,[Parameter(Mandatory)][string]$Label)
    if(-not(Test-Path $Path -PathType Leaf)){ return }
    $Directory=Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\grace\backups'
    New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    $Safe=($Label -replace '[^A-Za-z0-9_.-]','_')
    $Backup=Join-Path $Directory "$Safe-pre-$ToolVersion-$(Get-Date -Format 'yyyyMMdd-HHmmssfff').bak"
    Copy-Item $Path $Backup -Force
    Add-Line "BACKUP  $Path -> $Backup" Yellow
}

try {
    Add-Section 'RIVERVIEW RV-005.2 REPLAY-KEY STRUCTURAL REPAIR'

    $RepositoryPath=(Resolve-Path $RepositoryPath).Path
    $Python=Join-Path $RepositoryPath '.venv\Scripts\python.exe'
    $Head=(git.exe -C $RepositoryPath rev-parse HEAD).Trim()
    $Branch=(git.exe -C $RepositoryPath branch --show-current).Trim()

    Add-Line "Repository: $RepositoryPath" Green
    Add-Line "Branch: $Branch"
    Add-Line "Local HEAD: $Head"
    Add-Line "Repair version: $ToolVersion"

    Add-Section 'CHARTER AND RV-005.2 SCOPE ANCHOR'
    Add-Line 'Current waypoint: RV-005.2 - Objective and stage model.'
    Add-Line 'Root cause: broad substring replacement could transform DEFAULT_KEY into DEFAULT_DEFAULT_KEY while weaker validators still passed.'
    Add-Line 'Exact repair: normalize the declaration only at complete line boundaries, require a real Python AST assignment to DEFAULT_KEY, repair the installer generator structurally, then run full acceptance.'
    Add-Line 'Prohibited: migration rewrite, RV-005.3 behavior, roadmap mutation, commit, or push.'

    if($Branch -ne 'main'){ throw "${CheckpointId}: Expected main branch, observed $Branch." }
    if($Head -ne $ExpectedHead){ throw "${CheckpointId}: Expected HEAD $ExpectedHead, observed $Head." }
    if(-not(Test-Path $Python)){ throw 'RIV-BLD-0006: virtual environment missing.' }

    Add-Section 'SELF-INSTALLATION'
    $RepairPath=Join-Path $RepositoryPath 'tools\powershell\grace\Repair-RiverviewObjectiveStageAcceptance.ps1'
    New-Item -ItemType Directory -Path (Split-Path -Parent $RepairPath) -Force | Out-Null
    if([IO.Path]::GetFullPath($PSCommandPath) -ne [IO.Path]::GetFullPath($RepairPath)){
        Backup-File -Path $RepairPath -Label 'Repair-RiverviewObjectiveStageAcceptance.ps1'
        Copy-Item $PSCommandPath $RepairPath -Force
        Add-Line "Installed repair tool: $RepairPath" Green
    }

    $AcceptancePath=Join-Path $RepositoryPath 'src\riverview\grace\objective_acceptance.py'
    $InstallerPath=Join-Path $RepositoryPath 'tools\powershell\grace\Install-RiverviewObjectiveStageModel.ps1'
    $PublisherPath=Join-Path $RepositoryPath 'tools\powershell\synchronization\Publish-RiverviewObjectiveStageModel.ps1'
    $CheckpointPath=Join-Path $RepositoryPath 'docs\operations\troubleshooting\checkpoints\RIV-GRC-0002_OBJECTIVE_STAGE_MODEL.md'
    $MigrationPath=Join-Path $RepositoryPath 'database\migrations\0010_objective_stage_model.sql'

    foreach($Required in @($AcceptancePath,$InstallerPath,$PublisherPath,$CheckpointPath,$MigrationPath)){
        if(-not(Test-Path $Required -PathType Leaf)){ throw "${CheckpointId}: required file missing: $Required" }
    }

    Add-Section 'PRE-REPAIR WORKING TREE'
    foreach($Line in @(git.exe -C $RepositoryPath status --porcelain=v1 --untracked-files=all)){ Add-Line $Line Yellow }
    if(@(git.exe -C $RepositoryPath diff --cached --name-only).Count -ne 0){ throw "${CheckpointId}: staged files exist." }

    $MigrationHash=(Get-FileHash $MigrationPath -Algorithm SHA256).Hash
    Add-Line "Migration 0010 protected SHA256: $MigrationHash"

    Add-Section 'BACKUP TARGETS'
    Backup-File -Path $AcceptancePath -Label 'objective_acceptance.py'
    Backup-File -Path $InstallerPath -Label 'Install-RiverviewObjectiveStageModel.ps1'
    Backup-File -Path $CheckpointPath -Label 'RIV-GRC-0002_OBJECTIVE_STAGE_MODEL.md'

    Add-Section 'STRUCTURAL NORMALIZATION OF LIVE ACCEPTANCE'
    $Acceptance=Get-Content $AcceptancePath -Raw -Encoding UTF8

    # Normalize any malformed *KEY declaration at the start of a complete Python line.
    $Pattern='(?m)^[A-Z_]*KEY="acceptance\.rv0052\.restart"\s*$'
    $Matches=[regex]::Matches($Acceptance,$Pattern)
    Add-Line "Observed replay-key declaration lines before normalization: $($Matches.Count)"
    if($Matches.Count -ne 1){
        throw "${CheckpointId}: expected exactly one replay-key declaration line, found $($Matches.Count)."
    }

    $Acceptance=[regex]::Replace(
        $Acceptance,
        $Pattern,
        'DEFAULT_KEY="acceptance.rv0052.restart"',
        1
    )
    $Acceptance=$Acceptance.Replace('Version: 0.2.5','Version: 0.2.7').Replace('Version: 0.2.4','Version: 0.2.7')

    Write-Utf8NoBom -Path $AcceptancePath -Content $Acceptance
    Add-Line 'UPDATED  src/riverview/grace/objective_acceptance.py' Green

    Add-Section 'AST ASSIGNMENT AND REFERENCE VALIDATION'
    $AstProbe=Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\grace\validate_rv0052_key_ast_027.py'
    $AstText=@'
from __future__ import annotations
import ast
from pathlib import Path

path=Path(r"__PATH__")
source=path.read_text(encoding="utf-8")
tree=ast.parse(source,filename=str(path))

assignments=[]
bad_key_names=[]
bad_default_names=[]
for node in ast.walk(tree):
    if isinstance(node,ast.Assign):
        for target in node.targets:
            if isinstance(target,ast.Name):
                if target.id=="DEFAULT_KEY":
                    assignments.append((node.lineno,ast.literal_eval(node.value) if isinstance(node.value,ast.Constant) else None))
                if target.id=="KEY":
                    bad_key_names.append((node.lineno,"assignment"))
                if target.id.startswith("DEFAULT_") and target.id.endswith("_KEY") and target.id!="DEFAULT_KEY":
                    bad_default_names.append((node.lineno,target.id))
    if isinstance(node,ast.Name) and node.id=="KEY":
        bad_key_names.append((node.lineno,type(node.ctx).__name__))

if bad_key_names:
    raise RuntimeError(f"RIV-GRC-0002: standalone KEY identifiers remain: {bad_key_names}")
if bad_default_names:
    raise RuntimeError(f"RIV-GRC-0002: malformed DEFAULT_*_KEY identifiers remain: {bad_default_names}")
if assignments != [(assignments[0][0],"acceptance.rv0052.restart")] if assignments else True:
    raise RuntimeError(f"RIV-GRC-0002: unexpected DEFAULT_KEY assignments: {assignments}")
if len(assignments)!=1:
    raise RuntimeError(f"RIV-GRC-0002: expected exactly one DEFAULT_KEY assignment, found {assignments}")

required=[
    'def seed(key: str)',
    'def read_and_finish(key: str)',
    'if state["objective_key"]!=key:',
    'key=sys.argv[2] if len(sys.argv)>2 else DEFAULT_KEY',
]
missing=[item for item in required if item not in source]
if missing:
    raise RuntimeError(f"RIV-GRC-0002: parameterized contract incomplete: {missing}")

print(f"ast_key_contract=healthy default_key_assignments={len(assignments)} standalone_KEY=0 malformed_default_names=0")
'@
    $AstText=$AstText.Replace('__PATH__',$AcceptancePath.Replace('\','\\'))
    Write-Utf8NoBom -Path $AstProbe -Content $AstText
    Invoke-Captured -FilePath $Python -ArgumentList @($AstProbe) -Label 'ast_key_contract'

    Add-Section 'STRUCTURAL NORMALIZATION OF CANONICAL INSTALLER GENERATOR'
    $Installer=Get-Content $InstallerPath -Raw -Encoding UTF8

    $InstallerMatches=[regex]::Matches($Installer,$Pattern)
    Add-Line "Installer embedded replay-key declaration matches: $($InstallerMatches.Count)"
    if($InstallerMatches.Count -ne 1){
        throw "${CheckpointId}: expected exactly one embedded replay-key declaration in installer, found $($InstallerMatches.Count)."
    }

    $Installer=[regex]::Replace(
        $Installer,
        $Pattern,
        'DEFAULT_KEY="acceptance.rv0052.restart"',
        1
    )
    $Installer=$Installer.Replace('# Version: 0.2.5','# Version: 0.2.7')
    $Installer=$Installer.Replace("`$ToolVersion='0.2.5'","`$ToolVersion='0.2.7'")
    $Installer=$Installer.Replace('Version: 0.2.5','Version: 0.2.7')

    if(-not $Installer.Contains('acceptance.rv0052.install.')){
        throw "${CheckpointId}: installer does not supply a fresh acceptance key."
    }
    if($Installer.Contains("@('-m','riverview.grace.objective_acceptance','seed')") -or
       $Installer.Contains("@('-m','riverview.grace.objective_acceptance','read')")){
        throw "${CheckpointId}: installer contains unkeyed replay calls."
    }

    Write-Utf8NoBom -Path $InstallerPath -Content $Installer
    Add-Line 'UPDATED  tools/powershell/grace/Install-RiverviewObjectiveStageModel.ps1' Green

    Add-Section 'PUBLISHER CONTRACT CHECK'
    $Publisher=Get-Content $PublisherPath -Raw -Encoding UTF8
    $PublisherTokens=@(
        '# Version: 0.2.6',
        'acceptance.rv0052.publish.',
        "'riverview.grace.objective_acceptance','seed',`$AcceptanceKey",
        "'riverview.grace.objective_acceptance','read',`$AcceptanceKey",
        'REMOTE VERIFIED'
    )
    foreach($Token in $PublisherTokens){
        if(-not $Publisher.Contains($Token)){ throw "${CheckpointId}: publisher missing contract token: $Token" }
    }
    Add-Line 'Fresh v0.2.6 publisher contract passed.' Green

    Add-Section 'UPDATE COOKBOOK CHECKPOINT'
    $Checkpoint=Get-Content $CheckpointPath -Raw -Encoding UTF8
    $Checkpoint=$Checkpoint.Replace('Version: 0.2.6','Version: 0.2.7').Replace('Version: 0.2.5','Version: 0.2.7')
    if($Checkpoint -notmatch 'DEFAULT_DEFAULT_KEY'){
        $Checkpoint += @'

Sixth observed repair evidence:
- Broad substring replacement of `KEY="acceptance.rv0052.restart"` can match inside the already-correct identifier `DEFAULT_KEY`.
- Repeated application can therefore produce `DEFAULT_DEFAULT_KEY`, while weaker substring validators still appear to find `DEFAULT_KEY`.
- Ruff exposed the real failure because the CLI referenced `DEFAULT_KEY`, which was no longer actually assigned.

Recovery verification:
- Normalize only a complete line matching `^[A-Z_]*KEY="acceptance.rv0052.restart"$`.
- Parse the resulting Python AST.
- Require exactly one assignment target named `DEFAULT_KEY` with value `acceptance.rv0052.restart`.
- Reject any standalone `KEY` identifier or malformed `DEFAULT_*_KEY` assignment.
- Run two fresh-key cross-process restart/resume cycles.
'@
    }
    Write-Utf8NoBom -Path $CheckpointPath -Content $Checkpoint
    Add-Line 'UPDATED  RIV-GRC-0002 Cookbook checkpoint' Green

    Add-Section 'MIGRATION IMMUTABILITY'
    $MigrationHashAfter=(Get-FileHash $MigrationPath -Algorithm SHA256).Hash
    if($MigrationHashAfter -ne $MigrationHash){ throw "${CheckpointId}: migration 0010 changed during repair." }
    Add-Line 'Migration 0010 remained byte-for-byte unchanged.' Green

    Add-Section 'FULL STATIC AND CONTRACT ACCEPTANCE'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','compileall','-q','src\riverview\grace') -Label 'compile'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','ruff','check','src\riverview\grace','tests\test_objective_stage_model.py') -Label 'ruff'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','pytest','-q','tests\test_objective_stage_model.py') -Label 'tests'

    Add-Section 'TWO FRESH CROSS-PROCESS RESTART/RESUME CYCLES'
    $Key1="acceptance.rv0052.repair.$([Guid]::NewGuid().ToString('N'))"
    $Key2="acceptance.rv0052.repair.$([Guid]::NewGuid().ToString('N'))"

    Add-Line "Acceptance key 1: $Key1"
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','riverview.grace.objective_acceptance','seed',$Key1) -Label 'seed_1'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','riverview.grace.objective_acceptance','read',$Key1) -Label 'read_1'
    Add-Line 'First fresh-key restart/resume cycle passed.' Green

    Add-Line "Acceptance key 2: $Key2"
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','riverview.grace.objective_acceptance','seed',$Key2) -Label 'seed_2'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','riverview.grace.objective_acceptance','read',$Key2) -Label 'read_2'
    Add-Line 'Second fresh-key restart/resume cycle passed.' Green

    Add-Section 'GRACE AUTHORITY REGRESSION'
    Invoke-Captured -FilePath $Python -ArgumentList @('-m','riverview.grace.acceptance') -Label 'grace_authority'
    Add-Line 'Grace authority acceptance passed.' Green

    Add-Section 'MIGRATION LEDGER VERIFICATION'
    $LedgerProbe=Join-Path (Split-Path -Parent $RepositoryPath) 'runtime\diagnostics\grace\verify_0010_repair_027.py'
    $LedgerText=@'
from pathlib import Path
import hashlib
from riverview.database import connect
root=Path(r"__ROOT__")
path=root/"database/migrations/0010_objective_stage_model.sql"
checksum=hashlib.sha256(path.read_bytes()).hexdigest()
with connect() as connection, connection.cursor() as cursor:
    cursor.execute("SELECT version,checksum_sha256 FROM schema_migrations WHERE migration_id='0010'")
    row=cursor.fetchone()
    if row is None or row[0]!="0.2.0" or row[1].lower()!=checksum.lower():
        raise RuntimeError(f"RIV-DB-0006: migration 0010 mismatch: {row!r} local={checksum}")
    print(f"migration_0010=verified version={row[0]} checksum={row[1]}")
    connection.rollback()
'@
    $LedgerText=$LedgerText.Replace('__ROOT__',$RepositoryPath.Replace('\','\\'))
    Write-Utf8NoBom -Path $LedgerProbe -Content $LedgerText
    Invoke-Captured -FilePath $Python -ArgumentList @($LedgerProbe) -Label 'migration_0010'

    Add-Section 'FINAL WORKING TREE'
    foreach($Line in @(git.exe -C $RepositoryPath status --porcelain=v1 --untracked-files=all)){ Add-Line $Line Yellow }

    Add-Section 'RV-005.2 REPAIR RESULT'
    Add-Line 'Malformed replay-key declaration was structurally normalized.' Green
    Add-Line 'Python AST proves exactly one valid DEFAULT_KEY assignment and no standalone KEY identifier.' Green
    Add-Line 'Canonical installer generator is structurally normalized and replay-safe.' Green
    Add-Line 'Canonical publisher v0.2.6 contract remains intact.' Green
    Add-Line 'Two independent fresh-key cross-process restart/resume cycles passed.' Green
    Add-Line 'Migration 0010 remained unchanged and ledger-verified.' Green
    Add-Line 'No commit, push, or roadmap mutation was performed.' Green
    Add-Line 'RV-005.2 is locally acceptance-complete. Next stage: run the canonical exact-scope publisher.' Green
    Save-Report
}
catch {
    Add-Section 'RV-005.2 REPAIR BLOCKED'
    $Message=$_.Exception.Message
    if([string]::IsNullOrWhiteSpace($Message)){ $Message=$_.ToString() }
    Add-Line $Message Red
    Add-Line 'No commit or push was performed.' Yellow
    Save-Report
    throw
}
