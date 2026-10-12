[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [ValidateSet("Set", "Remove")]
    [string]$Action,
    [string]$SettingsPath = ""
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($SettingsPath)) {
    $SettingsPath = Join-Path $projectRoot "config\settings.json"
}
$credentialAction = $Action.ToLowerInvariant()

& uv run --project $projectRoot --no-sync python -m proofread_it.credential_cli `
    --settings ([System.IO.Path]::GetFullPath($SettingsPath)) `
    $credentialAction
exit $LASTEXITCODE
