# Unit economics: UniSense Pro — Türkiye üniversite tercih asistanı (RAG + resmi veri + sigmoid + garantili)

Every number below comes from the input file. Nothing is looked up or guessed.

## One kullanıcı/ay (aylık abonelik)

| line | per kullanıcı/ay (aylık abonelik) |
| --- | ---: |
| Price | $39.00 |
| Gemini API (RAG sorgusu/kullanıcı/ay) | -$0.50 |
| Firebase (Auth + Firestore + Storage) | -$0.30 |
| Render (Backend hosting, pay-as-you-go) | -$1.20 |
| Vercel (Frontend hosting, Pro plan paylaşımlı) | -$0.50 |
| Jooble/Careerjet API (Kariyer bonusu, premium) | -$2.00 |
| Payment gateway (İyzico/Stripe, %2.9 + 0.50 TL) | -$1.63 |
| SendGrid/Email + Twilio/SMS (Hatırlatıcı) | -$0.80 |
| **Contribution** (what each kullanıcı/ay (aylık abonelik) leaves to pay the fixed costs) | **$32.07** (82%) |

## The margin that matters

Fixed costs: $15,775 a month (Geliştirici maaş (part-time, 0.5 FTE) $15,000, Render (Backend, Starter plan) $210, Vercel (Pro plan, paylaşımlı) $20, Firebase (Spark plan - ücretsiz, quota içinde) $0, Gemini API (Free tier quota içinde) $0, Domain/SSL (unisense.com.tr) $15, Monitoring (Sentry/UptimeRobot) $30, Hesapçı/Muhasebe/Yasal $500).

- **Break-even: 17 kullanıcı/ay (aylık abonelik)s a day.** Below that you lose money every month.
- **Profit margin at your plan** (50 a day): **55%** of every sale, after every cost.
- Capacity: 10000 a day.

## Year 1, month by month

| month | kullanıcı/ay (aylık abonelik)s a day | revenue | profit | cumulative (after $75,000 startup) |
| ---: | ---: | ---: | ---: | ---: |
| 1 | 5 | $5,850 | -$10,964 | -$85,964 |
| 2 | 15 | $17,550 | -$1,344 | -$87,308 |
| 3 | 25 | $29,250 | $8,278 | -$79,030 |
| 4 | 40 | $46,800 | $22,709 | -$56,322 |
| 5 | 55 | $64,350 | $37,140 | -$19,181 |
| 6 | 70 | $81,900 | $51,572 | $32,391 |
| 7 | 85 | $99,450 | $66,004 | $98,394 |
| 8 | 100 | $117,000 | $80,435 | $178,830 |
| 9 | 120 | $140,400 | $99,677 | $278,506 |
| 10 | 150 | $175,500 | $128,540 | $407,046 |
| 11 | 200 | $234,000 | $176,645 | $583,692 |
| 12 | 300 | $351,000 | $272,855 | $856,546 |

- **Year 1 operating profit: $931,546** on $1,363,050 of revenue.
- After the $75,000 startup spend: $856,546.
- Startup money earned back: month 6.
- Cash you need before it pays for itself: **$87,308**.

## What if

| scenario | margin at plan | break-even a day | year 1 profit |
| --- | ---: | ---: | ---: |
| Base plan | 55% | 17 | $931,546 |
| Price -10% | 50% | 19 | $795,242 |
| Volume -20% | 49% | 17 | $707,377 |
| Unit costs +15% | 53% | 17 | $895,216 |

No red flags in these numbers. They are only as good as the inputs: check every cost against a real quote.
