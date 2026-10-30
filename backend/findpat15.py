import re
p = r'C:\Users\asker\Projelerim\UniSense\frontend\src\pages\Recommend.tsx'
s = open(p, encoding='utf-8').read()
for m in re.finditer(r'function \w+\(\{[^}]*\}\)', s):
    print(m.group(0))