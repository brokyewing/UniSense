import subprocess
r = subprocess.run(['npx','tsc','--noEmit'], capture_output=True, text=True, cwd=r'C:\Users\asker\Projelerim\UniSense\frontend', shell=True)
for l in (r.stdout + r.stderr).split('\n'):
    if 'error TS' in l and 'App.tsx' in l:
        print(l)