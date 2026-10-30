import os, re, glob
base = r'C:\Users\asker\Projelerim\UniSense\frontend\src'
files = glob.glob(base + '/**/*.ts*', recursive=True) + glob.glob(base + '/**/*.js', recursive=True)
imports = set()
for f in files:
    content = open(f, encoding='utf-8', errors='ignore').read()
    for m in re.finditer(r"from ['\"]\.\.?/lib/(\w+)['\"]", content):
        imports.add(m.group(1))
    for m in re.finditer(r"from ['\"]@/lib/(\w+)['\"]", content):
        imports.add(m.group(1))
print(sorted(imports))