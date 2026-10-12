[CmdletBinding()]
param(
    [switch]$Force
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$projectRoot = Split-Path -Parent $PSScriptRoot
$configuredHooksPath = ".githooks"

& git -C $projectRoot rev-parse --git-dir *> $null
if ($LASTEXITCODE -ne 0) {
    throw "The project directory is not a Git worktree: $projectRoot"
}

$currentHooksPath = & git -C $projectRoot config --local --get core.hooksPath
$readExitCode = $LASTEXITCODE
if ($readExitCode -ne 0 -and $readExitCode -ne 1) {
    throw "Could not read the local core.hooksPath setting (exit $readExitCode)."
}
$currentHooksPath = if ($null -eq $currentHooksPath) {
    ""
} else {
    ([string]$currentHooksPath).Trim()
}

if (
    $currentHooksPath -and
    $currentHooksPath -ne $configuredHooksPath -and
    -not $Force
) {
    throw (
        "core.hooksPath is already set to '{0}'. Re-run with -Force to replace it." -f `
            $currentHooksPath
    )
}

& git -C $projectRoot config --local core.hooksPath $configuredHooksPath
if ($LASTEXITCODE -ne 0) {
    throw "Could not configure core.hooksPath."
}

$installedHooksPath = & git -C $projectRoot config --local --get core.hooksPath
$verifyExitCode = $LASTEXITCODE
if ($verifyExitCode -ne 0) {
    throw "Could not verify core.hooksPath (exit $verifyExitCode)."
}
$installedHooksPath = ([string]$installedHooksPath).Trim()
if ($installedHooksPath -ne $configuredHooksPath) {
    throw "core.hooksPath verification failed."
}

Write-Host "Git hooks enabled from $configuredHooksPath"
