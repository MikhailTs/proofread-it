[CmdletBinding()]
param(
    [string]$SettingsPath = "",
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

if ([string]::IsNullOrWhiteSpace($SettingsPath)) {
    $SettingsPath = Join-Path $projectRoot "config\settings.json"
}
if ([string]::IsNullOrWhiteSpace($AutomationPath)) {
    $AutomationPath = Join-Path $projectRoot "automation\windows\proofread-it.ahk"
}

try {
    $settings = Get-Content -Raw -LiteralPath $SettingsPath | ConvertFrom-Json
} catch {
    throw "Cannot load application settings from '$SettingsPath': $($_.Exception.Message)"
}

$apiKeyEnv = $settings.api.api_key_env
if (
    -not ($apiKeyEnv -is [string]) -or
    [string]::IsNullOrWhiteSpace($apiKeyEnv) -or
    $apiKeyEnv.Trim() -ne $apiKeyEnv -or
    $apiKeyEnv.Contains("=") -or
    $apiKeyEnv.Contains([char]0)
) {
    throw "settings.api.api_key_env must be a valid environment variable name"
}

if ([string]::IsNullOrWhiteSpace($env:USERPROFILE)) {
    throw "USERPROFILE is unavailable; cannot locate the development API credential"
}
$secretPath = Join-Path $env:USERPROFILE ".secrets\openai_token.txt"
try {
    $apiKey = [System.IO.File]::ReadAllText($secretPath).Trim()
} catch {
    throw "Cannot read the development API credential file '$secretPath'"
}
if ([string]::IsNullOrWhiteSpace($apiKey)) {
    throw "The development API credential file '$secretPath' is empty"
}

$previousApiKey = [Environment]::GetEnvironmentVariable($apiKeyEnv, "Process")
try {
    [Environment]::SetEnvironmentVariable($apiKeyEnv, $apiKey, "Process")
    Start-Process `
        -FilePath $resolvedAutoHotkeyPath `
        -ArgumentList @([System.IO.Path]::GetFullPath($AutomationPath)) `
        -WorkingDirectory $projectRoot `
        -WindowStyle Hidden
} finally {
    [Environment]::SetEnvironmentVariable($apiKeyEnv, $previousApiKey, "Process")
    Remove-Variable apiKey -ErrorAction SilentlyContinue
}
