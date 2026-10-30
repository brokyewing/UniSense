import subprocess, sys
r = subprocess.run(['npx','tsc','--noEmit'], capture_output=True, text=True, cwd=r'C:\Users\asker\Projelerim\UniSense\frontend', shell=True)
target = sys.argv[1] if len(sys.argv) > 1 else None
errs = [l for l in (r.stdout + r.stderr).split('\n') if 'error TS' in l]
if target:
    errs = [l for l in errs if target in l]
for l in errs:
    print(l)
print(f'\nTotal: {len(errs)}', file=sys.stderr)