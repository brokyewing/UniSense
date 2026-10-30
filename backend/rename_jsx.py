import os, glob

base = r'C:\Users\asker\Projelerim\UniSense\frontend\src'
files = glob.glob(os.path.join(base, '**', '*.jsx'), recursive=True)
count = 0
for f in files:
    new_path = f.replace('.jsx', '.tsx')
    os.rename(f, new_path)
    count += 1
    print(f'Renamed: {os.path.basename(f)} -> {os.path.basename(new_path)}')

print(f'Total files renamed: {count}')