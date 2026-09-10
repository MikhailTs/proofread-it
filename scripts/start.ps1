[CmdletBinding()]
param(
    [string]$AutomationPath = "",
    [string]$AutoHotkeyPath = "",
    [switch]$PrintAutoHotkeyPath
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot

function Resolve-AutoHotkeyExecutable {
    param([string]$RequestedPath)

    if (-not [string]::IsNullOrWhiteSpace($RequestedPath)) {
        if (Test-Path -LiteralPath $RequestedPath -PathType Leaf) {
            return [System.IO.Path]::GetFullPath($RequestedPath)
        }
        $requestedCommand = Get-Command $RequestedPath -CommandType Application -ErrorAction SilentlyContinue
        if ($null -ne $requestedCommand) {
            return $requestedCommand.Source
        }
        throw "The requested AutoHotkey executable was not found: '$RequestedPath'"
    }

    $candidates = @()
    if (-not [string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
        $candidates += Join-Path $env:LOCALAPPDATA "Programs\AutoHotkey\v2\AutoHotkey64.exe"
        $candidates += Join-Path $env:LOCALAPPDATA "Programs\AutoHotkey\v2\AutoHotkey32.exe"
    }
    if (-not [string]::IsNullOrWhiteSpace($env:ProgramFiles)) {
        $candidates += Join-Path $env:ProgramFiles "AutoHotkey\v2\AutoHotkey64.exe"
        $candidates += Join-Path $env:ProgramFiles "AutoHotkey\v2\AutoHotkey32.exe"
    }
    if (-not [string]::IsNullOrWhiteSpace(${env:ProgramFiles(x86)})) {
        $candidates += Join-Path ${env:ProgramFiles(x86)} "AutoHotkey\v2\AutoHotkey32.exe"
    }

    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return [System.IO.Path]::GetFullPath($candidate)
        }
    }
    foreach ($commandName in @("AutoHotkey64.exe", "AutoHotkey32.exe", "AutoHotkey.exe")) {
        $command = Get-Command $commandName -CommandType Application -ErrorAction SilentlyContinue
        if ($null -ne $command) {
            return $command.Source
        }
    }

    throw (
        "AutoHotkey v2 was not found. Install it or pass " +
        "-AutoHotkeyPath with the full path to AutoHotkey64.exe."
    )
}

$resolvedAutoHotkeyPath = Resolve-AutoHotkeyExecutable $AutoHotkeyPath
if ($PrintAutoHotkeyPath) {
    Write-Output $resolvedAutoHotkeyPath
    exit 0
}

if ([string]::IsNullOrWhiteSpace($AutomationPath)) {
    $AutomationPath = Join-Path $projectRoot "automation\windows\proofread-it.ahk"
}

Start-Process `
    -FilePath $resolvedAutoHotkeyPath `
    -ArgumentList @([System.IO.Path]::GetFullPath($AutomationPath)) `
    -WorkingDirectory $projectRoot `
    -WindowStyle Hidden
