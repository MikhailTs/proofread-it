[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
$checkScript = Join-Path $PSScriptRoot "check.ps1"

& $checkScript -Fast
exit $LASTEXITCODE
