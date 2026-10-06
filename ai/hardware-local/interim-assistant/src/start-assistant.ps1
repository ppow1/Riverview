$Port = 8765
$Server = 'A:\AI\Assistant\assistant.py'

$Existing = Get-NetTCPConnection `
    -LocalPort $Port `
    -State Listen `
    -ErrorAction SilentlyContinue

if (-not $Existing) {

    Start-Process `
        -WindowStyle Hidden `
        -FilePath 'python' `
        -ArgumentList "`"$Server`""
}
