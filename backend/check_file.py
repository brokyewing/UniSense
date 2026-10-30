import subprocess, sys
fname = sys.argv[1]
r = subprocess.run(['npx','tsc','--noEmit'], capture_output=True, text=True, cwd=r'C:\Users\asker\Projelerim\UniSense\frontend', shell=True)
lines = [l for l in (r.stdout + r.stderr).split('\n') if 'error TS' in l and fname in l]
for l in lines:
    print(l)