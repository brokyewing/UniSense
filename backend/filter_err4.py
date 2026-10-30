import subprocess
r = subprocess.run(['npx','tsc','--noEmit'], capture_output=True, text=True, cwd=r'C:\Users\asker\Projelerim\UniSense\frontend', shell=True)
errs = [l for l in (r.stdout + r.stderr).split('\n') if 'error TS' in l and 'hooks.ts' in l]
print(f'hooks.ts errors: {len(errs)}')
for l in errs:
    print(l)