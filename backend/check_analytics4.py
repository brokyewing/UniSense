p = r'C:\Users\asker\Projelerim\UniSense\backend\src\unisense\api\v1\routes.py'
s = open(p, encoding='utf-8').read()
idx = s.find('@router.post("/analytics/log")')
print(s[idx:idx+300])