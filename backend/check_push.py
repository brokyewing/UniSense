import re
# Check frontend api.ts for push
p = r'C:\Users\asker\Projelerim\UniSense\frontend\src\services\api.ts'
s = open(p, encoding='utf-8').read()
print('push in api.ts:', 'push' in s.lower())
# Check backend push endpoints
import os
for root, dirs, files in os.walk(r'C:\Users\asker\Projelerim\UniSense\backend'):
    for f in files:
        if 'push' in f.lower():
            print('backend push file:', os.path.join(root, f))