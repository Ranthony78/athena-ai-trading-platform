# Starts the Athena backend, frontend and Celery worker/beat as split panes of ONE
# Windows Terminal window. Anything already running is left alone.
$root = Split-Path -Parent $MyInvocation.MyCommand.Path

function Test-Port($port) {
    [bool](Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
}
function Test-Celery($role) {
    [bool](Get-CimInstance Win32_Process | Where-Object {
        $_.Name -like 'python*' -and $_.CommandLine -match 'celery' -and $_.CommandLine -match " $role"
    })
}

$panes = @()
if (-not (Test-Port 8000)) { $panes += @{ Title = 'Backend';       Dir = "$root\backend";  Cmd = 'python manage.py runserver' } } else { Write-Host 'Backend already running - skipped.' }
if (-not (Test-Port 3000)) { $panes += @{ Title = 'Frontend';      Dir = "$root\frontend"; Cmd = 'npm run dev' } } else { Write-Host 'Frontend already running - skipped.' }
# Windows cannot run the scheduler inside the worker (-B), so they are two panes.
if (-not (Test-Celery 'worker')) { $panes += @{ Title = 'Celery worker'; Dir = "$root\backend"; Cmd = 'python -m celery -A config worker -l info -P solo' } } else { Write-Host 'Celery worker already running - skipped.' }
if (-not (Test-Celery 'beat'))   { $panes += @{ Title = 'Celery beat';   Dir = "$root\backend"; Cmd = 'python -m celery -A config beat -l info' } } else { Write-Host 'Celery beat already running - skipped.' }

if ($panes.Count -eq 0) { Write-Host 'Everything is already running.'; Start-Sleep 3; exit }

$wtArgs = @()
for ($i = 0; $i -lt $panes.Count; $i++) {
    $p = $panes[$i]
    # first pane opens the window; each next one splits the focused pane
    $head = if ($i -eq 0) { "new-tab" } else { "; split-pane" }
    $wtArgs += "$head --title `"$($p.Title)`" -d `"$($p.Dir)`" cmd /k $($p.Cmd)"
}
Start-Process wt -ArgumentList (@('-w', 'new') + ($wtArgs -join ' '))
Write-Host 'Started in one Windows Terminal window. Open http://localhost:3000 and reconnect Zerodha before 09:15.'
Start-Sleep 4
