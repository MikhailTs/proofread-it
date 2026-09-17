[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$SettingsPath,
    [string]$Profile,
    [Parameter(Mandatory = $true)]
    [ValidateSet("show_full", "copy_final")]
    [string]$Action
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$resolvedSettingsPath = [System.IO.Path]::GetFullPath($SettingsPath)

try {
    $settings = Get-Content -Raw -LiteralPath $resolvedSettingsPath | ConvertFrom-Json
} catch {
    throw "Cannot load application settings from '$resolvedSettingsPath': $($_.Exception.Message)"
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
$backendExitCode = 1
$backendArguments = @("--settings", $resolvedSettingsPath)
if ($PSBoundParameters.ContainsKey("Profile")) {
    $backendArguments += @("--profile", $Profile)
}
$backendArguments += @("--action", $Action)
try {
    [Environment]::SetEnvironmentVariable($apiKeyEnv, $apiKey, "Process")
    & uv run --project $projectRoot --no-sync proofread-it @backendArguments
    $backendExitCode = $LASTEXITCODE
} finally {
    [Environment]::SetEnvironmentVariable($apiKeyEnv, $previousApiKey, "Process")
    Remove-Variable apiKey -ErrorAction SilentlyContinue
}

exit $backendExitCode
