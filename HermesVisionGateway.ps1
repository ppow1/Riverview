$ErrorActionPreference = "Stop"

$ListenPort = 8092
$VisionURL = "http://localhost:11434/v1/chat/completions"
$VisionModel = "qwen3-vl:8b-instruct"
$ReasoningURL = "http://192.168.1.162:8080/v1/chat/completions"
$ReasoningModel = "/root/Qwen3-Next-80B-A3B-Instruct-Q4_K_M.gguf"

$listener = [System.Net.HttpListener]::new()
$listener.Prefixes.Add("http://localhost:$ListenPort/")
$listener.Start()

Write-Host "Hermes Vision Gateway listening on http://localhost:$ListenPort/v1" -ForegroundColor Green
Write-Host "Vision:    $VisionModel -> $VisionURL"
Write-Host "Reasoning: $ReasoningModel -> $ReasoningURL"

function Send-Json {
    param($Response, $Object, [int]$StatusCode = 200)

    $json = $Object | ConvertTo-Json -Depth 30 -Compress
    $bytes = [Text.Encoding]::UTF8.GetBytes($json)

    $Response.StatusCode = $StatusCode
    $Response.ContentType = "application/json"
    $Response.ContentEncoding = [Text.Encoding]::UTF8
    $Response.ContentLength64 = $bytes.Length
    $Response.OutputStream.Write($bytes, 0, $bytes.Length)
    $Response.Close()
}


function Send-SseCompletion {
    param($Response, $Answer)

    $Response.StatusCode = 200
    $Response.ContentType = "text/event-stream"
    $Response.ContentEncoding = [Text.Encoding]::UTF8
    $Response.SendChunked = $true
    $Response.KeepAlive = $false
    $Response.Headers["Cache-Control"] = "no-cache"

    $choice = $Answer.choices[0]
    $message = $choice.message

    $finishReason = $choice.finish_reason
    if ([string]::IsNullOrWhiteSpace([string]$finishReason)) {
        if ($message.tool_calls) {
            $finishReason = "tool_calls"
        }
        else {
            $finishReason = "stop"
        }
    }

    $delta = @{
        role = "assistant"
    }

    if ($null -ne $message.content) {
        $delta.content = [string]$message.content
    }

    if ($message.tool_calls) {
        $delta.tool_calls = $message.tool_calls
    }

    $chunk1 = @{
        id = if ($Answer.id) { $Answer.id } else { "chatcmpl-$(New-Guid)" }
        object = "chat.completion.chunk"
        created = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
        model = "hermes-multimodal"
        choices = @(
            @{
                index = 0
                delta = $delta
                finish_reason = $null
            }
        )
    } | ConvertTo-Json -Depth 30 -Compress

    $chunk2 = @{
        id = if ($Answer.id) { $Answer.id } else { "chatcmpl-$(New-Guid)" }
        object = "chat.completion.chunk"
        created = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
        model = "hermes-multimodal"
        choices = @(
            @{
                index = 0
                delta = @{}
                finish_reason = $finishReason
            }
        )
    } | ConvertTo-Json -Depth 30 -Compress

    foreach ($line in @(
        "data: $chunk1`n`n",
        "data: $chunk2`n`n",
        "data: [DONE]`n`n"
    )) {
        $bytes = [Text.Encoding]::UTF8.GetBytes($line)
        $Response.OutputStream.Write($bytes, 0, $bytes.Length)
        $Response.OutputStream.Flush()
    }

    $Response.Close()
}

function Send-Completion {
    param($Response, $Answer, [bool]$StreamRequested)

    if ($StreamRequested) {
        Send-SseCompletion $Response $Answer
    }
    else {
        Send-Json $Response $Answer
    }
}
function Get-ImageParts {
    param($Messages)

    $found = @()

    foreach ($message in $Messages) {
        if ($message.content -is [System.Array]) {
            foreach ($part in $message.content) {
                if ($part.type -eq "image_url") {
                    $url = $null

                    if ($part.image_url -is [string]) {
                        $url = $part.image_url
                    }
                    elseif ($part.image_url.url) {
                        $url = $part.image_url.url
                    }

                    if ($url) {
                        $found += $url
                    }
                }
            }
        }
    }

    return $found
}

function Get-UserText {
    param($Messages)

    $pieces = @()

    foreach ($message in $Messages) {
        if ($message.role -ne "user") { continue }

        if ($message.content -is [string]) {
            $pieces += $message.content
        }
        elseif ($message.content -is [System.Array]) {
            foreach ($part in $message.content) {
                if ($part.type -eq "text" -and $part.text) {
                    $pieces += $part.text
                }
            }
        }
    }

    return ($pieces -join "`n")
}

while ($listener.IsListening) {
    $context = $null

    try {
        $context = $listener.GetContext()
        $request = $context.Request
        $response = $context.Response
        $path = $request.Url.AbsolutePath.TrimEnd("/")

        Write-Host "$(Get-Date -Format HH:mm:ss) $($request.HttpMethod) $path"

        # OpenAI-compatible model discovery
        if ($request.HttpMethod -eq "GET" -and $path -eq "/v1/models") {
            $models = @{
                object = "list"
                data = @(
                    @{
                        id = "hermes-multimodal"
                        object = "model"
                        created = [DateTimeOffset]::UtcNow.ToUnixTimeSeconds()
                        owned_by = "local"
                    }
                )
            }

            Send-Json $response $models
            continue
        }

        if ($request.HttpMethod -ne "POST" -or $path -ne "/v1/chat/completions") {
            Send-Json $response @{
                error = @{
                    message = "Not Found"
                    type = "invalid_request_error"
                }
            } 404
            continue
        }

        $reader = [IO.StreamReader]::new($request.InputStream, $request.ContentEncoding)
        $raw = $reader.ReadToEnd()
        $reader.Close()

        $incoming = $raw | ConvertFrom-Json

        $streamRequested = ($incoming.stream -eq $true)


        $toolCount = @($incoming.tools).Count
        Write-Host "  stream=$streamRequested tools=$toolCount"

        $images = @(Get-ImageParts $incoming.messages)

        # --------------------------------------------------------
        # TEXT-ONLY REQUEST:
        # Pass the complete conversation straight to Octo2.
        # --------------------------------------------------------
        if ($images.Count -eq 0) {

            $payload = @{
                model = $ReasoningModel
                messages = $incoming.messages
            }

            if ($null -ne $incoming.temperature) {
                $payload.temperature = $incoming.temperature
            }

            if ($null -ne $incoming.max_tokens) {
                $payload.max_tokens = $incoming.max_tokens
            }

            if ($null -ne $incoming.tools) {
                $payload.tools = $incoming.tools
            }

            if ($null -ne $incoming.tool_choice) {
                $payload.tool_choice = $incoming.tool_choice
            }

            $jsonBody = $payload | ConvertTo-Json -Depth 30

            $answer = Invoke-RestMethod `
                -Uri $ReasoningURL `
                -Method Post `
                -ContentType "application/json" `
                -Body $jsonBody `
                -TimeoutSec 300

            Send-Completion $response $answer $streamRequested
            continue
        }

        # --------------------------------------------------------
        # IMAGE REQUEST:
        # Vision model sees image(s), then 80B reasons over result.
        # --------------------------------------------------------

        $userQuestion = Get-UserText $incoming.messages

        if ([string]::IsNullOrWhiteSpace($userQuestion)) {
            $userQuestion = "Describe and analyze the supplied image."
        }

        $visionContent = @(
            @{
                type = "text"
                text = @"
Analyze the supplied image carefully.

Describe only what is actually visible.
Transcribe visible text when possible.
Identify UI elements, errors, commands, windows, objects, and spatial relationships.
Do not invent details.

The user's question is:
$userQuestion
"@
            }
        )

        foreach ($img in $images) {
            $visionContent += @{
                type = "image_url"
                image_url = @{
                    url = $img
                }
            }
        }

        $visionPayload = @{
            model = $VisionModel
            messages = @(
                @{
                    role = "user"
                    content = $visionContent
                }
            )
            max_tokens = 1000
            temperature = 0.1
        } | ConvertTo-Json -Depth 30

        Write-Host "  -> Vision ($VisionModel)" -ForegroundColor Cyan

        $vision = Invoke-RestMethod `
            -Uri $VisionURL `
            -Method Post `
            -ContentType "application/json" `
            -Body $visionPayload `
            -TimeoutSec 180

        $description = $vision.choices[0].message.content

        Write-Host "  VISION RETURNED:" -ForegroundColor Yellow
        Write-Host "  >>> $description <<<" -ForegroundColor Yellow

        Write-Host "  -> Reasoning (80B)" -ForegroundColor Cyan

        # Preserve textual conversation history, but replace multimodal
        # content with text so the text-only 80B can consume it.
        $reasoningMessages = @()

        foreach ($message in $incoming.messages) {

            if ($message.content -is [string]) {
                $reasoningMessages += @{
                    role = $message.role
                    content = $message.content
                }
            }
            elseif ($message.content -is [System.Array]) {
                $textParts = @()

                foreach ($part in $message.content) {
                    if ($part.type -eq "text" -and $part.text) {
                        $textParts += $part.text
                    }
                }

                if ($textParts.Count -gt 0) {
                    $reasoningMessages += @{
                        role = $message.role
                        content = ($textParts -join "`n")
                    }
                }
            }
        }

        $visionObservation = @{
            role = "system"
            content = @"
An upstream vision model has already read the image.

The exact text extracted from the image is:

$description

Use the extracted text above to answer the user's request.
"@
        }

        # Keep the final user request as the final message.
        # Insert the vision observation immediately before it.
        if (
            $reasoningMessages.Count -gt 0 -and
            $reasoningMessages[-1].role -eq "user"
        ) {
            $finalUserMessage = $reasoningMessages[-1]

            if ($reasoningMessages.Count -gt 1) {
                $reasoningMessages = @(
                    $reasoningMessages[0..($reasoningMessages.Count - 2)]
                )
            }
            else {
                $reasoningMessages = @()
            }

            $reasoningMessages += $visionObservation
            $reasoningMessages += $finalUserMessage
        }
        else {
            $reasoningMessages += $visionObservation
        }

        $reasoningPayload = @{
            model = $ReasoningModel
            messages = $reasoningMessages
        }

        if ($null -ne $incoming.temperature) {
            $reasoningPayload.temperature = $incoming.temperature
        }

        if ($null -ne $incoming.max_tokens) {
            $reasoningPayload.max_tokens = $incoming.max_tokens
        }
        else {
            $reasoningPayload.max_tokens = 2048
        }

        $reasoningJson = $reasoningPayload | ConvertTo-Json -Depth 30

        Write-Host "  === EXACT 80B PAYLOAD ===" -ForegroundColor Magenta
        Write-Host $reasoningJson -ForegroundColor Magenta
        Write-Host "  === END 80B PAYLOAD ===" -ForegroundColor Magenta

        $answer = Invoke-RestMethod `
            -Uri $ReasoningURL `
            -Method Post `
            -ContentType "application/json" `
            -Body $reasoningJson `
            -TimeoutSec 300

        # Make returned model name stable for Hermes.
        $answer.model = "hermes-multimodal"

        Send-Completion $response $answer $streamRequested
    }
    catch {
        Write-Host "ERROR: $($_.Exception.Message)" -ForegroundColor Red

        if ($context -and $context.Response) {
            try {
                Send-Json $context.Response @{
                    error = @{
                        message = $_.Exception.Message
                        type = "gateway_error"
                    }
                } 500
            }
            catch {}
        }
    }
}











