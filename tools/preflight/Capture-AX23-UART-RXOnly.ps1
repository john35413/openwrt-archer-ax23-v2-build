<#
AX23 V2 receive-only serial logging, Windows PowerShell 5.1+
READ-ONLY: never invokes SerialPort.Write or sends router commands.
MANDATORY: confirm verified 1.8 V-compatible adapter, GND and router TX first.
Adapter TX, VCC, RTS and CTS MUST NOT be connected to the router.
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory=$true)]
    [ValidatePattern('^COM[0-9]+$')]
    [string]$Port,
    [switch]$ElectricalChecksConfirmed,
    [string]$OutputDirectory = "$env:USERPROFILE\Documents\AX23-UART-Logs"
)

$ErrorActionPreference = 'Stop'
if (-not $ElectricalChecksConfirmed) {
    Write-Error 'STOP: First verify router GND and TX, idle/signal level, and 1.8 V-compatible adapter input. Connect GND + router TX -> adapter RX ONLY. Rerun with -ElectricalChecksConfirmed.'
    exit 2
}

$available = [System.IO.Ports.SerialPort]::GetPortNames()
if ($Port -notin $available) {
    Write-Error "Port $Port is not available. Available ports: $($available -join ', ')"
    exit 3
}

New-Item -Path $OutputDirectory -ItemType Directory -Force | Out-Null
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$logFile = Join-Path $OutputDirectory "AX23_stock_UART_RXonly_${Port}_${stamp}.bin"

$serial = [System.IO.Ports.SerialPort]::new(
    $Port, 115200, [System.IO.Ports.Parity]::None,
    8, [System.IO.Ports.StopBits]::One
)
$serial.Handshake = [System.IO.Ports.Handshake]::None
$serial.DtrEnable = $false
$serial.RtsEnable = $false
$serial.ReadTimeout = 200
$serial.WriteTimeout = 200

$stream = $null
try {
    $stream = [System.IO.File]::Open($logFile, [System.IO.FileMode]::CreateNew, [System.IO.FileAccess]::Write, [System.IO.FileShare]::Read)
    $serial.Open()
    Write-Host "Receive-only stock UART capture on $Port at 115200 8N1."
    Write-Host "Saving raw bytes to $logFile"
    Write-Host 'NO commands are transmitted. Press Ctrl+C to end.'
    $buffer = New-Object byte[] 4096
    while ($true) {
        $ready = $serial.BytesToRead
        if ($ready -gt 0) {
            $n = $serial.Read($buffer, 0, [Math]::Min($ready, $buffer.Length))
            if ($n -gt 0) {
                $stream.Write($buffer, 0, $n)
                [Console]::Write([System.Text.Encoding]::ASCII.GetString($buffer, 0, $n))
            }
        } else {
            Start-Sleep -Milliseconds 30
        }
    }
} finally {
    if ($serial.IsOpen) { $serial.Close() }
    if ($null -ne $stream) { $stream.Dispose() }
    $serial.Dispose()
    Write-Host "`nCapture closed: $logFile"
    Write-Host 'Keep the raw log private; it may contain MAC addresses, serial numbers or other identifiers.'
}
