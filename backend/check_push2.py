p = r'C:\Users\asker\Projelerim\UniSense\backend\src\unisense\api\v1\routes.py'
s = open(p, encoding='utf-8').read()
import re
for m in re.finditer(r'@router\.\w+\([^)]*push[^)]*\)[^\n]*\n(?:.*\n){0,15}', s):
    print(m.group(0))
    print('---')