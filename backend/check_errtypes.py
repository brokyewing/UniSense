import subprocess, re
from collections import Counter
r = subprocess.run(['npx','tsc','--noEmit'], capture_output=True, text=True, cwd=r'C:\Users\asker\Projelerim\UniSense\frontend', shell=True)
lines = [l for l in (r.stdout + r.stderr).split('\n') if 'error TS' in l]
types = Counter()
for l in lines:
    m = re.search(r'error (TS\d+):', l)
    if m:
        types[m.group(1)] += 1
for t, c in types.most_common():
    print(f'{c:4} {t}')