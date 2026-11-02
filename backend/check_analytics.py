import os, re
# find analytics endpoint in backend
base = r'C:\Users\asker\Projelerim\UniSense\backend\src'
for root, dirs, files in os.walk(base):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            content = open(path, encoding='utf-8').read()
            if 'analytics' in content.lower() and ('log' in content.lower() or 'router' in content.lower()):
                print('===', path, '===')
                for m in re.finditer(r'@router\.\w+\([^\n]*analytics[^\n]*\)', content):
                    print(m.group(0))