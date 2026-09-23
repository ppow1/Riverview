$ErrorActionPreference = "Stop"

$GatewayScript = "A:\Riverview\standalone\HermesVisionGateway.ps1"
$ExpectedGatewayHash = "A101B547E065BCDFA763BD1098ED347087ABB2B387F1F8EF4946FD10E226D68C"
$TaskName = "Riverview Hermes Multimodal Gateway"
$GatewayURL = "http://localhost:8092"
$BundledVisionImage = Join-Path $PSScriptRoot "hermes-vision-test.png"
$RepositoryVisionImage = Join-Path $PSScriptRoot "test-assets\hermes-vision-test.png"

if (Test-Path $BundledVisionImage) {
    $VisionImage = $BundledVisionImage
}
else {
    $VisionImage = $RepositoryVisionImage
}

$Pass = 0
$Fail = 0

function Write-TestResult {
    param(
        [string]$Name,
        [bool]$Success,
        [string]$Detail = ""
    )

    if ($Success) {
        $script:Pass++
        Write-Output ("PASS  {0}" -f $Name)
    }
    else {
        $script:Fail++
        Write-Output ("FAIL  {0}" -f $Name)
    }

    if ($Detail) {
        Write-Output ("      {0}" -f $Detail)
    }
}

Write-Output "============================================================"
Write-Output " RIVERVIEW HERMES MULTIMODAL SELF-TEST"
Write-Output "============================================================"
Write-Output ""

# ------------------------------------------------------------
# 1. Gateway script
# ------------------------------------------------------------

if (Test-Path $GatewayScript) {
    Write-TestResult "Gateway script exists" $true $GatewayScript

    $actualHash = (Get-FileHash $GatewayScript -Algorithm SHA256).Hash

    Write-TestResult `
        "Gateway SHA256 matches known-good" `
        ($actualHash -eq $ExpectedGatewayHash) `
        "SHA256: $actualHash"
}
else {
    Write-TestResult "Gateway script exists" $false $GatewayScript
}

# ------------------------------------------------------------
# 2. Scheduled task
# ------------------------------------------------------------

$task = Get-ScheduledTask `
    -TaskName $TaskName `
    -ErrorAction SilentlyContinue

if ($null -ne $task) {
    Write-TestResult "Scheduled task exists" $true $TaskName

    $taskInfo = Get-ScheduledTaskInfo -TaskName $TaskName

    Write-Output ("      State: {0}" -f $task.State)
    Write-Output ("      Last Run: {0}" -f $taskInfo.LastRunTime)
    Write-Output ("      Last Result: {0}" -f $taskInfo.LastTaskResult)

    $correctAction = $false

    foreach ($action in $task.Actions) {
        if (
            $action.Execute -eq "C:\Program Files\PowerShell\7\pwsh.exe" -and
            $action.Arguments -like "*HermesVisionGateway.ps1*"
        ) {
            $correctAction = $true
        }
    }

    Write-TestResult "Scheduled task action" $correctAction
}
else {
    Write-TestResult "Scheduled task exists" $false $TaskName
}

# ------------------------------------------------------------
# 3. Running gateway process
# ------------------------------------------------------------

$gatewayProcesses = @(
    Get-CimInstance Win32_Process |
        Where-Object {
            $_.Name -eq "pwsh.exe" -and
            $_.CommandLine -like "*HermesVisionGateway.ps1*"
        }
)

Write-TestResult `
    "Exactly one gateway process" `
    ($gatewayProcesses.Count -eq 1) `
    ("Count: {0}" -f $gatewayProcesses.Count)

if ($gatewayProcesses.Count -eq 1) {
    Write-Output ("      PID: {0}" -f $gatewayProcesses[0].ProcessId)
}

# ------------------------------------------------------------
# 4. Models endpoint
# ------------------------------------------------------------

try {
    $models = Invoke-RestMethod `
        -Uri "$GatewayURL/v1/models" `
        -TimeoutSec 10

    $modelIds = @($models.data | ForEach-Object { $_.id })

    Write-TestResult `
        "/v1/models endpoint" `
        ($modelIds -contains "hermes-multimodal") `
        ("Models: {0}" -f ($modelIds -join ", "))
}
catch {
    Write-TestResult "/v1/models endpoint" $false $_.Exception.Message
}

# ------------------------------------------------------------
# 5. Text + SSE
# ------------------------------------------------------------

try {
    $textBody = @{
        model = "hermes-multimodal"
        messages = @(
            @{
                role = "user"
                content = "Reply with exactly: SELFTEST_TEXT_4729"
            }
        )
        stream = $true
        temperature = 0
        max_tokens = 32
    } | ConvertTo-Json -Depth 20

    $tempBody = Join-Path $env:TEMP "hermes-selftest-body.json"

    Set-Content `
        -Path $tempBody `
        -Value $textBody `
        -Encoding UTF8

    $sse = & curl.exe -sS -N `
        --max-time 300 `
        -H "Content-Type: application/json" `
        --data-binary "@$tempBody" `
        "$GatewayURL/v1/chat/completions"

    $sseText = $sse -join "`n"

    $textOK =
        $sseText -match '"content":"SELFTEST_TEXT_4729"' -and
        $sseText -match '"finish_reason":"stop"' -and
        $sseText -match 'data: \[DONE\]'

    Write-TestResult "Text + SSE" $textOK

    Remove-Item $tempBody -Force -ErrorAction SilentlyContinue
}
catch {
    Write-TestResult "Text + SSE" $false $_.Exception.Message
}

# ------------------------------------------------------------
# 6. Vision
# ------------------------------------------------------------

if (-not (Test-Path $VisionImage)) {
    Write-TestResult "Vision test image exists" $false $VisionImage
}
else {
    Write-TestResult "Vision test image exists" $true $VisionImage

    try {
        $bytes = [System.IO.File]::ReadAllBytes($VisionImage)
        $base64 = [Convert]::ToBase64String($bytes)

        $visionBody = @{
            model = "hermes-multimodal"
            messages = @(
                @{
                    role = "user"
                    content = @(
                        @{
                            type = "text"
                            text = "Read the text in this image. Reply with exactly the text shown and nothing else."
                        },
                        @{
                            type = "image_url"
                            image_url = @{
                                url = "data:image/png;base64,$base64"
                            }
                        }
                    )
                }
            )
            stream = $false
            temperature = 0
            max_tokens = 32
        } | ConvertTo-Json -Depth 20

        $visionResult = Invoke-RestMethod `
            -Uri "$GatewayURL/v1/chat/completions" `
            -Method Post `
            -ContentType "application/json" `
            -Body $visionBody `
            -TimeoutSec 300

        $visionAnswer =
            [string]$visionResult.choices[0].message.content

        $visionOK =
            $visionAnswer.Trim() -ceq "VISION TEST 4729"

        Write-TestResult `
            "Vision routing" `
            $visionOK `
            ("Returned: [{0}]" -f $visionAnswer.Trim())
    }
    catch {
        Write-TestResult "Vision routing" $false $_.Exception.Message
    }
}

# ------------------------------------------------------------
# 7. Hermes real tool loop
# ------------------------------------------------------------

$ToolProof = "C:\Temp\hermes-selftest-tool-proof.txt"
$ToolMarker = "SELFTEST_TOOL_5831"

Remove-Item $ToolProof -Force -ErrorAction SilentlyContinue

try {
    $hermesCommand = Get-Command hermes -ErrorAction Stop

    $prompt = "Use the terminal tool to create $ToolProof containing exactly $ToolMarker. Then use the terminal tool to read that file back. After you have verified its contents, reply with exactly: $ToolMarker"

    $hermesOutput = & $hermesCommand.Source -z $prompt 2>&1

    $hermesText = ($hermesOutput | Out-String).Trim()

    $fileExists = Test-Path $ToolProof

    $fileText = ""

    if ($fileExists) {
        $fileText = (Get-Content $ToolProof -Raw).Trim()
    }

    $responseOK = $hermesText -eq $ToolMarker
    $fileOK = $fileExists -and ($fileText -ceq $ToolMarker)

    Write-TestResult `
        "Hermes tool-loop response" `
        $responseOK `
        ("Returned: [{0}]" -f $hermesText)

    Write-TestResult `
        "Hermes tool-created file" `
        $fileOK `
        ("File contents: [{0}]" -f $fileText)
}
catch {
    Write-TestResult "Hermes tool-loop response" $false $_.Exception.Message
    Write-TestResult "Hermes tool-created file" $false
}
finally {
    Remove-Item $ToolProof -Force -ErrorAction SilentlyContinue
}
# ------------------------------------------------------------
# Summary
# ------------------------------------------------------------

Write-Output ""
Write-Output "============================================================"
Write-Output " SELF-TEST SUMMARY"
Write-Output "============================================================"
Write-Output ("PASS: {0}" -f $Pass)
Write-Output ("FAIL: {0}" -f $Fail)
Write-Output ""

if ($Fail -eq 0) {
    Write-Output "OVERALL: PASS"
    exit 0
}
else {
    Write-Output "OVERALL: FAIL"
    exit 1
}


