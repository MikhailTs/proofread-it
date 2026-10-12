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

$pythonIoEncodingEnv = "PYTHONIOENCODING"
$previousPythonIoEncoding = [Environment]::GetEnvironmentVariable($pythonIoEncodingEnv, "Process")
$backendExitCode = 1
$backendArguments = @("--settings", $resolvedSettingsPath)
if ($PSBoundParameters.ContainsKey("Profile")) {
    $backendArguments += @("--profile", $Profile)
}
$backendArguments += @("--action", $Action)

try {
    [Environment]::SetEnvironmentVariable($pythonIoEncodingEnv, "utf-8", "Process")
    & uv run --project $projectRoot --no-sync proofread-it @backendArguments
    $backendExitCode = $LASTEXITCODE
} finally {
    [Environment]::SetEnvironmentVariable(
        $pythonIoEncodingEnv,
        $previousPythonIoEncoding,
        "Process"
    )
}

exit $backendExitCode
