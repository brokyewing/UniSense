p = r'C:\Users\asker\Projelerim\UniSense\frontend\src\pages\Deneme.tsx'
s = open(p, encoding='utf-8').read()
# implicit any params
import re
# function params: turlerFor(s), flash(m), kaydet, etc.
s = s.replace('const turlerFor = (s) =>', 'const turlerFor = (s: any) =>')
s = s.replace('function flash(m) {', 'function flash(m: any) {')
s = s.replace('async function kaydet() {', 'async function kaydet() {')
s = s.replace('async function sil(d) {', 'async function sil(d: any) {')
s = s.replace('async function soruEkle() {', 'async function soruEkle() {')
s = s.replace('async function soruSil(s) {', 'async function soruSil(s: any) {')
s = s.replace('function trackUc() {', 'function trackUc() {')
s = s.replace('async function kocIste() {', 'async function kocIste() {')
# catch
s = s.replace('} catch (e) {', '} catch (e: any) {')
# setGirdi indexing
s = s.replace('nets[key]', 'nets[key as any]')
# Spark component
s = s.replace('function Spark({ points }) {', 'function Spark({ points }: any) {')
# setDY
s = s.replace('function setDY(field, k, v) {', 'function setDY(field: any, k: any, v: any) {')
# switchSinav
s = s.replace('function switchSinav(s) {', 'function switchSinav(s: any) {')
open(p, 'w', encoding='utf-8').write(s)
print('done')