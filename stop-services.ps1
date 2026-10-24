param(
    [switch]$WhatIf
)

$ErrorActionPreference = 'Stop'
$projectRoot = [System.IO.Path]::GetFullPath($PSScriptRoot).TrimEnd('\')
$frontendRoot = Join-Path $projectRoot 'frontend'
$processes = @(Get-CimInstance Win32_Process)
$byId = @{}
foreach ($process in $processes) {
    $byId[[int]$process.ProcessId] = $process
}

function Get-ProcessChain {
    param([int]$ProcessId)

    $chain = @()
    $seen = @{}
    $currentId = $ProcessId
    while ($currentId -gt 0 -and -not $seen.ContainsKey($currentId)) {
        $seen[$currentId] = $true
        if (-not $byId.ContainsKey($currentId)) { break }
        $current = $byId[$currentId]
        $chain += $current
        $currentId = [int]$current.ParentProcessId
    }
    return $chain
}

$listeners = @(Get-NetTCPConnection -State Listen -LocalPort 8002, 5174 -ErrorAction SilentlyContinue)
$targets = @{}

foreach ($listener in $listeners) {
    $ownerId = [int]$listener.OwningProcess
    $chain = @(Get-ProcessChain -ProcessId $ownerId)
    $anchor = $null

    foreach ($process in $chain) {
        $commandLine = [string]$process.CommandLine
        $isBackend = $commandLine.IndexOf($projectRoot, [System.StringComparison]::OrdinalIgnoreCase) -ge 0 -and
            $commandLine -match 'uvicorn\s+unisense\.main:app'
        $isFrontend = $commandLine.IndexOf($frontendRoot, [System.StringComparison]::OrdinalIgnoreCase) -ge 0 -and
            $commandLine -match 'vite'

        if (($listener.LocalPort -eq 8002 -and $isBackend) -or
            ($listener.LocalPort -eq 5174 -and $isFrontend)) {
            $anchor = $process
            break
        }
    }

    if ($null -eq $anchor) {
        Write-Host "[ATLANDI] Port $($listener.LocalPort), PID ${ownerId}: UniSense proje yolu dogrulanamadi; surece dokunulmadi." -ForegroundColor Yellow
        continue
    }

    $targets[[int]$anchor.ProcessId] = [pscustomobject]@{
        ProcessId = [int]$anchor.ProcessId
        Label = "port $($listener.LocalPort)"
        Name = [string]$anchor.Name
    }
}

$firebaseProcess = $processes | Where-Object {
    $_.CommandLine -match 'firebase\.js emulators:start' -and
    $_.CommandLine -match '--project\s+unisense-test'
} | Select-Object -First 1
if ($firebaseProcess) {
    $firestoreChild = $processes | Where-Object {
        $_.CommandLine -match '--project_id\s+unisense-test' -and
        $_.CommandLine.IndexOf((Join-Path $projectRoot 'firestore.rules'), [System.StringComparison]::OrdinalIgnoreCase) -ge 0 -and
        (Get-ProcessChain -ProcessId ([int]$_.ProcessId) | Where-Object ProcessId -eq $firebaseProcess.ProcessId)
    } | Select-Object -First 1

    if ($firestoreChild) {
        $targets[[int]$firebaseProcess.ProcessId] = [pscustomobject]@{
            ProcessId = [int]$firebaseProcess.ProcessId
            Label = 'UniSense Firebase Emulator (auth/firestore/UI)'
            Name = [string]$firebaseProcess.Name
        }
    } else {
        Write-Host '[ATLANDI] Firebase CLI --project unisense-test bulundu, ancak UniSense firestore.rules cocugu dogrulanamadi; emulator kapatilmadi.' -ForegroundColor Yellow
    }
}

if ($targets.Count -eq 0) {
    Write-Host '[BILGI] Durdurulacak UniSense servisi bulunamadi.'
    exit 0
}

foreach ($target in $targets.Values) {
    if ($WhatIf) {
        Write-Host "[DENEME] $($target.Label): $($target.Name) PID $($target.ProcessId) durdurulacakti."
        continue
    }

    if ($target.Label -like '*Firebase Emulator*') {
        Write-Host '[UYARI] Emulator kapanirken gecici Auth/Firestore test verileri silinebilir.' -ForegroundColor Yellow
    }
    Write-Host "[DURDUR] $($target.Label): $($target.Name) PID $($target.ProcessId)"
    & taskkill.exe /PID $target.ProcessId /T /F
    if ($LASTEXITCODE -ne 0) {
        Write-Error "PID $($target.ProcessId) kapatilamadi (taskkill exit $LASTEXITCODE)."
        exit $LASTEXITCODE
    }
}

if ($WhatIf) {
    Write-Host '[BILGI] WhatIf: hicbir surec kapatilmadi.'
} else {
    Start-Sleep -Milliseconds 700
    $stillListening = @(Get-NetTCPConnection -State Listen -LocalPort 8002, 5174, 4000, 4400, 4401, 4500, 4501, 8085, 9099, 9150 -ErrorAction SilentlyContinue)
    if ($stillListening.Count -gt 0) {
        Write-Host "[UYARI] Bazi servis portlari hala dinlemede: $((($stillListening | Select-Object -ExpandProperty LocalPort -Unique) -join ', ')). Sahibi UniSense degilse kapatilmadi." -ForegroundColor Yellow
        exit 1
    }
    Write-Host '[OK] Dogrulanan UniSense Backend, Frontend ve Firebase Emulator kapandi.'
}
