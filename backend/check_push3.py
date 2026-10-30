p = r'C:\Users\asker\Projelerim\UniSense\backend\src\unisense\api\v1\routes.py'
s = open(p, encoding='utf-8').read()
import re
# find exam-reminder endpoint
idx = s.find('exam-reminder')
print(s[idx:idx+600])