import re
p = r'C:\Users\asker\Projelerim\UniSense\frontend\src\pages\Recommend.tsx'
s = open(p, encoding='utf-8').read()
for m in re.finditer(r'\(\{\s*[^}]*\}\)', s):
    print(m.start(), m.group(0)[:60])