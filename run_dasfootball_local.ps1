param(
    [string]$Python = "python",
    [string]$Git = "git"
)
$ErrorActionPreference = "Stop"
if ($Git -eq "git" -and -not (Get-Command git -ErrorAction SilentlyContinue)) {
    $bundledGit = Join-Path $env:USERPROFILE ".cache\codex-runtimes\codex-primary-runtime\dependencies\native\git\cmd\git.exe"
    if (Test-Path -LiteralPath $bundledGit) { $Git = $bundledGit }
}
Set-Location -LiteralPath $PSScriptRoot
$mutex = New-Object System.Threading.Mutex($false, "Local\BuiCong1403-DasFootball")
if (-not $mutex.WaitOne(0)) { exit 0 }
Start-Transcript -Path (Join-Path $env:TEMP "dasfootball-local.log") -Append | Out-Null
function Invoke-Git {
    & $Git @args
    if ($LASTEXITCODE -ne 0) { throw "Git command failed: $args" }
}
try {
    $dirty = & $Git status --porcelain --untracked-files=no
    if ($LASTEXITCODE -ne 0) { throw "Cannot inspect repository" }
    if ($dirty) { throw "Tracked files have local changes. Skipping without overwriting them." }
    Invoke-Git pull --rebase origin main
    $oldMode = $env:RUN_MODE
    $collectionTimer = [System.Diagnostics.Stopwatch]::StartNew()
    try {
        $env:RUN_MODE = "dasfootball_snapshot"
        & $Python -u combined_m3u_collector.py
        if ($LASTEXITCODE -ne 0) { throw "DasFootball collection failed; no playlist published." }
    } finally { $env:RUN_MODE = $oldMode }
    $collectionTimer.Stop()
    Write-Host ("Standalone snapshot collected in {0:N1} seconds. Publishing without merging other sources." -f $collectionTimer.Elapsed.TotalSeconds)
    Invoke-Git add -- dasfootball.m3u
    & $Git diff --cached --quiet
    if ($LASTEXITCODE -eq 0) { exit 0 }
    if ($LASTEXITCODE -ne 1) { throw "Cannot inspect staged snapshot" }
    Invoke-Git commit -m "Refresh DasFootball from local collector"
    for ($attempt = 1; $attempt -le 3; $attempt++) {
        & $Git push origin main
        if ($LASTEXITCODE -eq 0) { exit 0 }
        Invoke-Git pull --rebase origin main
    }
    throw "Could not publish snapshot. Local commit is preserved."
} finally {
    $mutex.ReleaseMutex()
    $mutex.Dispose()
    Stop-Transcript | Out-Null
}
