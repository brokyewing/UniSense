"""İlgi Pusulası — bölüm kategorizasyonu, etiket ve kişilik ekseni eşleştirmesi.

Heuristik kural tabanlı: 358 lisans bölüm grubunu 9 ana kategoriye ayırır,
her bölüme 2-4 etiket ve 5-boyutlu kişilik vektörü atar.

Kişilik ekseni (1-5 ölçek):
- math:     matematik/sayısal yoğunluk
- human:    insan odaklı çalışma (sosyal ilişki, hizmet)
- creative: yaratıcı/estetik üretim
- research: derinlemesine araştırma/teori
- field:    saha/uygulama yoğunluğu (ofis dışı)
"""
from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path

from unisense.core.config import get_settings


# === Kategori şablonları: (id, label, emoji, default_axes [m,h,c,r,f]) ===
CATEGORIES: dict[str, dict] = {
    "muhendislik":   {"label": "Mühendislik",       "emoji": "🔧", "default": [5, 2, 3, 3, 3]},
    "saglik":        {"label": "Sağlık",            "emoji": "🏥", "default": [3, 5, 1, 3, 4]},
    "sosyal_hukuk":  {"label": "Sosyal & Hukuk",    "emoji": "⚖️", "default": [2, 4, 2, 4, 2]},
    "iktisat":       {"label": "İktisat & İşletme", "emoji": "💼", "default": [4, 4, 2, 3, 2]},
    "sanat":         {"label": "Sanat & Tasarım",   "emoji": "🎨", "default": [1, 3, 5, 2, 3]},
    "doga":          {"label": "Doğa Bilimleri",    "emoji": "🧪", "default": [5, 1, 2, 5, 3]},
    "egitim":        {"label": "Eğitim",            "emoji": "📚", "default": [2, 5, 2, 2, 3]},
    "dil":           {"label": "Dil & Edebiyat",    "emoji": "🌍", "default": [1, 4, 4, 4, 2]},
    "diger":         {"label": "Diğer",             "emoji": "⚙️", "default": [3, 3, 3, 3, 3]},
}


# Kural: (regex, kategori, etiketler, opsiyonel eksen_override)
# Sıra önemli — ilk eşleşen kazanır.
_RULES: list[tuple[str, str, list[str], list[int] | None]] = [
    # Tıp/Sağlık (en spesifik önce)
    (r"\btıp\b",                 "saglik", ["sağlık", "hasta", "klinik"], [4, 5, 1, 5, 4]),
    (r"diş hekim",               "saglik", ["diş", "klinik", "el becerisi"], [3, 5, 2, 3, 4]),
    (r"eczacılık",               "saglik", ["ilaç", "kimya", "klinik"], [4, 4, 1, 4, 2]),
    (r"hemşirelik",              "saglik", ["hasta bakımı", "klinik", "şefkat"], [2, 5, 1, 2, 5]),
    (r"ebelik",                  "saglik", ["doğum", "anne-bebek", "klinik"], [2, 5, 1, 2, 5]),
    (r"fizyoterapi",             "saglik", ["rehabilitasyon", "vücut", "tedavi"], [3, 5, 2, 3, 5]),
    (r"beslenme",                "saglik", ["sağlık", "diyet", "kimya"], [3, 4, 2, 4, 3]),
    (r"odyoloji",                "saglik", ["işitme", "klinik", "teknoloji"], [3, 5, 1, 4, 3]),
    (r"veteriner",               "saglik", ["hayvan", "klinik", "saha"], [3, 4, 1, 3, 5]),
    (r"sağlık yönetim",          "saglik", ["yönetim", "hastane", "iş"], [3, 4, 2, 2, 2]),
    (r"sağlık (bilim|teknik|kurum|hizmet)", "saglik", ["sağlık", "kamu", "hizmet"], None),
    (r"acil yardım|paramedik",   "saglik", ["acil", "saha", "ilk yardım"], [3, 5, 1, 2, 5]),
    (r"sağlık fizik|biyofizik",  "saglik", ["fizik", "tıbbi", "araştırma"], [5, 2, 1, 5, 2]),
    (r"diyaliz|protez|ortez|cerrahi tek", "saglik", ["klinik", "teknoloji", "vücut"], None),

    # Mühendislik (alt-dallarla)
    (r"bilgisayar mühendis|yazılım mühendis|yapay zeka|veri mühendis|bilişim sistem|yönetim bilişim",
        "muhendislik", ["yazılım", "algoritma", "matematik"], [5, 2, 3, 4, 1]),
    (r"elektrik(-elektronik)? mühendis|elektronik (ve haberleşme )?mühendis",
        "muhendislik", ["devre", "sinyal", "fizik"], [5, 2, 2, 4, 3]),
    (r"makine mühendis|mekatronik mühendis",
        "muhendislik", ["mekanik", "imalat", "fizik"], [5, 2, 3, 3, 4]),
    (r"endüstri mühendis|sistem mühendis",
        "muhendislik", ["süreç", "optimizasyon", "yöneylem"], [5, 4, 2, 4, 2]),
    (r"inşaat mühendis|yapı mühendis",
        "muhendislik", ["yapı", "saha", "fizik"], [5, 2, 2, 3, 5]),
    (r"kimya mühendis",          "muhendislik", ["kimya", "süreç", "endüstri"], [5, 2, 2, 4, 3]),
    (r"biyomedikal mühendis|biyomühendis",
        "muhendislik", ["sağlık", "teknoloji", "biyoloji"], [4, 4, 2, 5, 2]),
    (r"havacılık|uçak|uzay|astron(omi |aut)",
        "muhendislik", ["havacılık", "fizik", "teknoloji"], [5, 2, 3, 4, 3]),
    (r"otomotiv mühendis",       "muhendislik", ["araç", "mekanik", "imalat"], [5, 2, 3, 3, 4]),
    (r"gıda mühendis",           "muhendislik", ["gıda", "kimya", "endüstri"], [4, 3, 2, 4, 3]),
    (r"çevre mühendis",          "muhendislik", ["çevre", "kimya", "saha"], [4, 3, 2, 4, 5]),
    (r"jeoloji mühendis|petrol|maden mühendis|jeofizik",
        "muhendislik", ["jeoloji", "saha", "fizik"], [5, 1, 1, 4, 5]),
    (r"metal(urji)? mühendis|malzeme",
        "muhendislik", ["metal", "kimya", "imalat"], [5, 2, 2, 4, 3]),
    (r"tekstil mühendis",        "muhendislik", ["tekstil", "imalat", "tasarım"], [4, 3, 3, 3, 3]),
    (r"orman (endüstri )?mühendis",
        "muhendislik", ["doğa", "saha", "ekoloji"], [4, 2, 2, 3, 5]),
    (r"harita mühendis|geomatik|jeodezi",
        "muhendislik", ["harita", "uydu", "saha"], [5, 2, 2, 3, 5]),
    (r"deniz (taşımacılığ|ulaştırm|teknoloji|işletme|harita)|gemi (inşa|makine)",
        "muhendislik", ["deniz", "saha", "teknik"], [4, 2, 2, 3, 5]),
    (r"nükleer (enerji )?mühendis",
        "muhendislik", ["fizik", "enerji", "araştırma"], [5, 1, 1, 5, 2]),
    (r"enerji sistemleri mühendis",
        "muhendislik", ["enerji", "sistem", "fizik"], [5, 2, 2, 4, 3]),
    (r"endüstri sistemleri|imalat mühendis",
        "muhendislik", ["üretim", "sistem", "imalat"], [5, 3, 2, 3, 3]),
    (r"mühendis",                "muhendislik", ["teknik", "fizik", "matematik"], None),

    # Hukuk + Sosyal
    (r"\bhukuk\b",               "sosyal_hukuk", ["adalet", "yasalar", "müzakere"], [1, 5, 2, 4, 2]),
    (r"siyaset|kamu yönet|uluslararası ilişk|küresel siyaset|diplomas",
        "sosyal_hukuk", ["politika", "kamu", "analiz"], [2, 4, 2, 4, 2]),
    (r"psikoloji",               "sosyal_hukuk", ["zihin", "insan", "araştırma"], [2, 5, 2, 5, 2]),
    (r"sosyoloji|antropoloji",   "sosyal_hukuk", ["toplum", "insan", "araştırma"], [1, 4, 2, 5, 3]),
    (r"felsefe",                 "sosyal_hukuk", ["düşünce", "mantık", "okuma"], [2, 3, 2, 5, 1]),
    (r"\btarih\b",               "sosyal_hukuk", ["geçmiş", "kaynak", "okuma"], [1, 3, 2, 5, 2]),
    (r"sanat tarihi",            "sosyal_hukuk", ["sanat", "tarih", "araştırma"], [1, 3, 4, 5, 2]),
    (r"coğrafya",                "sosyal_hukuk", ["dünya", "saha", "harita"], [3, 2, 2, 4, 4]),
    (r"arkeoloji|kültür varlık", "sosyal_hukuk", ["geçmiş", "saha", "araştırma"], [1, 2, 2, 5, 5]),
    (r"sosyal hizmet",           "sosyal_hukuk", ["yardım", "insan", "saha"], [1, 5, 1, 3, 4]),
    (r"adalet|ceza infaz",       "sosyal_hukuk", ["adalet", "yasa", "kamu"], [1, 4, 1, 3, 3]),

    # Eğitim
    (r"öğretmenliği|öğretmen|eğitim (program|yöneticilik|bilim)",
        "egitim", ["öğretim", "çocuk/genç", "iletişim"], [3, 5, 3, 2, 3]),
    (r"okul öncesi",             "egitim", ["çocuk", "oyun", "gelişim"], [1, 5, 4, 2, 3]),
    (r"rehberlik|psikolojik dan", "egitim", ["danışmanlık", "psikoloji", "iletişim"], [2, 5, 2, 4, 2]),
    (r"özel eğitim",             "egitim", ["engelli", "şefkat", "saha"], [1, 5, 3, 3, 4]),
    (r"çocuk gelişim",           "egitim", ["çocuk", "gelişim", "oyun"], [1, 5, 3, 3, 3]),

    # İktisat & İşletme
    (r"\biktisat\b|ekonomi",     "iktisat", ["piyasa", "para", "analiz"], [4, 3, 2, 4, 1]),
    (r"\bişletme\b|yönetim$",    "iktisat", ["şirket", "yönetim", "iş"], [3, 4, 2, 3, 2]),
    (r"maliye",                  "iktisat", ["devlet", "vergi", "muhasebe"], [4, 3, 1, 3, 1]),
    (r"muhasebe|finans",         "iktisat", ["sayı", "para", "denetim"], [4, 2, 1, 3, 1]),
    (r"bankacılık",              "iktisat", ["finans", "müşteri", "iş"], [4, 4, 1, 2, 2]),
    (r"sigortacılık|aktüer",     "iktisat", ["risk", "matematik", "sayı"], [5, 3, 1, 4, 1]),
    (r"pazarlama|reklam",        "iktisat", ["satış", "marka", "yaratıcı"], [3, 5, 4, 3, 2]),
    (r"lojistik|tedarik",        "iktisat", ["taşıma", "süreç", "saha"], [3, 3, 1, 2, 4]),
    (r"insan kaynak",            "iktisat", ["insan", "yönetim", "psikoloji"], [2, 5, 2, 3, 2]),
    (r"turizm",                  "iktisat", ["seyahat", "müşteri", "iletişim"], [2, 5, 3, 2, 4]),
    (r"gastronomi|aşçılık",      "iktisat", ["yemek", "yaratıcı", "saha"], [1, 4, 5, 2, 5]),
    (r"emlak|gayrimenkul",       "iktisat", ["taşınmaz", "satış", "iş"], [3, 4, 1, 2, 3]),
    (r"uluslararası ticaret|dış ticaret",
        "iktisat", ["ihracat", "ekonomi", "yabancı dil"], [3, 4, 1, 3, 2]),

    # Sanat & Tasarım
    (r"mimar(lık)?",             "sanat", ["mekan", "tasarım", "estetik"], [4, 3, 5, 3, 3]),
    (r"\biç mimar",              "sanat", ["mekan", "estetik", "tasarım"], [3, 4, 5, 2, 3]),
    (r"endüstriyel tasarım",     "sanat", ["ürün", "yaratıcı", "fonksiyon"], [3, 3, 5, 3, 3]),
    (r"grafik (tasarım|sanat)|görsel iletişim",
        "sanat", ["görsel", "yaratıcı", "yazılım"], [2, 3, 5, 2, 1]),
    (r"moda tasarım",            "sanat", ["kıyafet", "yaratıcı", "trend"], [1, 3, 5, 2, 3]),
    (r"animasyon|oyun tasarım",  "sanat", ["dijital", "yaratıcı", "yazılım"], [2, 3, 5, 2, 1]),
    (r"sinema|televizyon|film",  "sanat", ["görsel", "anlatı", "saha"], [2, 4, 5, 3, 4]),
    (r"\bmüzik\b",               "sanat", ["ses", "performans", "icra"], [2, 4, 5, 3, 3]),
    (r"sahne sanat|tiyatro",     "sanat", ["performans", "oyun", "ifade"], [1, 5, 5, 3, 4]),
    (r"resim|heykel|seramik|cam",
        "sanat", ["plastik", "el becerisi", "yaratıcı"], [1, 2, 5, 2, 3]),
    (r"fotoğraf",                "sanat", ["görsel", "anlık", "saha"], [2, 3, 5, 2, 4]),
    (r"reklam|iletişim tasarım", "sanat", ["yaratıcı", "marka", "görsel"], [2, 4, 5, 2, 2]),
    (r"peyzaj",                  "sanat", ["doğa", "tasarım", "saha"], [3, 2, 4, 3, 4]),
    (r"şehir.*plan|bölge plan",  "sanat", ["şehir", "tasarım", "saha"], [4, 3, 4, 4, 3]),

    # Doğa Bilimleri
    (r"\bmatematik\b",           "doga", ["sayı", "soyutlama", "ispat"], [5, 1, 2, 5, 1]),
    (r"\bfizik\b",               "doga", ["evren", "deney", "matematik"], [5, 1, 2, 5, 3]),
    (r"\bkimya\b",               "doga", ["madde", "deney", "laboratuvar"], [4, 2, 2, 5, 3]),
    (r"\bbiyoloji\b|moleküler",  "doga", ["canlı", "deney", "araştırma"], [3, 2, 2, 5, 3]),
    (r"genetik|biyoteknoloji",   "doga", ["dna", "deney", "tıbbi"], [4, 2, 2, 5, 2]),
    (r"\bistatistik\b|aktüer",   "doga", ["veri", "olasılık", "matematik"], [5, 2, 1, 4, 1]),
    (r"astronomi",               "doga", ["evren", "fizik", "araştırma"], [5, 1, 2, 5, 2]),
    (r"meteoroloji",             "doga", ["hava", "fizik", "saha"], [4, 1, 1, 4, 4]),

    # Tarım/Doğa (Mühendislik dışı)
    (r"tarım|tarla|bahçe|bitki|toprak|bitkisel|tütün|zootekni|hayvansal",
        "doga", ["tarla", "doğa", "saha"], [3, 2, 1, 3, 5]),
    (r"yaban hayatı|ekoloji",    "doga", ["doğa", "araştırma", "saha"], [3, 1, 1, 5, 5]),
    (r"su ürünleri|balık|deniz bilim",
        "doga", ["deniz", "saha", "biyoloji"], [3, 2, 1, 4, 5]),

    # İletişim / Medya / Halkla İlişkiler (Sanat'ın bitişiği)
    (r"gazetecilik",             "sanat", ["haber", "araştırma", "yazma"], [2, 4, 4, 4, 3]),
    (r"halkla ilişkiler",        "sanat", ["kurumsal", "iletişim", "yazma"], [2, 5, 4, 2, 2]),
    (r"yeni medya|dijital med",  "sanat", ["dijital", "içerik", "yazılım"], [3, 4, 5, 2, 1]),
    (r"radyo|televizyon ve sinema|rts",
        "sanat", ["yayın", "görsel", "saha"], [2, 4, 5, 3, 4]),

    # Dil & Edebiyat
    (r"mütercim|tercüman|çeviri",
        "dil", ["dil", "kültür", "yazı"], [1, 3, 4, 4, 1]),
    (r"\b(ingiliz|alman|fransız|rus|italyan|ispanyol|çin|japon|kore|arap|fars|urdu|hint|moğol|kırgız|kazak|özbek|azeri|tatar|gürcü|ermeni|rum|yunan|bulgar|sırp|leh|polonya|macar|fin|isveç|norveç|hollanda|portekiz|latin|sümer|hitit|akad|sanskrit|ibrani|orta asya|çağdaş türk lehçeleri|türk dili|türkçe|türk edebiyat|türkoloji)",
        "dil", ["dil", "edebiyat", "kültür"], [1, 4, 4, 4, 1]),
    (r"karşılaştırmalı edebiyat|edebiyat",
        "dil", ["edebiyat", "okuma", "yazı"], [1, 3, 4, 5, 1]),
    (r"dilbilim",                "dil", ["dil", "yapı", "araştırma"], [3, 2, 2, 5, 1]),
    (r"linguist",                "dil", ["dil", "yapı", "araştırma"], [3, 2, 2, 5, 1]),

    # Spor
    (r"antrenörlük|beden eğitim|spor (yönetici|bilim|rekreasyon)|rekreasyon",
        "diger", ["spor", "saha", "performans"], [2, 4, 2, 2, 5]),

    # İlahiyat
    (r"ilahiyat|islam|din kültür|diyanet",
        "diger", ["din", "kültür", "felsefe"], [1, 4, 2, 4, 1]),

    # Bilişim/Teknoloji (Mühendislik dışı)
    (r"bilgisayar (program|teknoloji)|web tasarım",
        "muhendislik", ["yazılım", "uygulama", "teknik"], [4, 2, 3, 2, 1]),
    (r"yapay zeka mühendisl",    "muhendislik", ["yapay zeka", "veri", "matematik"], [5, 2, 3, 5, 1]),
    (r"yazılım geliştir",         "muhendislik", ["yazılım", "uygulama", "ekip"], [4, 3, 3, 2, 1]),

    # Ek kurallar (genelleyici)
    (r"veri bilim|bilgisayar bilim|veri analitik",
        "doga", ["veri", "matematik", "yazılım"], [5, 2, 2, 5, 1]),
    (r"bilgi güvenliği|siber güvenlik",
        "muhendislik", ["güvenlik", "ağ", "yazılım"], [5, 2, 2, 4, 1]),
    (r"adli bilim",              "sosyal_hukuk", ["adli", "kanıt", "kimya"], [4, 3, 1, 5, 4]),
    (r"dil ve konuşma terap",    "saglik", ["konuşma", "klinik", "çocuk"], [2, 5, 1, 3, 4]),
    (r"ergoterapi|iş ve uğraşı", "saglik", ["rehabilitasyon", "klinik", "saha"], [2, 5, 2, 3, 5]),
    (r"perfüzyon",               "saglik", ["klinik", "cerrahi", "teknoloji"], [3, 5, 1, 4, 4]),
    (r"gerontoloji",             "saglik", ["yaşlı", "klinik", "araştırma"], [2, 5, 1, 4, 3]),
    (r"biyokimya",               "doga", ["kimya", "biyoloji", "deney"], [4, 2, 1, 5, 2]),
    (r"nanoteknolog|nanobilim",  "doga", ["nano", "fizik", "araştırma"], [5, 1, 2, 5, 2]),
    (r"müzecilik",               "sanat", ["müze", "kültür", "araştırma"], [1, 3, 4, 5, 2]),
    (r"el sanatlar|geleneksel türk sanat|kuyumculuk",
        "sanat", ["zanaat", "yaratıcı", "el becerisi"], [1, 2, 5, 2, 3]),
    (r"medya|iletişim bilim|kültür ve iletişim",
        "sanat", ["medya", "iletişim", "kültür"], [2, 4, 4, 4, 2]),
    (r"sanat ve kültür yönet|sanat ve sosyal bilim",
        "sanat", ["sanat", "yönetim", "kültür"], [2, 4, 4, 3, 2]),
    (r"pilotaj|hava trafik",     "muhendislik", ["uçuş", "havacılık", "saha"], [4, 3, 2, 2, 5]),
    (r"denizcilik|gemi adamı",   "muhendislik", ["deniz", "saha", "teknik"], [3, 3, 1, 2, 5]),
    (r"gümrük",                  "iktisat", ["gümrük", "ticaret", "kamu"], [3, 3, 1, 2, 3]),
    (r"sermaye piyasa|borsa",    "iktisat", ["finans", "yatırım", "sayı"], [4, 3, 1, 4, 1]),
    (r"enerji yönetim",          "iktisat", ["enerji", "süreç", "iş"], [4, 3, 1, 3, 3]),
    (r"bilgi ve belge|kütüphane", "sosyal_hukuk", ["bilgi", "araştırma", "düzen"], [2, 3, 2, 5, 1]),
    (r"iş sağlığı",              "saglik", ["güvenlik", "sağlık", "saha"], [3, 4, 1, 3, 4]),
    (r"halkbilim|folklor",       "sosyal_hukuk", ["kültür", "araştırma", "saha"], [1, 3, 3, 5, 4]),
    (r"yönetim bilim",           "iktisat", ["yönetim", "iş", "analiz"], [3, 4, 2, 3, 2]),
    (r"\bekonometri\b",          "doga", ["ekonomi", "matematik", "veri"], [5, 2, 1, 5, 1]),
    (r"\bistatistik\b",          "doga", ["veri", "olasılık", "matematik"], [5, 1, 1, 5, 1]),
    (r"\bişletme\b|işletme yönet|girişim|elektronik ticaret",
        "iktisat", ["şirket", "yönetim", "iş"], [3, 4, 2, 3, 2]),
    (r"\biktisat\b|ekonomi",     "iktisat", ["piyasa", "para", "analiz"], [4, 3, 2, 4, 1]),
    (r"uluslararası ilişk|uluslararası ticaret",
        "sosyal_hukuk", ["politika", "yabancı dil", "analiz"], [2, 4, 2, 4, 2]),
    (r"halkla ilişkiler|tanıtım",
        "sanat", ["kurumsal", "iletişim", "yazma"], [2, 5, 4, 2, 2]),
    (r"görsel iletişim|iletişim tasarım|iletişim ve tasarım",
        "sanat", ["görsel", "yaratıcı", "yazılım"], [2, 4, 5, 2, 1]),
    (r"insan kaynak",            "iktisat", ["insan", "yönetim", "psikoloji"], [2, 5, 2, 3, 2]),
    (r"spor yöneticili|rekreasyon yönet",
        "iktisat", ["spor", "yönetim", "iş"], [2, 4, 2, 2, 4]),
    (r"islami ilim|ilahiyat",    "sosyal_hukuk", ["din", "kültür", "felsefe"], [1, 4, 2, 5, 1]),
]


def _tr_lower(s: str) -> str:
    """Türkçe güvenli lowercase (İ→i, I→ı, sonra .lower())."""
    return s.replace("İ", "i").replace("I", "ı").lower()


def _categorize(name: str) -> dict:
    """Bölüm adını kategoriye + etikete + kişilik vektörüne ata."""
    name_norm = _tr_lower(name).strip()
    for pat, cat, tags, axes in _RULES:
        if re.search(pat, name_norm):
            override = axes if axes is not None else CATEGORIES[cat]["default"]
            return {
                "category": cat,
                "tags": tags,
                "axes": override,
            }
    return {
        "category": "diger",
        "tags": ["genel"],
        "axes": CATEGORIES["diger"]["default"],
    }


@lru_cache(maxsize=1)
def get_taxonomy() -> dict:
    """358 lisans bölüm grubunun taksonomi sözlüğü.

    Şema:
    {
      "categories": {<cat_id>: {"label": str, "emoji": str}, ...},
      "departments": [
        {"name": "Bilgisayar Mühendisliği", "category": "muhendislik",
         "tags": [...], "axes": [m,h,c,r,f], "program_count": 87},
        ...
      ]
    }
    """
    settings = get_settings()
    proc = Path(settings.project_root) / "data" / "processed"
    departments = json.load(open(proc / "departments.json", encoding="utf-8"))

    # Benzersiz group_name'leri ve program sayılarını topla
    counts: dict[str, int] = {}
    for d in departments:
        gn = d.get("group_name") or d.get("name", "")
        if not gn:
            continue
        counts[gn] = counts.get(gn, 0) + 1

    items: list[dict] = []
    for name, count in sorted(counts.items(), key=lambda x: -x[1]):
        cat_info = _categorize(name)
        items.append({
            "name": name,
            "category": cat_info["category"],
            "tags": cat_info["tags"],
            "axes": cat_info["axes"],
            "program_count": count,
        })

    return {
        "categories": {
            k: {"label": v["label"], "emoji": v["emoji"]}
            for k, v in CATEGORIES.items()
        },
        "departments": items,
    }


def axes_to_label(axes: list[int]) -> str:
    """5-boyutlu eksenden insan dostu özet."""
    labels = ["matematik", "insan", "yaratıcı", "araştırma", "saha"]
    pairs = sorted(zip(labels, axes), key=lambda x: -x[1])
    return " · ".join(p[0] for p in pairs[:2])
