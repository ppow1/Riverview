[CmdletBinding()]
param(
    [ValidateRange(1, 15)]
    [int]$DurationSeconds = 8
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$engine = New-Object System.Speech.Recognition.SpeechRecognitionEngine
$engine.LoadGrammar((New-Object System.Speech.Recognition.DictationGrammar))
$engine.SetInputToDefaultAudioDevice()
$result = $engine.Recognize([TimeSpan]::FromSeconds($DurationSeconds))
$engine.Dispose()
$text = if ($null -eq $result) { '' } else { $result.Text.Trim() }
if ([string]::IsNullOrWhiteSpace($text)) {
    throw 'RIV-UI-0015: local microphone produced no bounded transcription.'
}
[pscustomobject]@{
    provider_id = 'windows:System.Speech'
    text = $text
    retention = 'discard-after-transcription'
    duration_seconds = $DurationSeconds
} | ConvertTo-Json -Compress
