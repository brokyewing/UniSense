import subprocess
from collections import Counter
r = subprocess.run(['npx','tsc','--noEmit'], capture_output=True, text=True, cwd=r'C:\Users\asker\Projelerim\UniSense\frontend', shell=True)
lines = [l for l in (r.stdout + r.stderr).split('\n') if 'error TS' in l]
files = Counter()
for l in lines:
    f = l.split('(')[0].replace('C:/Users/asker/Projelerim/UniSense/frontend/src/', '')
    files[f] += 1
print(f'Total: {len(lines)}')
for f, c in files.most_common():
    print(f'{c:3} {f}')