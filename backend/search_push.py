import os, re
base = r'C:\Users\asker\Projelerim\UniSense\backend\src'
for root, dirs, files in os.walk(base):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            content = open(path, encoding='utf-8').read()
            if 'push' in content.lower():
                # find route definitions
                for m in re.finditer(r'@(?:router|app)\.\w+\([^)]*push[^)]*\)', content):
                    print(path, '->', m.group(0))
                for m in re.finditer(r'def \w*push\w*\(', content):
                    print(path, '->', m.group(0))