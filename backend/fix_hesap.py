import re
p = r'C:\Users\asker\Projelerim\UniSense\frontend\src\pages\Hesap.tsx'
s = open(p, encoding='utf-8').read()
# function params
s = s.replace('function netOf(dogru, yanlis, pen = YKS_PEN)', 'function netOf(dogru: any, yanlis: any, pen: any = YKS_PEN)')
s = s.replace('function weightedSum(nets, coefMap)', 'function weightedSum(nets: any, coefMap: any)')
s = s.replace('function tytHam(nets)', 'function tytHam(nets: any)')
s = s.replace('function aytWeighted(nets, type)', 'function aytWeighted(nets: any, type: any)')
s = s.replace('function kpssScore(nets)', 'function kpssScore(nets: any)')
s = s.replace('function dgsScores(nets, aobp)', 'function dgsScores(nets: any, aobp: any)')
s = s.replace('function alesWeightedNets(nets)', 'function alesWeightedNets(nets: any)')
s = s.replace('function lgsScore(nets)', 'function lgsScore(nets: any)')
s = s.replace('function aytHam(nets, type)', 'function aytHam(nets: any, type: any)')
# e catch
s = s.replace('} catch (e) {', '} catch (e: any) {')
# field/value/onChange
s = s.replace('function NetInput({ field, value, onChange })', 'function NetInput({ field, value, onChange }: any)')
# catch (e) already
open(p, 'w', encoding='utf-8').write(s)
print('done')