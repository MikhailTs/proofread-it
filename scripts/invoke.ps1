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
$utf8Encoding = New-Object System.Text.UTF8Encoding($false)
[Console]::OutputEncoding = $utf8Encoding
$OutputEncoding = $utf8Encoding
$projectRoot = Split-Path -Parent $PSScriptRoot
$resolvedSettingsPath = [System.IO.Path]::GetFullPath($SettingsPath)
$hasRequestedProfile = $PSBoundParameters.ContainsKey("Profile")

function Write-InvocationFailure {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Reason,
        [bool]$HasProfile,
        [string]$ProfileName
    )

    $arguments = @(
        "run", "--project", $projectRoot, "--no-sync", "python", "-m",
        "proofread_it.invocation_failure", "--settings", $resolvedSettingsPath,
        "--action", $Action, "--reason", $Reason
    )
    if ($HasProfile) {
        $arguments += @("--profile", $ProfileName)
    }
    try {
        & uv @arguments 2>$null | Out-Null
    } catch {
        # Preserve the original credential or settings error if logging is unavailable.
    }
}

try {
    $settings = Get-Content -Raw -LiteralPath $resolvedSettingsPath | ConvertFrom-Json
} catch {
    Write-InvocationFailure -Reason "configuration_invalid" -HasProfile $hasRequestedProfile -ProfileName $Profile
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
    Write-InvocationFailure -Reason "configuration_invalid" -HasProfile $hasRequestedProfile -ProfileName $Profile
    throw "settings.api.api_key_env must be a valid environment variable name"
}

if ([string]::IsNullOrWhiteSpace($env:USERPROFILE)) {
    Write-InvocationFailure -Reason "credential_unavailable" -HasProfile $hasRequestedProfile -ProfileName $Profile
    throw "USERPROFILE is unavailable; cannot locate the development API credential"
}
$secretPath = Join-Path $env:USERPROFILE ".secrets\openai_token.txt"
try {
    $apiKey = [System.IO.File]::ReadAllText($secretPath).Trim()
} catch {
    Write-InvocationFailure -Reason "credential_unavailable" -HasProfile $hasRequestedProfile -ProfileName $Profile
    throw "Cannot read the development API credential file '$secretPath'"
}
if ([string]::IsNullOrWhiteSpace($apiKey)) {
    Write-InvocationFailure -Reason "credential_empty" -HasProfile $hasRequestedProfile -ProfileName $Profile
    throw "The development API credential file '$secretPath' is empty"
}

$previousApiKey = [Environment]::GetEnvironmentVariable($apiKeyEnv, "Process")
$pythonIoEncodingEnv = "PYTHONIOENCODING"
$previousPythonIoEncoding = [Environment]::GetEnvironmentVariable($pythonIoEncodingEnv, "Process")
$backendExitCode = 1
$backendArguments = @("--settings", $resolvedSettingsPath)
if ($PSBoundParameters.ContainsKey("Profile")) {
    $backendArguments += @("--profile", $Profile)
}
$backendArguments += @("--action", $Action)
try {
    [Environment]::SetEnvironmentVariable($apiKeyEnv, $apiKey, "Process")
    [Environment]::SetEnvironmentVariable($pythonIoEncodingEnv, "utf-8", "Process")
    & uv run --project $projectRoot --no-sync proofread-it @backendArguments
    $backendExitCode = $LASTEXITCODE
} finally {
    [Environment]::SetEnvironmentVariable($apiKeyEnv, $previousApiKey, "Process")
    [Environment]::SetEnvironmentVariable(
        $pythonIoEncodingEnv,
        $previousPythonIoEncoding,
        "Process"
    )
    Remove-Variable apiKey -ErrorAction SilentlyContinue
}

exit $backendExitCode
