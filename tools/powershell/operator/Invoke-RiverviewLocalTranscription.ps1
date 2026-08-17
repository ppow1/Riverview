[CmdletBinding()]
param(
    [ValidateRange(1, 15)]
    [int]$DurationSeconds = 8,
    [ValidateSet('en-US','en-GB')]
    [string]$Culture = 'en-US'
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$engine = New-Object System.Speech.Recognition.SpeechRecognitionEngine([Globalization.CultureInfo]::GetCultureInfo($Culture))
$engine.LoadGrammar((New-Object System.Speech.Recognition.DictationGrammar))
$engine.SetInputToDefaultAudioDevice()
$engine.InitialSilenceTimeout = [TimeSpan]::FromSeconds(2)
$engine.EndSilenceTimeout = [TimeSpan]::FromMilliseconds(900)
$engine.BabbleTimeout = [TimeSpan]::FromSeconds(2)
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
    culture = $Culture
    confidence = if ($null -eq $result) { $null } else { [math]::Round($result.Confidence, 3) }
} | ConvertTo-Json -Compress
