/**
 * Haftalık e-posta re-engagement — Push'un (özellikle iOS'ta) ulaşamadığı
 * kullanıcılar için ikinci kanal. GitHub Action cron ile çalışır (backend'e yük yok).
 *
 * SADECE opt-in (emailReminders==true) VE çalışmaya ara vermiş (3-10 gün) kullanıcılara
 * nazik bir "geri dön" e-postası yollar (KVKK — açık rıza + her mailde kapatma yönergesi).
 *
 * Dormant: RESEND_API_KEY yoksa hiçbir şey yapmadan çıkar (kurulmamışsa güvenli).
 * Gerekli: RESEND_API_KEY (Resend hesabı + doğrulanmış domain), GOOGLE_APPLICATION_CREDENTIALS.
 */
import { readFileSync } from 'node:fs'
import { initializeApp, cert } from 'firebase-admin/app'
import { getFirestore } from 'firebase-admin/firestore'

const RESEND = process.env.RESEND_API_KEY
if (!RESEND) { console.log('[email-digest] RESEND_API_KEY yok — dormant, atlandı'); process.exit(0) }
const FROM = process.env.EMAIL_FROM || 'UniSense <hatirlatma@unisense.com.tr>'

const saPath = process.env.GOOGLE_APPLICATION_CREDENTIALS
if (!saPath) { console.error('GOOGLE_APPLICATION_CREDENTIALS yok'); process.exit(1) }
initializeApp({ credential: cert(JSON.parse(readFileSync(saPath, 'utf-8'))) })
const db = getFirestore()

const today = new Date().toISOString().slice(0, 10)
const esc = (s = '') => String(s).replace(/[<>&"]/g, (c) => ({ '<': '&lt;', '>': '&gt;', '&': '&amp;', '"': '&quot;' }[c]))

const snap = await db.collection('users').where('emailReminders', '==', true).get()
let gonderilen = 0

for (const d of snap.docs) {
  const u = d.data()
  if (!u.email) continue
  const akt = await db.collection('users').doc(d.id).collection('aktivite').doc('gunluk').get()
  if (!akt.exists()) continue
  const last = akt.data().lastDate
  if (!last) continue
  const gunFark = Math.round((new Date(today) - new Date(last)) / 864e5)
  if (gunFark < 3 || gunFark > 10) continue // çok taze / çok eski → gönderme (spam yok)
  const streak = akt.data().longest || 0
  const ad = esc(u.displayName || 'Merhaba')

  const html = `<div style="font-family:system-ui,sans-serif;max-width:480px;margin:auto">
    <h2 style="color:#111">${ad}, seni özledik 📚</h2>
    <p style="color:#333">${gunFark} gündür çalışmaya ara verdin. En uzun serin <b>${streak} gün</b>di — bugün küçük bir adımla geri dön, momentumu kaybetme!</p>
    <p><a href="https://www.unisense.com.tr/konular" style="background:#6366f1;color:#fff;padding:11px 20px;border-radius:8px;text-decoration:none;display:inline-block">Çalışmaya devam et →</a></p>
    <p style="font-size:12px;color:#999;margin-top:24px">Bu hatırlatmaları istemiyorsan uygulamada <b>Çalışma → Pano → Haftalık e-posta hatırlatma</b>'yı kapatabilirsin.</p>
  </div>`

  const res = await fetch('https://api.resend.com/emails', {
    method: 'POST',
    headers: { Authorization: `Bearer ${RESEND}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ from: FROM, to: u.email, subject: `${ad}, çalışmaya dönme vakti 📚`, html }),
  })
  if (res.ok) gonderilen++
  else console.log(`[email-digest] gönderilemedi (${u.email}): ${res.status}`)
}

console.log(`[email-digest] ${gonderilen} e-posta gönderildi (today=${today})`)
process.exit(0)
