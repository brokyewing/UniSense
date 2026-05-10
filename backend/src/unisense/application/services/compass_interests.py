"""İlgi etiketleri (interest tags) — kullanıcı bu pill'leri seçer, biz bölüm öneririz.

Kategori başına curated etiket havuzu + her bölümü bu havuzdan etiketleyen
regex kural seti. Etiketler bölüm adı DEĞİL — kullanıcı "tıp" yazmak yerine
"hasta bakımı, klinik, anatomi" seçer ve birden fazla bölüm önerilir.
"""
from __future__ import annotations

import re
from functools import lru_cache

from unisense.application.services.compass_taxonomy import (
    CATEGORIES,
    _tr_lower,
    get_taxonomy,
)


# === Kategori başına curated ilgi havuzu ===
# Sıra önemli — UI'da bu sırada gösterilir.
CATEGORY_INTERESTS: dict[str, list[str]] = {
    "muhendislik": [
        "yazılım", "algoritma", "yapay zeka", "veri",
        "matematik", "fizik", "elektronik", "robotik",
        "mekanik", "imalat", "tasarım", "üretim",
        "havacılık", "uzay", "otomotiv", "biyomedikal",
        "kimya", "enerji", "inşaat ve yapı", "deniz ve gemi",
        "jeoloji ve maden", "malzeme", "ağ ve sistem", "güvenlik",
        "süreç optimizasyonu", "saha çalışması",
    ],
    "saglik": [
        "hasta bakımı", "klinik çalışma", "tedavi", "ilaç",
        "anatomi ve vücut", "cerrahi", "acil durum", "rehabilitasyon",
        "doğum ve anne-bebek", "çocuk sağlığı", "yaşlı bakımı",
        "ağız ve diş sağlığı", "konuşma ve işitme", "ruh sağlığı",
        "diyet ve beslenme", "veteriner ve hayvan", "halk sağlığı",
        "hastane yönetimi", "ekip çalışması", "şefkat ve empati",
        "kimya ve biyokimya", "deney ve laboratuvar",
    ],
    "sosyal_hukuk": [
        "adalet", "yasalar", "müzakere", "okuma ve yazma",
        "politika", "kamu yönetimi", "uluslararası ilişkiler", "diplomasi",
        "psikoloji", "ruh sağlığı", "toplum analizi", "sosyal yardım",
        "felsefe", "kavramsal düşünme", "tarih", "arkeoloji",
        "coğrafya", "kültür", "araştırma", "saha çalışması",
        "bilgi ve belge",
    ],
    "iktisat": [
        "para ve finans", "ekonomi analizi", "şirket yönetimi", "girişimcilik",
        "muhasebe", "vergi ve maliye", "bankacılık", "sigorta ve risk",
        "borsa ve yatırım", "satış ve pazarlama", "marka", "reklam",
        "lojistik ve taşıma", "uluslararası ticaret", "insan kaynakları",
        "turizm", "yemek ve gastronomi", "müşteri ilişkileri",
        "iletişim", "matematik ve sayı",
    ],
    "sanat": [
        "yaratıcılık", "estetik", "tasarım", "görsel sanatlar",
        "resim", "heykel ve plastik", "fotoğraf", "grafik tasarım",
        "müzik", "tiyatro ve sahne", "sinema ve film", "animasyon ve oyun",
        "moda", "iç mekân", "mimari", "endüstriyel ürün",
        "performans", "anlatı ve yazma", "dijital medya", "iletişim",
        "el becerisi ve zanaat", "kültür",
    ],
    "doga": [
        "matematik ve sayı", "fizik ve evren", "kimya ve madde", "biyoloji ve canlı",
        "genetik ve dna", "deney ve laboratuvar", "veri ve istatistik", "araştırma",
        "tarım ve tarla", "doğa ve ekoloji", "deniz ve su", "bitki ve hayvan",
        "uzay ve astronomi", "nanoteknoloji", "saha çalışması",
    ],
    "egitim": [
        "çocuk gelişimi", "okul öncesi", "ilkokul ve sınıf öğretmenliği",
        "matematik öğretimi", "fen öğretimi", "dil öğretimi",
        "yabancı dil öğretimi", "Türk dili öğretimi",
        "özel eğitim", "rehberlik ve danışmanlık", "psikolojik destek",
        "spor ve beden eğitimi", "müzik ve sanat öğretimi",
        "iletişim", "ekip çalışması",
    ],
    "dil": [
        "yabancı dil", "edebiyat", "çeviri ve mütercimlik",
        "Türk dili", "doğu dilleri", "batı dilleri", "slav dilleri",
        "uzak doğu dilleri", "ortadoğu dilleri",
        "dilbilim", "yazma ve okuma", "kültür", "tarih ve geçmiş",
    ],
    "diger": [
        "spor", "performans", "din ve maneviyat", "felsefe", "kültür",
        "havacılık", "denizcilik",
    ],
}


# === Bölüm adından ilgi seçimi ===
# (regex pattern, [interest_id, ...]) — interest_id, CATEGORY_INTERESTS değerlerinden biri olmalı
_INTEREST_RULES: list[tuple[str, list[str]]] = [
    # === SAĞLIK ===
    (r"\btıp\b", ["hasta bakımı", "klinik çalışma", "tedavi", "anatomi ve vücut", "cerrahi", "ekip çalışması", "şefkat ve empati"]),
    (r"hemşirelik", ["hasta bakımı", "klinik çalışma", "şefkat ve empati", "ekip çalışması"]),
    (r"diş hekim", ["ağız ve diş sağlığı", "klinik çalışma", "el becerisi ve zanaat"]),
    (r"eczacılık", ["ilaç", "kimya ve biyokimya", "klinik çalışma"]),
    (r"ebelik", ["doğum ve anne-bebek", "klinik çalışma", "şefkat ve empati"]),
    (r"fizyoterapi", ["rehabilitasyon", "anatomi ve vücut", "klinik çalışma"]),
    (r"beslenme", ["diyet ve beslenme", "kimya ve biyokimya", "klinik çalışma"]),
    (r"odyoloji", ["konuşma ve işitme", "klinik çalışma"]),
    (r"veteriner", ["veteriner ve hayvan", "klinik çalışma"]),
    (r"sağlık yönetim|hastane yönet", ["hastane yönetimi", "ekip çalışması"]),
    (r"acil yardım|paramedik", ["acil durum", "klinik çalışma"]),
    (r"sağlık (bilim|teknik|kurum|hizmet)", ["halk sağlığı", "klinik çalışma"]),
    (r"sağlık fizik|biyofizik", ["fizik ve evren", "klinik çalışma", "araştırma"]),
    (r"diyaliz|protez|ortez|cerrahi tek", ["klinik çalışma", "anatomi ve vücut"]),
    (r"dil ve konuşma terap", ["konuşma ve işitme", "klinik çalışma", "çocuk sağlığı"]),
    (r"ergoterapi|iş ve uğraşı", ["rehabilitasyon", "klinik çalışma"]),
    (r"perfüzyon", ["cerrahi", "klinik çalışma"]),
    (r"gerontoloji", ["yaşlı bakımı", "klinik çalışma"]),
    (r"iş sağlığı", ["halk sağlığı", "ekip çalışması"]),

    # === MÜHENDİSLİK ===
    (r"bilgisayar mühendis|yazılım mühendis", ["yazılım", "algoritma", "matematik", "veri"]),
    (r"yapay zeka", ["yapay zeka", "yazılım", "veri", "matematik"]),
    (r"veri (mühendis|analitik)", ["veri", "yazılım", "matematik"]),
    (r"bilişim sistem|yönetim bilişim", ["yazılım", "veri", "ağ ve sistem"]),
    (r"bilgisayar (program|teknoloji)|web tasarım", ["yazılım", "tasarım"]),
    (r"yazılım geliştir", ["yazılım", "ekip çalışması"]),
    (r"siber güvenlik|bilgi güvenliği", ["güvenlik", "ağ ve sistem", "yazılım"]),
    (r"elektrik(-elektronik)? mühendis|elektronik", ["elektronik", "fizik", "matematik"]),
    (r"makine mühendis", ["mekanik", "imalat", "fizik"]),
    (r"mekatronik", ["mekanik", "elektronik", "robotik"]),
    (r"endüstri mühendis|sistem mühendis", ["süreç optimizasyonu", "matematik", "üretim"]),
    (r"inşaat mühendis|yapı mühendis", ["inşaat ve yapı", "saha çalışması", "fizik"]),
    (r"kimya mühendis", ["kimya", "imalat", "süreç optimizasyonu"]),
    (r"biyomedikal mühendis|biyomühendis", ["biyomedikal", "elektronik", "kimya"]),
    (r"havacılık|uçak", ["havacılık", "fizik", "matematik"]),
    (r"uzay", ["uzay", "fizik", "matematik"]),
    (r"otomotiv mühendis", ["otomotiv", "mekanik", "imalat"]),
    (r"gıda mühendis", ["kimya", "imalat", "üretim"]),
    (r"çevre mühendis", ["kimya", "saha çalışması", "doğa ve ekoloji"]),
    (r"jeoloji mühendis|petrol|maden mühendis|jeofizik", ["jeoloji ve maden", "saha çalışması", "fizik"]),
    (r"metal(urji)? mühendis|malzeme", ["malzeme", "kimya", "imalat"]),
    (r"tekstil mühendis", ["üretim", "tasarım", "imalat"]),
    (r"orman (endüstri )?mühendis", ["doğa ve ekoloji", "saha çalışması"]),
    (r"harita mühendis|geomatik|jeodezi", ["saha çalışması", "matematik"]),
    (r"deniz (taşımacılığ|ulaştırm|teknoloji|işletme|harita)|gemi", ["deniz ve gemi", "saha çalışması"]),
    (r"nükleer", ["fizik", "enerji"]),
    (r"enerji sistem", ["enerji", "fizik"]),
    (r"endüstri sistemleri|imalat mühendis", ["üretim", "imalat", "süreç optimizasyonu"]),
    (r"mühendis", ["matematik", "fizik"]),  # generic mühendislik fallback

    # === SOSYAL & HUKUK ===
    (r"\bhukuk\b", ["adalet", "yasalar", "müzakere", "okuma ve yazma"]),
    (r"siyaset|kamu yönet|uluslararası ilişk|diplomas|küresel siyaset", ["politika", "kamu yönetimi", "uluslararası ilişkiler"]),
    (r"psikoloji", ["psikoloji", "ruh sağlığı", "araştırma"]),
    (r"sosyoloji|antropoloji", ["toplum analizi", "araştırma"]),
    (r"felsefe", ["felsefe", "kavramsal düşünme", "okuma ve yazma"]),
    (r"\btarih\b", ["tarih", "araştırma", "okuma ve yazma"]),
    (r"sanat tarihi", ["tarih", "görsel sanatlar", "araştırma"]),
    (r"coğrafya", ["coğrafya", "saha çalışması"]),
    (r"arkeoloji|kültür varlık", ["arkeoloji", "tarih", "saha çalışması"]),
    (r"sosyal hizmet", ["sosyal yardım", "psikoloji"]),
    (r"adalet|ceza infaz", ["adalet", "kamu yönetimi"]),
    (r"halkbilim|folklor", ["kültür", "tarih"]),
    (r"bilgi ve belge|kütüphane", ["bilgi ve belge", "araştırma"]),
    (r"adli bilim", ["adalet", "deney ve laboratuvar"]),

    # === EĞİTİM ===
    (r"okul öncesi", ["okul öncesi", "çocuk gelişimi"]),
    (r"sınıf öğretmen", ["ilkokul ve sınıf öğretmenliği", "çocuk gelişimi"]),
    (r"matematik öğretmen", ["matematik öğretimi"]),
    (r"fen.*öğretmen|kimya öğretmen|fizik öğretmen|biyoloji öğretmen", ["fen öğretimi"]),
    (r"türkçe öğretmen|türk dili.*öğretmen", ["dil öğretimi", "Türk dili öğretimi"]),
    (r"ingilizce öğretmen|alman.*öğretmen|fransız.*öğretmen|arap.*öğretmen", ["dil öğretimi", "yabancı dil öğretimi"]),
    (r"sosyal bilgiler öğretmen", ["fen öğretimi", "ekip çalışması"]),
    (r"özel eğitim", ["özel eğitim"]),
    (r"rehberlik|psikolojik dan", ["rehberlik ve danışmanlık", "psikolojik destek"]),
    (r"çocuk gelişim", ["çocuk gelişimi"]),
    (r"beden eğit.*öğretmen", ["spor ve beden eğitimi"]),
    (r"müzik öğretmen|resim öğretmen", ["müzik ve sanat öğretimi"]),
    (r"öğretmenliği|öğretmen|eğitim (program|yöneticilik|bilim)", ["iletişim", "ekip çalışması"]),

    # === İKTİSAT ===
    (r"\biktisat\b|ekonomi", ["ekonomi analizi", "para ve finans"]),
    (r"\bişletme\b|işletme yönet|girişim|elektronik ticaret", ["şirket yönetimi", "girişimcilik"]),
    (r"maliye", ["vergi ve maliye", "muhasebe"]),
    (r"muhasebe|finans", ["muhasebe", "para ve finans"]),
    (r"bankacılık", ["bankacılık", "para ve finans"]),
    (r"sigortacılık|aktüer", ["sigorta ve risk", "matematik ve sayı"]),
    (r"pazarlama", ["satış ve pazarlama", "marka"]),
    (r"reklam", ["reklam", "marka", "iletişim"]),
    (r"lojistik|tedarik", ["lojistik ve taşıma"]),
    (r"insan kaynak", ["insan kaynakları", "psikoloji"]),
    (r"turizm", ["turizm", "müşteri ilişkileri"]),
    (r"gastronomi|aşçılık|yiyecek|otel", ["yemek ve gastronomi", "müşteri ilişkileri"]),
    (r"emlak|gayrimenkul", ["satış ve pazarlama"]),
    (r"uluslararası ticaret|dış ticaret|gümrük", ["uluslararası ticaret", "ekonomi analizi"]),
    (r"sermaye piyasa|borsa", ["borsa ve yatırım", "para ve finans"]),
    (r"halkla ilişkiler|tanıtım", ["iletişim", "marka"]),
    (r"yönetim bilim", ["şirket yönetimi"]),
    (r"spor yöneticili|rekreasyon yönet", ["şirket yönetimi", "spor"]),
    (r"enerji yönetim", ["şirket yönetimi"]),

    # === SANAT ===
    (r"mimar(lık)?", ["mimari", "tasarım", "iç mekân"]),
    (r"\biç mimar", ["iç mekân", "tasarım", "mimari"]),
    (r"endüstriyel tasarım", ["endüstriyel ürün", "tasarım"]),
    (r"grafik (tasarım|sanat)|görsel iletişim|iletişim tasarım|iletişim ve tasarım", ["grafik tasarım", "görsel sanatlar", "tasarım"]),
    (r"moda tasarım", ["moda", "tasarım"]),
    (r"animasyon|oyun tasarım", ["animasyon ve oyun", "dijital medya", "tasarım"]),
    (r"sinema|televizyon|film|rts", ["sinema ve film", "anlatı ve yazma", "performans"]),
    (r"\bmüzik\b", ["müzik", "performans"]),
    (r"sahne sanat|tiyatro", ["tiyatro ve sahne", "performans"]),
    (r"resim|heykel", ["resim", "görsel sanatlar", "el becerisi ve zanaat"]),
    (r"seramik|cam", ["heykel ve plastik", "el becerisi ve zanaat"]),
    (r"fotoğraf", ["fotoğraf", "görsel sanatlar"]),
    (r"peyzaj", ["tasarım", "doğa ve ekoloji"]),
    (r"şehir.*plan", ["mimari", "tasarım"]),
    (r"gazetecilik", ["anlatı ve yazma", "iletişim"]),
    (r"yeni medya|dijital med|medya|iletişim bilim", ["dijital medya", "iletişim"]),
    (r"el sanatlar|geleneksel|kuyumculuk", ["el becerisi ve zanaat", "yaratıcılık"]),
    (r"müzecilik", ["kültür", "araştırma"]),
    (r"sanat ve kültür yönet|sanat ve sosyal bilim", ["yaratıcılık", "şirket yönetimi"]),

    # === DOĞA BİLİMLERİ ===
    (r"\bmatematik\b", ["matematik ve sayı", "araştırma"]),
    (r"\bfizik\b", ["fizik ve evren", "deney ve laboratuvar"]),
    (r"\bkimya\b", ["kimya ve madde", "deney ve laboratuvar"]),
    (r"\bbiyoloji\b|moleküler", ["biyoloji ve canlı", "deney ve laboratuvar"]),
    (r"genetik|biyoteknoloji", ["genetik ve dna", "deney ve laboratuvar"]),
    (r"\bistatistik\b", ["veri ve istatistik", "matematik ve sayı"]),
    (r"\bekonometri\b", ["veri ve istatistik", "matematik ve sayı"]),
    (r"astronomi", ["uzay ve astronomi", "fizik ve evren"]),
    (r"nanoteknolog|nanobilim", ["nanoteknoloji", "fizik ve evren"]),
    (r"meteoroloji", ["fizik ve evren", "saha çalışması"]),
    (r"tarım|tarla|bahçe|bitki|toprak|tütün|zootekni|hayvansal", ["tarım ve tarla", "bitki ve hayvan", "saha çalışması"]),
    (r"yaban hayatı|ekoloji", ["doğa ve ekoloji", "saha çalışması"]),
    (r"su ürünleri|balık|deniz bilim", ["deniz ve su", "saha çalışması"]),
    (r"bilgisayar bilim|veri bilim", ["veri ve istatistik", "matematik ve sayı"]),
    (r"biyokimya", ["kimya ve madde", "deney ve laboratuvar"]),

    # === DİL ===
    (r"mütercim|tercüman|çeviri", ["çeviri ve mütercimlik", "yabancı dil", "kültür"]),
    (r"\bingiliz", ["batı dilleri", "yabancı dil", "edebiyat"]),
    (r"\b(alman|fransız|italyan|ispanyol|hollanda|portekiz|latin)", ["batı dilleri", "yabancı dil", "edebiyat"]),
    (r"\b(rus|leh|polonya|çek|sırp|bulgar|ukrayn)", ["slav dilleri", "yabancı dil", "edebiyat"]),
    (r"\b(çin|japon|kore)", ["uzak doğu dilleri", "yabancı dil", "kültür"]),
    (r"\b(arap|fars|urdu|ibrani|sümer|hitit|akad)", ["ortadoğu dilleri", "yabancı dil", "tarih ve geçmiş"]),
    (r"\b(hint|sanskrit|moğol|kırgız|kazak|özbek|tatar|azeri|gürcü|ermeni|rum|yunan|fin|isveç|norveç|macar)", ["doğu dilleri", "yabancı dil", "kültür"]),
    (r"türk dili|türkçe|türk edebiyat|türkoloji|çağdaş türk lehçeleri", ["Türk dili", "edebiyat", "yazma ve okuma"]),
    (r"karşılaştırmalı edebiyat|edebiyat", ["edebiyat", "yazma ve okuma"]),
    (r"dilbilim|linguist", ["dilbilim", "araştırma"]),

    # === DİĞER ===
    (r"antrenörlük|beden eğit|spor (yönetici|bilim|rekreasyon)|rekreasyon|egzersiz", ["spor", "performans"]),
    (r"ilahiyat|islam|din kültür|diyanet|islami ilim", ["din ve maneviyat", "felsefe", "kültür"]),
    (r"pilotaj|hava trafik", ["havacılık"]),
    (r"denizcilik|gemi adamı", ["denizcilik"]),
]


def _get_interests(name: str, category: str) -> list[str]:
    """Bölüm adından ilgi alanı listesi (CATEGORY_INTERESTS havuzundan subset)."""
    name_norm = _tr_lower(name).strip()
    matched: list[str] = []
    for pat, interests in _INTEREST_RULES:
        if re.search(pat, name_norm):
            for iv in interests:
                if iv not in matched:
                    matched.append(iv)
    if matched:
        return matched
    # Hiçbir kural eşleşmediyse kategori havuzundan ilk 2'sini ver
    pool = CATEGORY_INTERESTS.get(category, [])
    return pool[:2] if pool else []


@lru_cache(maxsize=1)
def get_interests_taxonomy() -> dict:
    """UI için: kategori başına ilgi pill'leri + her pill kaç bölümü temsil ediyor.

    Şema:
    {
      "categories": [
        {
          "id": "saglik", "label": "Sağlık", "emoji": "🏥",
          "interests": [
            {"id": "hasta bakımı", "department_count": 5},
            {"id": "klinik çalışma", "department_count": 27},
            ...
          ]
        }, ...
      ]
    }
    """
    tax = get_taxonomy()
    # bölüm → ilgileri ön-hesapla
    dept_interests: dict[str, list[str]] = {
        d["name"]: _get_interests(d["name"], d["category"]) for d in tax["departments"]
    }

    # Kategori başına ilgi → bölüm sayısı
    by_cat: dict[str, dict[str, int]] = {}
    for d in tax["departments"]:
        cat = d["category"]
        by_cat.setdefault(cat, {})
        for iv in dept_interests[d["name"]]:
            by_cat[cat][iv] = by_cat[cat].get(iv, 0) + d["program_count"]

    out_categories = []
    for cat_id, cat_meta in CATEGORIES.items():
        pool = CATEGORY_INTERESTS.get(cat_id, [])
        counts = by_cat.get(cat_id, {})
        # Havuzdaki sırayı koru, sayısı 0 olanları da ekle ama kullanılanları öne al
        items = []
        # Önce kullanılanları havuz sırasına göre
        for iv in pool:
            if iv in counts:
                items.append({"id": iv, "department_count": counts[iv]})
        # Sonra havuzdaki kullanılmayanları da ekle (sayı=0, opsiyonel)
        if not items:
            continue
        out_categories.append({
            "id": cat_id,
            "label": cat_meta["label"],
            "emoji": cat_meta["emoji"],
            "interests": items,
        })

    return {"categories": out_categories, "_dept_interests": dept_interests}


def get_dept_to_interests() -> dict[str, list[str]]:
    """Public: bölüm → ilgi listesi (matching servisi için)."""
    return get_interests_taxonomy()["_dept_interests"]
