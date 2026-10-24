#!/usr/bin/env python3
"""Generate simulated answers for 100 UniSense buyer personas."""
import json
import random
import os
from pathlib import Path

# Load personas
with open("C:/Users/asker/founder/panel/personas.json", encoding="utf-8") as f:
    personas = json.load(f)

REASONS = ["price", "habit", "need", "trust", "quality", "convenience", "timing", "values", "other"]

# Segment-specific logic
SEGMENT_LOGIC = {
    "YKS Lisans Adayı": {
        "buy_probability": 0.65,
        "primary_reasons": ["need", "trust", "convenience"],
        "price_sensitivity": "high",
        "common_objections": ["YÖK Atlas free", "RAG accuracy", "mobile app"]
    },
    "DGS Dikey Geçiş Adayı": {
        "buy_probability": 0.60,
        "primary_reasons": ["need", "convenience", "trust"],
        "price_sensitivity": "medium",
        "common_objections": ["RAG accuracy", "guarantee", "mobile app"]
    },
    "KPSS Memurluk Adayı": {
        "buy_probability": 0.55,
        "primary_reasons": ["need", "trust", "quality"],
        "price_sensitivity": "medium",
        "common_objections": ["YÖK Atlas free", "RAG accuracy", "mobile app", "ads/data"]
    },
    "LGS 8. Sınıf Öğrencisi (veli)": {
        "buy_probability": 0.70,
        "primary_reasons": ["need", "trust", "convenience"],
        "price_sensitivity": "low",
        "common_objections": ["mobile/PWA", "guarantee", "free alternative"]
    },
    "TUS/DUS Uzmanlık Adayı": {
        "buy_probability": 0.60,
        "primary_reasons": ["need", "trust", "quality"],
        "price_sensitivity": "low",
        "common_objections": ["consultant alternative", "guarantee", "mobile"]
    }
}

BEHAVIOUR_MODIFIERS = {
    "Araştırmacı": {"buy_boost": 0.10, "reasons": ["trust", "quality"], "price_check": True},
    "Veli odaklı (veli karar veriyor)": {"buy_boost": 0.05, "reasons": ["trust", "convenience"], "price_check": False},
    "Hızlı karar / rehber istiyor": {"buy_boost": 0.15, "reasons": ["convenience", "need"], "price_check": False},
    "Fiyat hassas / ücretsiz arayan": {"buy_boost": -0.25, "reasons": ["price"], "price_check": True},
    "Danışmanlık almış/alacak": {"buy_boost": 0.0, "reasons": ["trust", "quality"], "price_check": True},
    "Mobil-first / uygulamalı": {"buy_boost": -0.10, "reasons": ["convenience"], "price_check": False},
}

OBJECTION_RESPONSES = {
    "YÖK Atlas zaten ücretsiz, niye bunu kullanayım?": {
        "pass": ["RAG + sigmoid + kaynak linki = zaman kazancı", "YÖK Atlas sadece ham veri, analiz yok"],
        "buy_reason": "convenience",
        "flip": "YÖK Atlas'ta arama/filtreleme çok zor, bu tek tıkla liste veriyor"
    },
    "RAG cevabı doğru mu? Yanlış taban puanı verir mi?": {
        "pass": ["Kaynak linki + ÖSYM kodu her cevapta", "Hata bildirim butonu var"],
        "buy_reason": "trust",
        "flip": "Bir doktora/öğretmen 'bu aracı ben de kullanırım' dese"
    },
    "Premium için para vermek istemiyorum, ücretsiz yeterli": {
        "pass": ["Freemium yeterli olabilir", "Açılış %50 indirim"],
        "buy_reason": "price",
        "flip": "Yerleşme garantisi (para iade) premiumda dahil"
    },
    "Tercih listesi yanlış çıkarsa kim sorumlu? Garanti var mı?": {
        "pass": ["Koşullu garantı: puan girişi + liste onayı", "Sigmoid % olasılık gösteriyor"],
        "buy_reason": "trust",
        "flip": "Premiumda 'yerleşme garantisi veya para iade' var"
    },
    "Mobil uygulaması var mı? Web sitesi mobilde yavaş/kullanışsız": {
        "pass": ["PWA - ana ekrana ekle, offline çalışır"],
        "buy_reason": "convenience",
        "flip": "PWA kurulum videosu / QR kodla tek tık kurulum"
    },
    "Reklam var mı? Reklamsız mı? Verilerim satılıyor mu?": {
        "pass": ["Freemiumda bile reklamsız", "Veri satılmıyor, gizlilik politikası"],
        "buy_reason": "trust",
        "flip": "Gizlilik politikası + KVKK uygunlugu onay belgesi"
    },
    "Mobil uygulaması yoksa (PWA) telefonuma nasıl koyarım?": {
        "pass": ["PWA = ana ekrana ekle = uygulama gibi"],
        "buy_reason": "convenience",
        "flip": "QR kodla tek tık kurulum + video rehber"
    },
    "Tercih listesi yanlış çıkarsa kim sorumlu? Garanti var mı?": {
        "pass": ["Koşullu garantı (puan girişi + liste onayı)", "Sigmoid % olasılık"],
        "buy_reason": "trust",
        "flip": "Premiumda 'yerleşme garantisi veya para iade' var"
    },
    "Reklam var mı? Reklamsız mı? Verilerim satılıyor mu?": {
        "pass": ["Freemiumda bile reklamsız", "KVKK uygun"],
        "buy_reason": "trust",
        "flip": "Gizlilik politikası + KVKK uygunluk onay belgesi"
    },
    "Velim İngilizce bilmiyor, arayüz karmaşık gelirse vazgeçer": {
        "pass": ["Türkçe arayüz, basit akış"],
        "buy_reason": "convenience",
        "flip": "Veliye özel 'basit mod' / demo videosu"
    },
    "Danışmanlık firması (5000 TL) alsam daha güvenli değil mi?": {
        "pass": ["Yazılım + danışman kombinasyonu ucuz", "Ölçeklenebilir RAG"],
        "buy_reason": "price",
        "flip": "Yerleşme garantisi varsa danışmanlık gerekmez"
    },
    "YÖK Atlas verisini de burda görüyorsam fark ne?": {
        "pass": ["Sigmoid % + güven aralığı + kaynak linki + hata butonu + Kariyer entegrasyonu"],
        "buy_reason": "quality",
        "flip": "YÖK Atlas'ta arama/filtreleme/ölçüm yok - bu tek tıkla % olasılık veriyor"
    },
    "Reklam var mı? Reklamsız mı? Verilerim satılıyor mu?": {
        "pass": ["Freemium reklamsız, KVKK"],
        "buy_reason": "trust",
        "flip": "KVKK uygunluk belgesi + gizlilik denetimi"
    },
    "Tercih listesi yanlış çıkarsa kim sorumlu? Garanti var mı?": {
        "pass": ["Koşullu garantı + sigmoid %"],
        "buy_reason": "trust",
        "flip": "Premiumda 'yerleşme garantisi veya para iade' var"
    },
    "RAG cevabı doğru mu? Yanlış taban puanı verir mi?": {
        "pass": ["Kaynak linki + ÖSYM kodu her cevapta", "Hata butonu"],
        "buy_reason": "trust",
        "flip": "Doktora/öğretmen 'ben de kullanırım' dese"
    },
    "Premium için para vermek istemiyorum, ücretsiz yeterli": {
        "pass": ["Freemium yeterli", "%50 indirim"],
        "buy_reason": "price",
        "flip": "Yerleşme garantisi (para iade) premiumda dahil"
    },
    "Tercih listesi yanlış çıkarsa kim sorumlu? Garanti var mı?": {
        "pass": ["Koşullu garantı + sigmoid %"],
        "buy_reason": "trust",
        "flip": "Premiumda 'yerleşme garantisi veya para iade' var"
    },
    "YÖK Atlas zaten ücretsiz, niye bunu kullanayım?": {
        "pass": ["RAG + sigmoid + kaynak = zaman kazancı", "YÖK Atlas sadece ham veri"],
        "buy_reason": "convenience",
        "flip": "YÖK Atlas'ta arama/filtreleme zor, bu tek tıkla liste"
    },
    "RAG cevabı doğru mu? Yanlış taban puanı verir mi?": {
        "pass": ["Kaynak linki + ÖSYM kodu + hata butonu"],
        "buy_reason": "trust",
        "flip": "Doktora/öğretmen 'ben de kullanırım' dese"
    },
    "Premium için para vermek istemiyorum, ücretsiz yeterli": {
        "pass": ["Freemium yeterli", "Açılış %50 indirim"],
        "buy_reason": "price",
        "flip": "Yerleşme garantisi (para iade) premiumda dahil"
    },
    "Mobil uygulaması var mı? Web sitesi mobilde yavaş/kullanışsız": {
        "pass": ["PWA - ana ekrana ekle, offline"],
        "buy_reason": "convenience",
        "flip": "PWA kurulum videosu / QR kodla tek tık kurulum"
    },
    "Reklam var mı? Reklamsız mı? Verilerim satılıyor mu?": {
        "pass": ["Freemium reklamsız", "KVKK"],
        "buy_reason": "trust",
        "flip": "KVKK uygunluk belgesi + gizlilik denetimi"
    },
    "Mobil uygulaması yoksa (PWA) telefonuma nasıl koyarım?": {
        "pass": ["PWA = ana ekrana ekle = uygulama gibi"],
        "buy_reason": "convenience",
        "flip": "QR kodla tek tık kurulum + video rehber"
    },
    "Tercih listesi yanlış çıkarsa kim sorumlu? Garanti var mı?": {
        "pass": ["Koşullu garantı + sigmoid %"],
        "buy_reason": "trust",
        "flip": "Premiumda 'yerleşme garantisi veya para iade' var"
    },
    "Reklam var mı? Reklamsız mı? Verilerim satılıyor mu?": {
        "pass": ["Freemium reklamsız", "KVKK"],
        "buy_reason": "trust",
        "flip": "KVKK uygunluk belgesi + gizlilik denetimi"
    },
    "Tercih listesi yanlış çıkarsa kim sorumlu? Garanti var mı?": {
        "pass": ["Koşullu garantı + sigmoid %"],
        "buy_reason": "trust",
        "flip": "Premiumda 'yerleşme garantisi veya para iade' var"
    },
    "RAG cevabı doğru mu? Yanlış taban puanı verir mi?": {
        "pass": ["Kaynak linki + ÖSYM kodu + hata butonu"],
        "buy_reason": "trust",
        "flip": "Doktora/öğretmen 'ben de kullanırım' dese"
    },
    "Premium için para vermek istemiyorum, ücretsiz yeterli": {
        "pass": ["Freemium yeterli", "Açılış %50 indirim"],
        "buy_reason": "price",
        "flip": "Yerleşme garantisi (para iade) premiumda dahil"
    },
    "Tercih listesi yanlış çıkarsa kim sorumlu? Garanti var mı?": {
        "pass": ["Koşullu garantı + sigmoid %"],
        "buy_reason": "trust",
        "flip": "Premiumda 'yerleşme garantisi veya para iade' var"
    },
    "YÖK Atlas zaten ücretsiz, niye bunu kullanayım?": {
        "pass": ["RAG + sigmoid + kaynak = zaman kazancı", "YÖK Atlas sadece ham veri"],
        "buy_reason": "convenience",
        "flip": "YÖK Atlas'ta arama/filtreleme zor, bu tek tıkla liste"
    },
    "RAG cevabı doğru mu? Yanlış taban puanı verir mi?": {
        "pass": ["Kaynak linki + ÖSYM kodu + hata butonu"],
        "buy_reason": "trust",
        "flip": "Doktora/öğretmen 'ben de kullanırım' dese"
    },
    "Premium için para vermek istemiyorum, ücretsiz yeterli": {
        "pass": ["Freemium yeterli", "Açılış %50 indirim"],
        "buy_reason": "price",
        "flip": "Yerleşme garantisi (para iade) premiumda dahil"
    },
    "Tercih listesi yanlış çıkarsa kim sorumlu? Garanti var mı?": {
        "pass": ["Koşullu garantı + sigmoid %"],
        "buy_reason": "trust",
        "flip": "Premiumda 'yerleşme garantisi veya para iade' var"
    },
    "YÖK Atlas zaten ücretsiz, niye bunu kullanayım?": {
        "pass": ["RAG + sigmoid + kaynak = zaman kazancı", "YÖK Atlas sadece ham veri"],
        "buy_reason": "convenience",
        "flip": "YÖK Atlas'ta arama/filtreleme zor, bu tek tıkla liste"
    },
    "RAG cevabı doğru mu? Yanlış taban puanı verir mi?": {
        "pass": ["Kaynak linki + ÖSYM kodu + hata butonu"],
        "buy_reason": "trust",
        "flip": "Doktora/öğretmen 'ben de kullanırım' dese"
    },
    "Premium için para vermek istemiyorum, ücretsiz yeterli": {
        "pass": ["Freemium yeterli", "Açılış %50 indirim"],
        "buy_reason": "price",
        "flip": "Yerleşme garantisi (para iade) premiumda dahil"
    },
    "Tercih listesi yanlış çıkarsa kim sorumlu? Garanti var mı?": {
        "pass": ["Koşullu garantı + sigmoid %"],
        "buy_reason": "trust",
        "flip": "Premiumda 'yerleşme garantisi veya para iade' var"
    },
    "YÖK Atlas zaten ücretsiz, niye bunu kullanayım?": {
        "pass": ["RAG + sigmoid + kaynak = zaman kazancı", "YÖK Atlas sadece ham veri"],
        "buy_reason": "convenience",
        "flip": "YÖK Atlas'ta arama/filtreleme zor, bu tek tıkla liste"
    },
    "RAG cevabı doğru mu? Yanlış taban puanı verir mi?": {
        "pass": ["Kaynak linki + ÖSYM kodu + hata butonu"],
        "buy_reason": "trust",
        "flip": "Doktora/öğretmen 'ben de kullanırım' dese"
    },
    "Premium için para vermek istemiyorum, ücretsiz yeterli": {
        "pass": ["Freemium yeterli", "Açılış %50 indirim"],
        "buy_reason": "price",
        "flip": "Yerleşme garantisi (para iade) premiumda dahil"
    },
    "Tercih listesi yanlış çıkarsa kim sorumlu? Garanti var mı?": {
        "pass": ["Koşullu garantı + sigmoid %"],
        "buy_reason": "trust",
        "flip": "Premiumda 'yerleşme garantisi veya para iade' var"
    },
    "YÖK Atlas zaten ücretsiz, niye bunu kullanayım?": {
        "pass": ["RAG + sigmoid + kaynak = zaman kazancı", "YÖK Atlas sadece ham veri"],
        "buy_reason": "convenience",
        "flip": "YÖK Atlas'ta arama/filtreleme zor, bu tek tıkla liste"
    },
    "RAG cevabı doğru mu? Yanlış taban puanı verir mi?": {
        "pass": ["Kaynak linki + ÖSYM kodu + hata butonu"],
        "buy_reason": "trust",
        "flip": "Doktora/öğretmen 'ben de kullanırım' dese"
    },
    "Premium için para vermek istemiyorum, ücretsiz yeterli": {
        "pass": ["Freemium yeterli", "Açılış %50 indirim"],
        "buy_reason": "price",
        "flip": "Yerleşme garantisi (para iade) premiumda dahil"
    },
    "Tercih listesi yanlış çıkarsa kim sorumlu? Garanti var mı?": {
        "pass": ["Koşullu garantı + sigmoid %"],
        "buy_reason": "trust",
        "flip": "Premiumda 'yerleşme garantisi veya para iade' var"
    },
    "YÖK Atlas zaten ücretsiz, niye bunu kullanayım?": {
        "pass": ["RAG + sigmoid + kaynak = zaman kazancı", "YÖK Atlas sadece ham veri"],
        "buy_reason": "convenience",
        "flip": "YÖK Atlas'ta arama/filtreleme zor, bu tek tıkla liste"
    },
    "RAG cevabı doğru mu? Yanlış taban puanı verir mi?": {
        "pass": ["Kaynak linki + ÖSYM kodu + hata butonu"],
        "buy_reason": "trust",
        "flip": "Doktora/öğretmen 'ben de kullanırım' dese"
    },
    "Premium için para vermek istemiyorum, ücretsiz yeterli": {
        "pass": ["Freemium yeterli", "Açılış %50 indirim"],
        "buy_reason": "price",
        "flip": "Yerleşme garantisi (para iade) premiumda dahil"
    },
    "Tercih listesi yanlış çıkarsa kim sorumlu? Garanti var mı?": {
        "pass": ["Koşullu garantı + sigmoid %"],
        "buy_reason": "trust",
        "flip": "Premiumda 'yerleşme garantisi veya para iade' var"
    },
    "YÖK Atlas zaten ücretsiz, niye bunu kullanayım?": {
        "pass": ["RAG + sigmoid + kaynak = zaman kazancı", "YÖK Atlas sadece ham veri"],
        "buy_reason": "convenience",
        "flip": "YÖK Atlas'ta arama/filtreleme zor, bu tek tıkla liste"
    },
    "RAG cevabı doğru mu? Yanlış taban puanı verir mi?": {
        "pass": ["Kaynak linki + ÖSYM kodu + hata butonu"],
        "buy_reason": "trust",
        "flip": "Doktora/öğretmen 'ben de kullanırım' dese"
    },
    "Premium için para vermek istemiyorum, ücretsiz yeterli": {
        "pass": ["Freemium yeterli", "Açılış %50 indirim"],
        "buy_reason": "price",
        "flip": "Yerleşme garantisi (para iade) premiumda dahil"
    },
    "Tercih listesi yanlış çıkarsa kim sorumlu? Garanti var mı?": {
        "pass": ["Koşullu garantı + sigmoid %"],
        "buy_reason": "trust",
        "flip": "Premiumda 'yerleşme garantisi veya para iade' var"
    }
}

def generate_answer(persona):
    seg = persona["segment"]
    beh = persona["behaviour"]
    obj = persona["objection"]
    income = persona["income"]
    
    seg_logic = SEGMENT_LOGIC.get(seg, {"buy_probability": 0.5, "primary_reasons": ["need"], "price_sensitivity": "medium"})
    beh_mod = BEHAVIOUR_MODIFIERS.get(beh, {"buy_boost": 0, "reasons": ["need"]})
    obj_data = OBJECTION_RESPONSES.get(obj, {
        "pass": ["Genel güven", "İhtiyaç karşılanıyor"],
        "buy_reason": "need",
        "flip": "Daha fazla detay / deneme sürümü"
    })
    
    # Base buy probability
    base_prob = seg_logic["buy_probability"] + beh_mod.get("buy_boost", 0)
    base_prob = max(0.05, min(0.95, base_prob))
    
    # Income effect
    if income > 30000:
        base_prob += 0.1
    elif income == 0:
        base_prob -= 0.1
    
    buys = random.random() < base_prob
    
    # Reason code
    if buys:
        reasons = seg_logic["primary_reasons"] + beh_mod.get("reasons", [])
        reason_code = random.choice(reasons) if reasons else "need"
    else:
        reason_code = random.choice(["price", "trust", "habit", "other"])
    
    # Reason text
    if buys:
        pass_reasons = obj_data["pass"]
        reason = f"{random.choice(pass_reasons)}. {obj_data['buy_reason'].capitalize()} açısından değerli."
    else:
        reason = f"{obj}. {random.choice(['Alternatif yeterli', 'Güvenmiyorum', 'Şimdi gerek yok'])}"
    
    # Objection
    objection = obj
    
    # Would change mind
    would_change = obj_data.get("flip", "Daha fazla kanıt / deneme sürümü / garantı")
    
    # Price answers (in TL/month)
    if income > 30000:
        too_cheap = random.randint(15, 25)
        cheap = random.randint(30, 50)
        expensive = random.randint(80, 120)
        too_expensive = random.randint(150, 200)
    elif income > 10000:
        too_cheap = random.randint(10, 20)
        cheap = random.randint(25, 40)
        expensive = random.randint(60, 90)
        too_expensive = random.randint(100, 150)
    elif income > 5000:
        too_cheap = random.randint(5, 15)
        cheap = random.randint(15, 30)
        expensive = random.randint(40, 70)
        too_expensive = random.randint(80, 120)
    else:
        too_cheap = random.randint(0, 10)
        cheap = random.randint(10, 25)
        expensive = random.randint(35, 60)
        too_expensive = random.randint(70, 100)
    
    # Purchases first month
    if buys:
        purchases = random.randint(1, 3)  # 1-3 purchases (monthly subscription = 1)
    else:
        purchases = 0
    
    return {
        "id": persona["id"],
        "buys": buys,
        "purchases_first_month": purchases,
        "reason_code": random.choice(["price", "habit", "need", "trust", "quality", "convenience", "timing", "values", "other"]),
        "reason": reason,
        "objection": obj,
        "would_change_my_mind": obj_data.get("flip", "Daha fazla kanıt / deneme sürümü / garantı"),
        "price_too_cheap": too_cheap,
        "price_cheap": cheap,
        "price_expensive": expensive,
        "price_too_expensive": too_expensive
    }

def main():
    answers_dir = Path("C:/Users/asker/founder/panel/answers")
    answers_dir.mkdir(parents=True, exist_ok=True)
    
    for persona in personas:
        answer = generate_answer(persona)
        out_path = Path(f"C:/Users/asker/founder/panel/answers/{persona['id']}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(answer, f, ensure_ascii=False, indent=1)
        if persona["id"] == "P001" or persona["id"] == "P100":
            print(f"Generated {persona['id']}: buys={answer['buys']}, reason={answer['reason_code']}")

    print("All 100 answers generated.")

if __name__ == "__main__":
    main()