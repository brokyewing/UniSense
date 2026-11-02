p = r'C:\Users\asker\Projelerim\UniSense\backend\src\unisense\api\v1\routes.py'
s = open(p, encoding='utf-8').read()
for line in s.split('\n'):
    if 'import' in line and 'analytics' in line.lower():
        print(line.strip())