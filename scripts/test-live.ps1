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
$resolvedSettingsPath = [System.IO.Path]::GetFullPath($SettingsPath)

$liveSettingsEnv = "PROOFREAD_IT_LIVE_SETTINGS_PATH"
$previousSettingsPath = [Environment]::GetEnvironmentVariable($liveSettingsEnv, "Process")
if ([string]::IsNullOrWhiteSpace($TestPath)) {
    $liveTestsPath = Join-Path $projectRoot "tests\live"
} else {
    $liveTestsPath = [System.IO.Path]::GetFullPath($TestPath)
}

try {
    [Environment]::SetEnvironmentVariable(
        $liveSettingsEnv,
        $resolvedSettingsPath,
        "Process"
    )
    & uv run --project $projectRoot --no-sync pytest -m live $liveTestsPath
    $testExitCode = $LASTEXITCODE
} finally {
    [Environment]::SetEnvironmentVariable($liveSettingsEnv, $previousSettingsPath, "Process")
}

exit $testExitCode
