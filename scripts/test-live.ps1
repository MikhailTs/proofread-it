[CmdletBinding()]
param(
    [string]$SettingsPath = "",
    [string]$TestPath = ""
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($SettingsPath)) {
    $SettingsPath = Join-Path $projectRoot "config\settings.json"
}

try {
    $settings = Get-Content -Raw -LiteralPath $SettingsPath | ConvertFrom-Json
} catch {
    throw "Cannot load live-test settings from '$SettingsPath': $($_.Exception.Message)"
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

$liveSettingsEnv = "PROOFREAD_IT_LIVE_SETTINGS_PATH"
$previousApiKey = [Environment]::GetEnvironmentVariable($apiKeyEnv, "Process")
$previousSettingsPath = [Environment]::GetEnvironmentVariable($liveSettingsEnv, "Process")
if ([string]::IsNullOrWhiteSpace($TestPath)) {
    $liveTestsPath = Join-Path $projectRoot "tests\live"
} else {
    $liveTestsPath = [System.IO.Path]::GetFullPath($TestPath)
}

try {
    [Environment]::SetEnvironmentVariable($apiKeyEnv, $apiKey, "Process")
    [Environment]::SetEnvironmentVariable(
        $liveSettingsEnv,
        [System.IO.Path]::GetFullPath($SettingsPath),
        "Process"
    )
    & uv run --project $projectRoot --no-sync pytest -m live $liveTestsPath
    $testExitCode = $LASTEXITCODE
} finally {
    [Environment]::SetEnvironmentVariable($apiKeyEnv, $previousApiKey, "Process")
    [Environment]::SetEnvironmentVariable($liveSettingsEnv, $previousSettingsPath, "Process")
    Remove-Variable apiKey -ErrorAction SilentlyContinue
}

exit $testExitCode
