p = r'C:\Users\asker\Projelerim\UniSense\frontend\src\pages\Recommend.tsx'
s = open(p, encoding='utf-8').read()
# component prop destructure
s = s.replace('function SafetyBadge({ level })', 'function SafetyBadge({ level }: any)')
s = s.replace('function DocCard({ item, isInTercih, onAdd, onRemove, busyCode })', 'function DocCard({ item, isInTercih, onAdd, onRemove, busyCode }: any)')
# catch
s = s.replace('} catch (e) {', '} catch (e: any) {')
# implicit any params - common
s = s.replace('.map((c, i) =>', '.map((c: any, i: number) =>')
s = s.replace('.map((t) =>', '.map((t: any) =>')
s = s.replace('.map((g, gi) =>', '.map((g: any, gi: number) =>')
s = s.replace('.map((l) =>', '.map((l: any) =>')
s = s.replace('.map((k) =>', '.map((k: any) =>')
s = s.replace('.map((o, i) =>', '.map((o: any, i: number) =>')
s = s.replace('.map((item) =>', '.map((item: any) =>')
s = s.replace('.filter((it) =>', '.filter((it: any) =>')
s = s.replace('.filter((g) =>', '.filter((g: any) =>')
s = s.replace('.filter((c) =>', '.filter((c: any) =>')
s = s.replace('.filter((k) =>', '.filter((k: any) =>')
s = s.replace('.some((it) =>', '.some((it: any) =>')
s = s.replace('.forEach((k) =>', '.forEach((k: any) =>')
s = s.replace('.forEach((n) =>', '.forEach((n: any) =>')
# function params
s = s.replace('function toggleTercih(item)', 'function toggleTercih(item: any)')
s = s.replace('function handleAdd(item)', 'function handleAdd(item: any)')
s = s.replace('function handleRemove(item)', 'function handleRemove(item: any)')
s = s.replace('function handleBulkAdd(codes)', 'function handleBulkAdd(codes: any)')
s = s.replace('function handleAddToPusula(name)', 'function handleAddToPusula(name: any)')
s = s.replace('function handleRemoveFromPusula(name)', 'function handleRemoveFromPusula(name: any)')
# indexing of RISK_STIL
s = s.replace('RISK_STIL[level]', '(RISK_STIL as any)[level]')
s = s.replace('RISK_STIL[item.riskLevel]', '(RISK_STIL as any)[item.riskLevel]')
open(p, 'w', encoding='utf-8').write(s)
print('done')