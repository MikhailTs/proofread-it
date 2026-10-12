[CmdletBinding()]
param(
    [switch]$Fast
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$projectRoot = Split-Path -Parent $PSScriptRoot
$ruffCheck = @{
    Name = "Ruff"
    Command = "uv"
    Arguments = @("run", "--project", $projectRoot, "--no-sync", "ruff", "check", ".")
}
$mypyCheck = @{
    Name = "mypy"
    Command = "uv"
    Arguments = @("run", "--project", $projectRoot, "--no-sync", "mypy", "src")
}

if ($Fast) {
    $suiteName = "Fast checks"
    $checks = @(
        $ruffCheck,
        $mypyCheck,
        @{
            Name = "git diff --cached --check"
            Command = "git"
            Arguments = @("diff", "--cached", "--check")
        }
    )
} else {
    $suiteName = "All checks"
    $checks = @(
        @{
            Name = "pytest"
            Command = "uv"
            Arguments = @(
                "run", "--project", $projectRoot, "--no-sync",
                "pytest", "-q", "-p", "no:cacheprovider"
            )
        },
        $ruffCheck,
        $mypyCheck,
        @{
            Name = "git diff --check"
            Command = "git"
            Arguments = @("diff", "--check")
        }
    )
}

$overallStopwatch = [System.Diagnostics.Stopwatch]::StartNew()
$exitCode = 0

Push-Location $projectRoot
try {
    foreach ($check in $checks) {
        $name = [string]$check.Name
        $command = [string]$check.Command
        $arguments = [string[]]$check.Arguments
        $checkStopwatch = [System.Diagnostics.Stopwatch]::StartNew()

        Write-Host "==> $name"
        & $command @arguments
        $checkExitCode = $LASTEXITCODE
        $checkStopwatch.Stop()

        if ($checkExitCode -ne 0) {
            Write-Host (
                "<== {0} failed in {1:N2}s (exit {2})" -f `
                    $name, $checkStopwatch.Elapsed.TotalSeconds, $checkExitCode
            )
            $exitCode = $checkExitCode
            break
        }

        Write-Host (
            "<== {0} passed in {1:N2}s" -f $name, $checkStopwatch.Elapsed.TotalSeconds
        )
    }
} catch {
    [Console]::Error.WriteLine("Verification aborted: {0}", $_.Exception.Message)
    $exitCode = 1
} finally {
    Pop-Location
    $overallStopwatch.Stop()
}

if ($exitCode -eq 0) {
    Write-Host ("{0} passed in {1:N2}s." -f $suiteName, $overallStopwatch.Elapsed.TotalSeconds)
} else {
    Write-Host ("{0} failed after {1:N2}s." -f $suiteName, $overallStopwatch.Elapsed.TotalSeconds)
}

exit $exitCode
