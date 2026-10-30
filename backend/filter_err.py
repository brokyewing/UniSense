import sys
fname = sys.argv[1]
pattern = sys.argv[2] if len(sys.argv) > 2 else ''
lines = open(sys.argv[3] if len(sys.argv) > 3 else 'NUL').read().split('\n') if False else None
import subprocess
r = subprocess.run(['npx','tsc','--noEmit'], capture_output=True, text=True, cwd=r'C:\Users\asker\Projelerim\UniSense\frontend', shell=True)
for l in (r.stdout + r.stderr).split('\n'):
    if 'error TS' in l and fname in l:
        if not pattern or pattern in l:
            print(l)