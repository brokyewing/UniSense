<#
.SYNOPSIS
  opencode'u Kariyer yol haritasindaki acik gorevler bitene kadar sirayla kosturur.

.DESCRIPTION
  opencode'da "tum todo'lari sirayla yap" diye tek bir komut YOK. Bu betik
  eksigi disaridan kapatir:

    1. .beyin/PLAN_KARIYER_YOL_HARITASI.md icindeki acik "- [ ]" sayisini okur
    2. Acik gorev varsa `opencode run -c` ile bir tur kosturur
    3. Tur bitince sayimi tekrar okur; azalmadiysa TIKANDI sayip durur
    4. Acik gorev kalmayinca durur

  Tikanma tespiti onemli: ayni gorevde sonsuz donmesin diye ust uste 2 tur
  ilerleme olmazsa betik kendini durdurur.

.PARAMETER MaxTur
  En fazla kac tur kosulacak (varsayilan 20). Guvenlik freni.

.PARAMETER Auto
  opencode'a --auto gecer (izinleri otomatik onaylar). Gozetimsiz kosu icin
  gerekli AMA riskli: opencode onay sormadan dosya yazar, komut calistirir,
  commit/push eder. Once -Auto OLMADAN birkac tur izleyip davranisini gor.

.PARAMETER Model
  opencode'a -m ile gecilecek model (ornek: anthropic/claude-sonnet-4-5).
  Bos birakilirsa opencode kendi varsayilanini kullanir.

.EXAMPLE
  # Once gozetimli dene (her izni sen onayla)
  .\scripts\opencode-loop.ps1 -MaxTur 2

.EXAMPLE
  # Gozetimsiz, en fazla 10 tur
  .\scripts\opencode-loop.ps1 -MaxTur 10 -Auto

.NOTES
  DIKKAT: Ayni repoda baska bir ajan (ornegin Claude Code) calisiyorsa
  ikisi ayni dosyaya yazip birbirinin isini ezebilir. Bu betigi calistirmadan
  once digerinin isini bitirmesini bekle.
#>
[CmdletBinding()]
param(
    [int]$MaxTur = 20,
    [switch]$Auto,
    [string]$Model = ""
)

$ErrorActionPreference = "Stop"

# Repo koku: bu betik scripts/ altinda duruyor
$RepoKok = Split-Path -Parent $PSScriptRoot
$PlanYolu = Join-Path $RepoKok ".beyin\PLAN_KARIYER_YOL_HARITASI.md"

if (-not (Test-Path $PlanYolu)) {
    Write-Error "Plan dosyasi bulunamadi: $PlanYolu"
}

function Get-AcikGorevSayisi {
    # Satir basi bosluk + "- [ ]" kalibi
    return @(Select-String -Path $PlanYolu -Pattern '^\s*- \[ \]').Count
}

# opencode'a her turda verilecek yonerge. Yol haritasinin §0 protokolune isaret
# eder; ayrintiyi tekrarlamaz ki plan tek dogruluk kaynagi kalsin.
$Yonerge = @'
.beyin/PLAN_KARIYER_YOL_HARITASI.md dosyasini ac ve §0 "Calisma protokolu"ne uy.

Bu turda YALNIZCA en ustteki acik "- [ ]" gorevi al ve BITIR:
- Gorevin "Bitti:" kriterini karsila.
- Tikanirsan durma: §3 erisim karar agacini uygula, hala olmuyorsa gorevi [!]
  isaretle, tek satir sebep yaz ve o gorevi kapat.
- Bitirince: ruff temiz + pytest yesil oldugunu DOGRULA, plandaki kutuyu [x]
  yap, .beyin/GOREVLER.md ve GUNLUK.md guncelle, commit et.
- Yarim birakma. Tek gorev bitince dur.
'@

Write-Host ""
Write-Host "opencode dongusu — Kariyer yol haritasi" -ForegroundColor Cyan
Write-Host "  plan     : $PlanYolu"
Write-Host "  max tur  : $MaxTur"
Write-Host "  auto     : $(if ($Auto) { 'ACIK (izinler otomatik onaylanir)' } else { 'kapali (her izni sen onaylarsin)' })"
Write-Host ""

$onceki = Get-AcikGorevSayisi
Write-Host "Baslangicta acik gorev: $onceki" -ForegroundColor Yellow

if ($onceki -eq 0) {
    Write-Host "Acik gorev yok — yapacak bir sey kalmamis." -ForegroundColor Green
    exit 0
}

$ilerlemesizTur = 0

for ($tur = 1; $tur -le $MaxTur; $tur++) {
    Write-Host ""
    Write-Host ("=" * 60)
    Write-Host "TUR $tur / $MaxTur   (acik gorev: $onceki)" -ForegroundColor Cyan
    Write-Host ("=" * 60)

    $argumanlar = @("run", "-c")
    if ($Auto)   { $argumanlar += "--auto" }
    if ($Model)  { $argumanlar += @("-m", $Model) }
    $argumanlar += $Yonerge

    Push-Location $RepoKok
    try {
        & opencode @argumanlar
        $cikis = $LASTEXITCODE
    } finally {
        Pop-Location
    }

    if ($cikis -ne 0) {
        Write-Host "opencode sifirdan farkli kodla cikti ($cikis) — donguyu durduruyorum." -ForegroundColor Red
        break
    }

    $simdiki = Get-AcikGorevSayisi
    $fark = $onceki - $simdiki
    Write-Host ""
    Write-Host "Tur $tur sonucu: acik gorev $onceki -> $simdiki (kapanan: $fark)" -ForegroundColor Yellow

    if ($simdiki -eq 0) {
        Write-Host ""
        Write-Host "TUM GOREVLER BITTI." -ForegroundColor Green
        break
    }

    if ($fark -le 0) {
        $ilerlemesizTur++
        Write-Host "UYARI: bu turda hicbir gorev kapanmadi ($ilerlemesizTur. kez)." -ForegroundColor Red
        if ($ilerlemesizTur -ge 2) {
            Write-Host ""
            Write-Host "Ust uste 2 tur ilerleme yok — tikandi sayiyorum, duruyorum." -ForegroundColor Red
            Write-Host "Elle bak: opencode son turda ne yapti, gorev gercekten tikali mi?" -ForegroundColor Red
            break
        }
    } else {
        $ilerlemesizTur = 0
    }

    $onceki = $simdiki
}

Write-Host ""
Write-Host "Dongu bitti. Kalan acik gorev: $(Get-AcikGorevSayisi)" -ForegroundColor Cyan
Write-Host "Durum icin: .beyin/DEVIR.md ve .beyin/GOREVLER.md"
