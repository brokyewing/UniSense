import re
p = r'C:\Users\asker\Projelerim\UniSense\frontend\src\pages\Profile.tsx'
s = open(p, encoding='utf-8').read()
for m in re.finditer(r'function \w+\(e\)', s):
    print(m.group(0))
for m in re.finditer(r'async function \w+\(e\)', s):
    print('ASYNC:', m.group(0))