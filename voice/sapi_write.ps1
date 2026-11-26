param(
    [Parameter(Mandatory=$true)][string]$InFile,
    [Parameter(Mandatory=$true)][string]$OutFile,
    [string]$VoiceName = "",
    [int]$Rate = 0
)

$text = Get-Content -LiteralPath $InFile -Raw -Encoding UTF8
if (-not $text) { throw "Matn fayli bo'sh: $InFile" }

$voice = New-Object -ComObject SAPI.SpVoice
if ($VoiceName) {
    foreach ($token in $voice.GetVoices()) {
        if ($token.GetDescription() -eq $VoiceName) {
            $voice.Voice = $token
            break
        }
    }
}
$voice.Rate = $Rate

$stream = New-Object -ComObject SAPI.SpFileStream
$stream.Open($OutFile, 3, $false)
$voice.AudioOutputStream = $stream
$voice.Speak($text, 0)
$stream.Close()

[System.Runtime.InteropServices.Marshal]::ReleaseComObject($stream) | Out-Null
[System.Runtime.InteropServices.Marshal]::ReleaseComObject($voice) | Out-Null
Write-Output "OK"
