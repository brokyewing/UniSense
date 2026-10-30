import subprocess
r = subprocess.run(['npx','tsc','--noEmit'], capture_output=True, text=True, cwd=r'C:\Users\asker\Projelerim\UniSense\frontend', shell=True)
errs = [l for l in (r.stdout + r.stderr).split('\n') if 'error TS' in l]
print(f'TOTAL: {len(errs)}')