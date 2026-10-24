$c = gc 'C:\Users\asker\Projelerim\UniSense\frontend\src\pages\TercihList.jsx' -Raw
$c = $c -replace '\)\s*}$', ')}'
[IO.File]::WriteAllText('C:\Users\asker\Projelerim\UniSense\frontend\src\pages\TercihList.jsx', $c)