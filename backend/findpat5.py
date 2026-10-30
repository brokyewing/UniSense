import re
p = r'C:\Users\asker\Projelerim\UniSense\frontend\src\pages\Profile.tsx'
s = open(p, encoding='utf-8').read()
for m in re.finditer(r'function \w+\(name\)', s):
    print(m.group(0))
for m in re.finditer(r'\(name\) =>', s):
    print('ARROW:', m.group(0))