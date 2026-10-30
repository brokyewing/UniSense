p = r'C:\Users\asker\Projelerim\UniSense\.beyin\GOREVLER.md'
s = open(p, encoding='utf-8').read()
for line in s.split('\n'):
    if '- [ ]' in line or '- [x]' in line:
        print(line.strip())