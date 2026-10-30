import re
p = r'C:\Users\asker\Projelerim\UniSense\frontend\src\pages\Search.tsx'
s = open(p, encoding='utf-8').read()
for m in re.finditer(r'function \w+\([^)]*\)\s*\{', s):
    if 'level' in m.group(0) or 'config' in s[m.start():m.start()+200]:
        print(m.start(), m.group(0))