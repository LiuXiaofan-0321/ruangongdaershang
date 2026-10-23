param([string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot))

$ErrorActionPreference = 'Stop'
$env:GIT_TERMINAL_PROMPT = '0'
$env:GCM_INTERACTIVE = 'Never'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$RepositoryRoot = [IO.Path]::GetFullPath($RepositoryRoot)
$gitCommand = (Get-Command git.exe -ErrorAction Stop).Source
$gitDirectory = Join-Path $RepositoryRoot '.git'
$logPath = Join-Path $gitDirectory 'course-sync.log'
if (-not (Test-Path -LiteralPath $gitDirectory -PathType Container)) { throw 'Not a local course Git repository.' }

function Write-SyncLog([string]$Message) {
    $line = (Get-Date -Format 'yyyy-MM-dd HH:mm:ss') + ' ' + $Message
    Add-Content -LiteralPath $logPath -Value $line -Encoding UTF8
    Write-Output $line
}

function Invoke-CourseGit([string[]]$GitArguments) {
    $savedErrorPreference = $ErrorActionPreference
    try {
        $ErrorActionPreference = 'Continue'
        $result = @(& $gitCommand -C $RepositoryRoot -c 'credential.interactive=never' @GitArguments 2>&1)
        $gitExitCode = $LASTEXITCODE
    } finally { $ErrorActionPreference = $savedErrorPreference }
    if ($gitExitCode -ne 0) { throw (($GitArguments -join ' ') + ': ' + ($result -join "`n")) }
    return $result
}

$hash = [Security.Cryptography.SHA256]::Create()
$rootHash = ([BitConverter]::ToString($hash.ComputeHash([Text.Encoding]::UTF8.GetBytes($RepositoryRoot.ToLowerInvariant())))).Replace('-', '')
$hash.Dispose()
$mutex = [Threading.Mutex]::new($false, ('Local\UniversityCoursesSync-' + $rootHash.Substring(0, 16)))
$ownsMutex = $false
$syncExitCode = 0
try {
    try { $ownsMutex = $mutex.WaitOne(0) } catch [Threading.AbandonedMutexException] { $ownsMutex = $true }
    if (-not $ownsMutex) { exit 0 }
    foreach ($marker in @('MERGE_HEAD', 'rebase-merge', 'rebase-apply', 'CHERRY_PICK_HEAD')) {
        if (Test-Path -LiteralPath (Join-Path $gitDirectory $marker)) { throw 'An existing Git operation needs attention; automatic sync stopped.' }
    }
    $courseNames = @('操作系统', '操作系统lab', '概率论与数理统计', '高端软件开发方法', '计算机网络', '计算机网络lab', '密码与网络安全导论', '密码与网络安全引论', '软件质量分析')
    foreach ($courseName in $courseNames) {
        $coursePath = Join-Path $RepositoryRoot $courseName
        if (-not (Test-Path -LiteralPath $coursePath)) { continue }
        $largeFiles = @(Get-ChildItem -LiteralPath $coursePath -File -Recurse -Force | Where-Object Length -gt 100MB)
        foreach ($file in $largeFiles) {
            $relativePath = $file.FullName.Substring($RepositoryRoot.Length + 1).Replace('\', '/')
            & $gitCommand -C $RepositoryRoot check-ignore --quiet -- $relativePath 2>$null
            if ($LASTEXITCODE -ne 0) { throw ('File exceeds 100 MiB; exclude it in .gitignore before syncing: ' + $relativePath) }
        }
    }
    Invoke-CourseGit -GitArguments @('add', '--all', '--', '.') | Out-Null
    & $gitCommand -C $RepositoryRoot diff --cached --quiet
    $diffExitCode = $LASTEXITCODE
    if ($diffExitCode -eq 1) {
        Invoke-CourseGit -GitArguments @('commit', '-m', ('Sync course materials ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss'))) | Out-Null
        Write-SyncLog 'Local course changes saved.'
    } elseif ($diffExitCode -ne 0) { throw 'Unable to inspect local changes.' }
    Invoke-CourseGit -GitArguments @('fetch', 'origin', 'main') | Out-Null
    $counts = ((Invoke-CourseGit -GitArguments @('rev-list', '--left-right', '--count', 'HEAD...origin/main')) -join '').Trim() -split '\s+'
    if ([int]$counts[1] -gt 0) {
        if ([int]$counts[0] -eq 0) {
            Invoke-CourseGit -GitArguments @('merge', '--ff-only', 'origin/main') | Out-Null
        } else {
            try {
                Invoke-CourseGit -GitArguments @('merge', '--no-edit', 'origin/main') | Out-Null
            } catch {
                if (Test-Path -LiteralPath (Join-Path $gitDirectory 'MERGE_HEAD')) {
                    Invoke-CourseGit -GitArguments @('merge', '--abort') | Out-Null
                }
                throw 'Both computers changed the same files and automatic merge failed. Local changes are committed and preserved; resolve the conflict manually.'
            }
        }
    }
    Invoke-CourseGit -GitArguments @('push', 'origin', 'HEAD:main') | Out-Null
    Write-SyncLog 'Sync completed.'
} catch {
    Write-SyncLog ('ERROR: ' + $_.Exception.Message)
    $syncExitCode = 1
} finally {
    if ($ownsMutex) { $mutex.ReleaseMutex() }
    $mutex.Dispose()
}
exit $syncExitCode
