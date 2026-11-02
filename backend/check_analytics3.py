import os
base = r'C:\Users\asker\Projelerim\UniSense\backend\src'
for root, dirs, files in os.walk(base):
    for f in files:
        if f.endswith('.py'):
            path = os.path.join(root, f)
            content = open(path, encoding='utf-8').read()
            if 'class AnalyticsEvent' in content:
                print('===', path, '===')
                idx = content.find('class AnalyticsEvent')
                print(content[idx:idx+400])