import re
p = r'C:\Users\asker\Projelerim\UniSense\frontend\src\lib\planlayici.ts'
s = open(p, encoding='utf-8').read()
# Add any type to empty array inits
s = s.replace('const aday = []', 'const aday: any[] = []')
s = s.replace('const out = []', 'const out: any[] = []')
s = s.replace('const tasks = []', 'const tasks: any[] = []')
s = s.replace('const yeniler = []', 'const yeniler: any[] = []')
# Fix function params
s = s.replace('function havuz(konuData, checked, soruOzet = [])', 'function havuz(konuData: any, checked: any, soruOzet: any = [])')
s = s.replace('function gunFark(aIso, bIso)', 'function gunFark(aIso: any, bIso: any)')
s = s.replace('function haftaSonuMu(iso)', 'function haftaSonuMu(iso: any)')
s = s.replace('function roundRobinDers(list)', 'function roundRobinDers(list: any)')
s = s.replace('function isoGun(d = new Date())', 'function isoGun(d: any = new Date())')
s = s.replace('function haftaGunleri(d = new Date())', 'function haftaGunleri(d: any = new Date())')
s = s.replace('function carryForward(tasks, bugun)', 'function carryForward(tasks: any, bugun: any)')
s = s.replace('function oneriler', 'function oneriler')
open(p, 'w', encoding='utf-8').write(s)
print('done')