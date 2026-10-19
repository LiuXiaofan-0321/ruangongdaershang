param([string]$RepositoryRoot = (Split-Path -Parent $PSScriptRoot))
$ErrorActionPreference = 'Stop'
$RepositoryRoot = [IO.Path]::GetFullPath($RepositoryRoot)
$syncScript = Join-Path $RepositoryRoot '.course-sync\Sync-Courses.ps1'
$hiddenLauncher = Join-Path $RepositoryRoot '.course-sync\Run-Hidden.vbs'
if (-not (Test-Path -LiteralPath $syncScript)) { throw 'Course synchronization script is missing.' }
if (-not (Test-Path -LiteralPath $hiddenLauncher)) { throw 'Hidden synchronization launcher is missing.' }
if (-not (Test-Path -LiteralPath (Join-Path $RepositoryRoot '.git') -PathType Container)) { throw 'Clone the course repository before installing auto sync.' }
$taskName = 'UniversityCourses-GitHub-Sync-ruangongdaershang'
$existingTask = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
if ($existingTask -and $existingTask.Actions.Arguments -notlike ('*' + $syncScript + '*')) { throw 'A course sync task already points to another folder. Remove that task before switching folders.' }
$arguments = '//B //NoLogo "' + $hiddenLauncher + '" "' + $syncScript + '"'
$action = New-ScheduledTaskAction -Execute (Join-Path $env:SystemRoot 'System32\wscript.exe') -Argument $arguments -WorkingDirectory $RepositoryRoot
$currentUser = [Security.Principal.WindowsIdentity]::GetCurrent().Name
$onLogon = New-ScheduledTaskTrigger -AtLogOn -User $currentUser
$everyTenMinutes = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(2) -RepetitionInterval (New-TimeSpan -Minutes 10)
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 1) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$principal = New-ScheduledTaskPrincipal -UserId $currentUser -LogonType Interactive -RunLevel Limited
$task = New-ScheduledTask -Action $action -Trigger @($onLogon, $everyTenMinutes) -Settings $settings -Principal $principal -Description 'Synchronize this semester course materials with the user-selected GitHub repository every 10 minutes while signed in.'
Register-ScheduledTask -TaskName $taskName -InputObject $task -Force | Out-Null
Write-Output ('Automatic course sync installed for: ' + $RepositoryRoot)
Write-Output 'Runs at sign-in and every 10 minutes while this user is signed in.'
