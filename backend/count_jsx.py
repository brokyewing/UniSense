import os, glob
files = glob.glob(r'C:\Users\asker\Projelerim\UniSense\frontend\src\**\*.jsx', recursive=True)
print(f'Total .jsx files: {len(files)}')
for f in sorted(files):
    print(f)