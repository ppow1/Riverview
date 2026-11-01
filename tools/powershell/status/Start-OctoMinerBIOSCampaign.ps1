# OctoMiner BIOS Campaign manual startup
# Purpose: restore the Steward status surface and SNAIL coordinator against the existing durable runtime.
# Campaign PowerShell contract: no else token.

[CmdletBinding()]
param(
    [string]$RepositoryPath='A:\Riverview\standalone',
    [string]$CampaignRepository='T:\OctoMiner_BIOS_Campaign\repo',
    [string]$SnailRuntime='T:\OctoMiner_BIOS_Campaign\repo\runtime\snail',
    [int]$Port=8785
)

Clear-Host
$ErrorActionPreference='Stop'
$Result=@()
$Python=Join-Path $RepositoryPath '.venv\Scripts\python.exe'
$StewardLauncher=Join-Path $RepositoryPath 'tools\powershell\status\Start-RiverviewStewardStatus.ps1'
$Requirements=Join-Path $RepositoryPath 'docs\operations\octominer\campaign\PROJECT_REQUIREMENTS.md'
$ProcessMap=Join-Path $RepositoryPath 'docs\operations\octominer\campaign\PROCESS_MAP.md'
$CampaignDocs=Join-Path $CampaignRepository 'docs\operations\octominer\campaign'

$Result+='========== OCTOMINER BIOS CAMPAIGN MANUAL START =========='
$Result+="TIME=$(Get-Date -Format o)"
$Result+="REPOSITORY=$RepositoryPath"
$Result+="CAMPAIGN_REPOSITORY=$CampaignRepository"
$Result+="SNAIL_RUNTIME=$SnailRuntime"
$Result+=''

if(-not(Test-Path $Python)){throw "Riverview Python not found: $Python"}
if(-not(Test-Path $StewardLauncher)){throw "Steward launcher not found: $StewardLauncher"}
if(-not(Test-Path (Join-Path $SnailRuntime 'state.json'))){throw "Existing SNAIL state not found: $SnailRuntime"}
if(-not(Test-Path $Requirements)){throw "Project requirements not found: $Requirements"}
if(-not(Test-Path $ProcessMap)){throw "Process map not found: $ProcessMap"}

New-Item -ItemType Directory -Path $CampaignDocs -Force | Out-Null
Copy-Item -LiteralPath $Requirements -Destination (Join-Path $CampaignDocs 'PROJECT_REQUIREMENTS.md') -Force
Copy-Item -LiteralPath $ProcessMap -Destination (Join-Path $CampaignDocs 'PROCESS_MAP.md') -Force
$Result+='CAMPAIGN_DOC_SYNC=OK'

$StewardArgs=@(
    '-NoExit','-ExecutionPolicy','Bypass','-File',$StewardLauncher,
    '-RepositoryPath',$RepositoryPath,
    '-Port',"$Port",
    '-SnailRuntime',$SnailRuntime
)
Start-Process powershell.exe -ArgumentList $StewardArgs
$Result+="STEWARD_START_REQUESTED=http://127.0.0.1:$Port/"

Start-Sleep -Seconds 2
$Health=$null
try{$Health=Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:$Port/api/snail/status" -TimeoutSec 5}catch{$Result+="STEWARD_CHECK_ERROR=$($_.Exception.Message)"}
if($null -ne $Health){$Result+="STEWARD_HTTP_STATUS=$($Health.StatusCode)"}

$CoordinatorHelp=& $Python -m riverview.snail --help 2>&1
$Result+='=== SNAIL CLI DISCOVERY ==='
$Result+=$CoordinatorHelp
$Result+=''
$Result+='NOTE=This launcher restores the Steward surface against the existing durable runtime. It does not issue RESUME, START, BIOS mutation, HID, reboot, or power actions.'
$Result+='SNAIL_STATE_MUTATION=NO'
$Result+='BIOS_MUTATION=NO'
$Result+='HID_ACTION=NO'
$Result+='REBOOT_ACTION=NO'
$Result+='POWER_ACTION=NO'
$Result+='========== MANUAL START COMPLETE =========='

$Result|ForEach-Object{Write-Host $_}
Set-Clipboard -Value ($Result -join "`r`n")
Start-Process "http://127.0.0.1:$Port/"
Write-Host ''
Write-Host '========== COMPLETE RESULT COPIED TO CLIPBOARD =========='
