import re
p = r'C:\Users\asker\Projelerim\UniSense\frontend\src\pages\Profile.tsx'
s = open(p, encoding='utf-8').read()
for m in re.finditer(r'catch \((e|err)\)', s):
    print(m.start(), repr(s[max(0,m.start()-5):m.start()+15]))