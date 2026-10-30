import subprocess
r = subprocess.run(['git','add','-A'], capture_output=True, text=True, cwd=r'C:\Users\asker\Projelerim\UniSense')
r2 = subprocess.run(['git','commit','-m','chore cleanup'], capture_output=True, text=True, cwd=r'C:\Users\asker\Projelerim\UniSense')
print(r2.stdout.strip())
r3 = subprocess.run(['git','push','origin','main'], capture_output=True, text=True, cwd=r'C:\Users\asker\Projelerim\UniSense')
print('push:', r3.returncode)
import os
os.remove(r'C:\Users\asker\Projelerim\UniSense\backend\gs.py') if os.path.exists(r'C:\Users\asker\Projelerim\UniSense\backend\gs.py') else None
os.remove(r'C:\Users\asker\Projelerim\UniSense\backend\gs2.py') if os.path.exists(r'C:\Users\asker\Projelerim\UniSense\backend\gs2.py') else None