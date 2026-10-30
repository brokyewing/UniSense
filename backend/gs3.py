import subprocess, os
os.remove(r'C:\Users\asker\Projelerim\UniSense\backend\gs2.py') if os.path.exists(r'C:\Users\asker\Projelerim\UniSense\backend\gs2.py') else None
r = subprocess.run(['git','add','-A'], capture_output=True, text=True, cwd=r'C:\Users\asker\Projelerim\UniSense')
r2 = subprocess.run(['git','commit','-m','chore cleanup2'], capture_output=True, text=True, cwd=r'C:\Users\asker\Projelerim\UniSense')
print(r2.stdout.strip())
r3 = subprocess.run(['git','push','origin','main'], capture_output=True, text=True, cwd=r'C:\Users\asker\Projelerim\UniSense')
print('push:', r3.returncode)
os.remove(r'C:\Users\asker\Projelerim\UniSense\backend\gs3.py') if os.path.exists(r'C:\Users\asker\Projelerim\UniSense\backend\gs3.py') else None