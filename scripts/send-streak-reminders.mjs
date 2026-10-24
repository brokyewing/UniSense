/**
 * Streak hatırlatma göndericisi — GitHub Action cron ile çalışır (UniSense
 * backend'ine SIFIR yük; Render 512MB'a dokunmaz).
 *
 * Mantık: serisi olan (current ≥ 1) ama BUGÜN henüz çalışmamış, üstelik en son
 * DÜN çalışmış (yani bugün çalışmazsa seri kırılacak) kullanıcılara "serini koru"
 * push'u yollar. Böylece spam yok — yalnız seri riskteyken tek dürtme.
 *
 * lastDate formatı client'taki bugunStr() ile AYNI: UTC YYYY-MM-DD.
 *
 * Gerekli: GOOGLE_APPLICATION_CREDENTIALS (service account JSON yolu).
 */
import { readFileSync } from 'node:fs'
import { initializeApp, cert } from 'firebase-admin/app'
import { getFirestore } from 'firebase-admin/firestore'
import { getMessaging } from 'firebase-admin/messaging'

const saPath = process.env.GOOGLE_APPLICATION_CREDENTIALS
if (!saPath) { console.error('GOOGLE_APPLICATION_CREDENTIALS yok'); process.exit(1) }
const sa = JSON.parse(readFileSync(saPath, 'utf-8'))
initializeApp({ credential: cert(sa) })
const db = getFirestore()
const messaging = getMessaging()

const dayStr = (ms) => new Date(ms).toISOString().slice(0, 10)
const today = dayStr(Date.now())
const dun = dayStr(Date.now() - 864e5)

const snap = await db.collectionGroup('aktivite').get()
let hedef = 0
let gonderilen = 0
const silinecekler = []

for (const d of snap.docs) {
  if (d.id !== 'gunluk') continue
  const data = d.data() || {}
  const current = data.current || 0
  const lastDate = data.lastDate
  if (current < 1 || !lastDate) continue
  if (lastDate === today) continue   // bugün zaten çalışmış → dürtme
  if (lastDate !== dun) continue     // seri zaten kırılmış (eski) → spam yapma

  const uid = d.ref.parent.parent.id
  const tokensSnap = await db.collection('users').doc(uid).collection('pushTokens').get()
  const tokens = tokensSnap.docs.map((t) => t.id)
  if (!tokens.length) continue
  hedef++

  const res = await messaging.sendEachForMulticast({
    tokens,
    notification: {
      title: `🔥 ${current} günlük serini koru!`,
      body: 'Bugün henüz çalışmadın. Bir konu işaretle ya da deneme gir — serin devam etsin.',
    },
    data: { url: '/konular' },
    webpush: { fcmOptions: { link: 'https://www.unisense.com.tr/konular' } },
  })
  gonderilen += res.successCount

  // Geçersiz/expired token'ları temizle — delete'ler biriktirilir, çıkıştan ÖNCE beklenir
  // (fire-and-forget + process.exit, gRPC yazmalarını kesiyordu → temizlik hiç çalışmıyordu)
  res.responses.forEach((r, i) => {
    if (r.success) return
    const code = r.error?.code || ''
    if (code.includes('registration-token-not-registered') || code.includes('invalid-argument')) {
      silinecekler.push(
        db.collection('users').doc(uid).collection('pushTokens').doc(tokens[i]).delete().catch(() => {}),
      )
    }
  })
}

await Promise.allSettled(silinecekler)
console.log(`[streak-reminder] today=${today} · ${hedef} kullanıcı hedeflendi · ${gonderilen} bildirim gönderildi · ${silinecekler.length} ölü token silindi`)
process.exit(0)
