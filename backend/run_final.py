import subprocess
r = subprocess.run(['npm','run','build'], capture_output=True, text=True, cwd=r'C:\Users\asker\Projelerim\UniSense\frontend', shell=True, timeout=300)
print('BUILD:', r.returncode)
r2 = subprocess.run(['npm','test'], capture_output=True, text=True, cwd=r'C:\Users\asker\Projelerim\UniSense\frontend', shell=True, timeout=120)
print('TEST:', r2.returncode)
for l in (r2.stdout + r2.stderr).split('\n'):
    if 'passed' in l.lower() or 'failed' in l.lower():
        print(l.strip())