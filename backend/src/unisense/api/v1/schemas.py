"""API v1 — request/response DTOs."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator

from unisense.domain.enums import ScoreType


class ChatTurn(BaseModel):
    role: str = Field(..., pattern="^(user|bot|assistant)$")
    text: str = Field(..., max_length=4000)


class UserExamContext(BaseModel):
    """Profilden gelen sınav puanları ve çalışma hafızası — /ask bağlamında kullanılır."""
    exam_track: str | None = Field(None, pattern="^(YKS|DGS|KPSS|LGS|TUS|DUS|AGS)$")
    # YKS: "puanıma göre X kazanabilir miyim" için profildeki puan/sıra/tür
    yks_puan: float | None = Field(None, ge=0, le=600)
    yks_turu: str | None = Field(None, pattern="^(SAY|EA|SÖZ|DİL|TYT)$")
    yks_sira: int | None = Field(None, ge=1, le=3_500_000)
    kpss_puan: float | None = Field(None, ge=0, le=120)
    kpss_duzey: str | None = Field(None, pattern="^(lisans|önlisans|ortaöğretim)$")
    dgs_puan: float | None = Field(None, ge=0, le=600)
    dgs_turu: str | None = Field(None, pattern="^(SAY|EA|SÖZ)$")
    # Tüm sınav profili — chat'e tek blok olarak iletilir (KENDİ verisi)
    tus_puan: float | None = Field(None, ge=0, le=100)
    dus_puan: float | None = Field(None, ge=0, le=100)
    lgs_yuzdelik: float | None = Field(None, ge=0, le=100)
    ags_net: float | None = Field(None, ge=0, le=120)
    tercih_sehirler: list[str] | None = Field(None, max_length=10)
    tercih_uni_turu: str | None = Field(None, max_length=20)
    # Çalışma ilerlemesi (Konu Takibi + Çalışmalarım + Pano + Planım + Notlar + Pusula)
    calisma_kalan_konu: int | None = Field(None, ge=0, le=5000)
    calisma_toplam_konu: int | None = Field(None, ge=0, le=5000)
    calisma_eksik_konular: list[str] | None = Field(None, max_length=8)
    calisma_zayif: list[str] | None = Field(None, max_length=6)
    gunluk_soru_hedef: int | None = Field(None, ge=0, le=2000)
    bugun_cozulen_soru: int | None = Field(None, ge=0, le=5000)
    ilgi_alanlari: list[str] | None = Field(None, max_length=15)
    son_denemeler: list[str] | None = Field(None, max_length=5)
    bekleyen_gorevler: list[str] | None = Field(None, max_length=8)
    son_notlar: list[str] | None = Field(None, max_length=5)
    tercih_ozeti: list[str] | None = Field(None, max_length=10)
    toplam_calisma_dk: int | None = Field(None, ge=0, le=500_000)
    seri_gun: int | None = Field(None, ge=0, le=5_000)

    @field_validator("tercih_sehirler", mode="before")
    @classmethod
    def _validate_sehirler(cls, v):
        if v is None:
            return None
        if not isinstance(v, list):
            raise TypeError("tercih_sehirler liste olmalıdır")
        out = []
        for item in v:
            s = str(item or "").strip()
            if not s:
                raise ValueError("Şehir adı boş olamaz")
            if len(s) > 50:
                raise ValueError("Şehir adı 50 karakteri aşamaz")
            out.append(s)
        return out

    @field_validator(
        "ilgi_alanlari",
        "son_denemeler",
        "bekleyen_gorevler",
        "son_notlar",
        "tercih_ozeti",
        "calisma_eksik_konular",
        "calisma_zayif",
        mode="before",
    )
    @classmethod
    def _validate_memory_lists(cls, v):
        if v is None:
            return None
        if not isinstance(v, list):
            raise TypeError("Liste alanı dizi olmalıdır")
        out = []
        for item in v:
            s = str(item or "").strip()
            if s:
                out.append(s[:180])
        return out


class AskRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500)
    top_k: int = Field(default=12, ge=1, le=30)
    # Son N tur (user+bot) — multi-turn chat için. Boş ise tek-tur sorgu.
    history: list[ChatTurn] = Field(default_factory=list, max_length=10)
    # LLM seçimi: şu an sadece "gemini" — ileride yeni model gelirse genişletilir
    model_preference: str = Field(default="gemini")
    # Girişli kullanıcının profil sınav puanları (opsiyonel)
    user_context: UserExamContext | None = None


class ModelInfo(BaseModel):
    id: str
    name: str
    available: bool
    description: str


class ModelsResponse(BaseModel):
    models: list[ModelInfo]


class DocResponse(BaseModel):
    content: str
    source: str
    source_url: str = ""
    university_code: str = ""
    department_code: str = ""
    year: int | None = None
    score_type: str = ""
    distance: float | None = None
    # Frontend'in "Pusulaya Ekle" / "Tercihe Ekle" butonları için ek alanlar
    department_name: str = ""
    department_group_name: str = ""
    university_name: str = ""
    city: str = ""
    last_year_base_rank: int | None = None
    last_year_base_score: float | None = None
    quota: int | None = None


class CoachActionSchema(BaseModel):
    type: Literal[
        "set_daily_goal",
        "create_study_plan",
        "log_questions",
        "add_task",
        "mark_topic_done",
        "add_preference",
        "add_deneme",
        "complete_task",
        "add_note",
        "log_study_time",
        "update_profile",
        "remove_preference",
        "reorder_preferences",
        "delete_task",
        "reschedule_task",
        "complete_note",
        "delete_note",
        "unmark_topic_done",
        "open_compare",
    ]
    label: str = Field(..., max_length=160)
    auto_apply: bool = True
    payload: dict = Field(default_factory=dict)


class PreferenceResolveRequest(BaseModel):
    sinav: Literal["YKS", "KPSS", "DGS", "TUS", "DUS", "LGS"] = "YKS"
    codes: list[str] = Field(default_factory=list, max_length=10)
    query: str | None = Field(None, max_length=120)


class PreferenceResolveResponse(BaseModel):
    sinav: str
    items: list[dict] = Field(default_factory=list)


class AskResponse(BaseModel):
    query: str
    text: str
    docs: list[DocResponse]
    total_latency_ms: int | None = None
    actions: list[CoachActionSchema] = Field(default_factory=list)


class HealthResponse(BaseModel):
    status: str
    version: str
    chunks_count: int | None = None


class StudentProfileRequest(BaseModel):
    score_type: ScoreType
    score: float | None = Field(None, ge=0, le=600)
    rank: int | None = Field(None, ge=1)
    # max_length: aşırı-boyutlu gövde DoS'unu engelle (81 il, birkaç tür/dil
    # yeter — sınırsız liste 512MB instance'ı OOM'a sürükleyebilir)
    preferred_cities: list[str] = Field(default_factory=list, max_length=81)
    preferred_uni_types: list[str] = Field(default_factory=list, max_length=10)
    preferred_languages: list[str] = Field(default_factory=list, max_length=10)
    preferred_departments: list[str] = Field(default_factory=list, max_length=50)


class SiralamaResponse(BaseModel):
    """Hesap makinesi: yerleştirme puanından tahmini başarı sırası."""
    puan: float
    tur: str
    tahmini_sira: int
    # "alt"/"ust" = puan veri aralığının dışında (uçta tahmin daha zayıf); None = aralık içi
    sinir: str | None = None


class RecommendationItem(BaseModel):
    department_code: str
    university_code: str
    department_name: str
    university_name: str
    city: str
    fit_score: float
    safety_level: str
    reason: str = ""
    placement_probability: float | None = None
    last_year_base_rank: int | None = None
    last_year_base_score: float | None = None
    scholarship: str = ""
    education_language: str = ""
    duration_years: int | None = None
    osym_conditions: list[str] = []
    trend: list[dict] = []


class RecommendResponse(BaseModel):
    safe: list[RecommendationItem]
    target: list[RecommendationItem]
    reach: list[RecommendationItem]
    notes: str = ""


class UniversityResponse(BaseModel):
    code: str
    name: str
    short_name: str = ""
    type: str
    city: str
    description: str = ""
    urap_rank_tr: int | None = None
    qs_rank_world: int | None = None


class DepartmentResponse(BaseModel):
    code: str
    name: str
    university_code: str
    score_type: str
    education_level: str
    education_language: str
    duration_years: int = 4
    quota: int | None = None
    description: str = ""


# === Compass (İlgi Pusulası) ===

class CompassDepartmentItem(BaseModel):
    name: str
    tags: list[str]
    program_count: int
    axis_summary: str = ""


class CompassCategoryItem(BaseModel):
    id: str
    label: str
    emoji: str
    departments: list[CompassDepartmentItem]


class CompassTaxonomyResponse(BaseModel):
    categories: list[CompassCategoryItem]


class CompassMatchItem(BaseModel):
    name: str
    category: str
    category_label: str
    category_emoji: str
    tags: list[str]
    axis_summary: str
    program_count: int
    match_score: float
    matched_interests: list[str] = Field(default_factory=list)
    matched_count: int = 0


class CompassInterestPill(BaseModel):
    id: str
    department_count: int


class CompassInterestCategory(BaseModel):
    id: str
    label: str
    emoji: str
    interests: list[CompassInterestPill]


class CompassInterestsTaxonomyResponse(BaseModel):
    categories: list[CompassInterestCategory]


class CompassInterestsRequest(BaseModel):
    interests: list[str] = Field(..., min_length=1, max_length=30)
    top_k: int = Field(default=15, ge=3, le=30)


# === Program Lookup (Tercih listesi için sıra/taban/kontenjan eksiğini doldur) ===

class ProgramLookupRequest(BaseModel):
    codes: list[str] = Field(..., min_length=1, max_length=24)


class ProgramLookupItem(BaseModel):
    department_code: str
    found: bool
    department_name: str = ""
    department_group_name: str = ""
    university_code: str = ""
    university_name: str = ""
    city: str = ""
    score_type: str = ""
    education_language: str = ""
    scholarship: str = ""
    last_year_base_rank: int | None = None
    last_year_base_score: float | None = None
    quota: int | None = None


class ProgramLookupResponse(BaseModel):
    programs: list[ProgramLookupItem]


# === KPSS Kadro Arama ===

class KpssKadroRequest(BaseModel):
    bolum: str = Field(default="", max_length=120)
    puan: float | None = Field(None, ge=0, le=120)
    duzey: str | None = Field(None, pattern="^(lisans|önlisans|ortaöğretim)$")
    il: str | None = Field(None, max_length=40)          # tekil (geriye uyum)
    iller: list[str] | None = Field(None, max_length=20)  # çoklu şehir seçimi
    limit: int = Field(default=30, ge=1, le=100)


class KpssKadroItem(BaseModel):
    kadro_kodu: str
    kurum: str
    unvan: str
    il: str = ""
    duzey: str
    puan_turu: str
    kontenjan: int | None = None
    eslesme: str = ""
    gecmis_taban: float | None = None
    ozel_kosullar: list[str] = []
    nitelik_aciklama: str = ""


class KpssKadroResponse(BaseModel):
    donem: str
    total: int
    items: list[KpssKadroItem]
    uyari: str = ""


# === DGS Program Arama ===

class DgsProgramRequest(BaseModel):
    puan_turu: str = Field(default="SAY", pattern="^(SAY|EA|SÖZ|SOZ|say|ea|söz|soz)$")
    puan: float | None = Field(None, ge=0, le=600)
    bolum: str = Field(default="", max_length=120)
    il: str | None = Field(None, max_length=40)
    uni_turu: str | None = Field(None, max_length=20)  # Devlet | Vakıf | all
    oneri: bool = False  # true → tabanı puanın 10 puana kadar üstünde olanlar da döner (üst seviye)
    limit: int = Field(default=30, ge=1, le=100)


class DgsProgramItem(BaseModel):
    department_code: str
    program_adi: str
    university_name: str = ""
    city: str = ""
    puan_turu: str
    kontenjan: int | None = None
    yerlesen: int | None = None
    min_puan: float | None = None
    yil: int | None = None


class DgsProgramResponse(BaseModel):
    total: int
    items: list[DgsProgramItem]
    uyari: str = ""


class DgsGecisRequest(BaseModel):
    onlisans: str = Field(default="", max_length=120)


class DgsGecisGrup(BaseModel):
    alan: str
    eslesen_programlar: list[str] = []
    lisans: list[dict] = []


class DgsGecisResponse(BaseModel):
    programlar: list[str] = []
    gruplar: list[DgsGecisGrup] = []


# === Bölüm Karşılaştırma ===

class CompareRequest(BaseModel):
    codes: list[str] = Field(..., min_length=2, max_length=5)


class CompareTrendPoint(BaseModel):
    year: int | None = None
    base_rank: int | None = None
    base_score: float | None = None
    quota: int | None = None


class CompareItem(BaseModel):
    code: str
    found: bool
    # DGS (dikey geçiş) — kod eşleşirse taban/kontenjan
    dgs_min_puan: float | None = None
    dgs_puan_turu: str | None = None
    dgs_kontenjan: int | None = None
    # Program
    department_name: str = ""
    department_group: str = ""
    faculty_name: str = ""
    score_type: str = ""
    education_level: str = ""
    education_language: str = ""
    duration_years: int | None = None
    scholarship: str = ""
    fee_try: int | None = None
    accreditation: str = ""
    min_basari_sirasi_kosul: str | None = None
    # Üniversite
    university_code: str = ""
    university_name: str = ""
    university_type: str = ""
    city: str = ""
    region: str = ""
    logo_url: str = ""
    website: str = ""
    founded_year: int | None = None
    # 2025 yerleştirme
    base_score: float | None = None
    base_rank: int | None = None
    quota: int | None = None
    yerlesen: int | None = None
    # Akademik kadro
    academic_total: int = 0
    academic_professor: int = 0
    academic_associate: int = 0
    academic_assistant: int = 0
    # Trend
    trend: list[CompareTrendPoint] = Field(default_factory=list)
    # Coğrafi
    is_coastal: bool = False
    is_metropolis: bool = False


class CompareDiffEntry(BaseModel):
    best_code: str
    worst_code: str


class CompareResponse(BaseModel):
    items: list[CompareItem]
    diffs: dict[str, CompareDiffEntry] = Field(default_factory=dict)
    error: str | None = None


class CompassResponse(BaseModel):
    matches: list[CompassMatchItem]
    mode: str
    notes: str = ""


class CompassSelectionRequest(BaseModel):
    selected: list[str] = Field(..., min_length=1, max_length=40)
    top_k: int = Field(default=15, ge=3, le=30)


class CompassTextRequest(BaseModel):
    text: str = Field(..., min_length=3, max_length=500)
    top_k: int = Field(default=15, ge=3, le=30)


class CompassAxesRequest(BaseModel):
    """5-boyutlu kişilik vektörü, her boyut 1-5."""
    math: float = Field(..., ge=1, le=5)
    human: float = Field(..., ge=1, le=5)
    creative: float = Field(..., ge=1, le=5)
    research: float = Field(..., ge=1, le=5)
    field: float = Field(..., ge=1, le=5)
    top_k: int = Field(default=15, ge=3, le=30)


# === Bölüm Rehberi (gezilebilir /bolum katalog + detay) ===

class GuideListItem(BaseModel):
    slug: str
    name: str
    category: str = ""
    program_count: int = 0
    summary: str = ""


class GuideListResponse(BaseModel):
    total: int
    items: list[GuideListItem]


class GuideProgram(BaseModel):
    department_code: str
    university_name: str = ""
    university_type: str = ""
    city: str = ""
    score_type: str = ""
    base_score: float | None = None
    base_rank: int | None = None
    quota: int | None = None
    scholarship: str = ""
    education_language: str = ""


class GuideDetailResponse(BaseModel):
    slug: str
    name: str
    category: str = ""
    program_count: int = 0
    data_yili: int | None = None  # taban/sıra verilerinin yılı (rankings'ten)
    summary: str = ""
    content: str = ""
    programs: list[GuideProgram]


# === Haber / Sınav Takvimi ===

class ExamEvent(BaseModel):
    id: str = ""
    sinav: str = ""
    tam_ad: str = ""
    tur: str = ""          # sinav | sonuc | tercih | yerlestirme | basvuru
    tarih: str = ""        # ISO (süreli etkinlikte başlangıç)
    bitis: str | None = None   # süreli etkinlik bitişi (ör. tercih dönemi)
    devam: bool = False        # başlangıç geçti ama bitiş gelmedi → sürüyor
    aciklama: str = ""
    kaynak: str = ""
    tahmini: bool = False
    kalan_gun: int = 0


class ExamCalendarResponse(BaseModel):
    guncelleme: str = ""
    not_: str = Field(default="", alias="not")
    yaklasan: list[ExamEvent]
    gecmis: list[ExamEvent] = []

    model_config = {"populate_by_name": True}


# === LGS tercih robotu (tersine öneri) ===

class LgsOneriRequest(BaseModel):
    yuzdelik: float = Field(..., ge=0, le=100)  # Türkiye geneli yüzdelik dilim
    il: str | None = Field(None, max_length=40)  # tekil (geriye uyum)
    # max_length: KpssKadroRequest.iller (max 20) ile tutarlı — sınırsız liste
    # aşırı-boyutlu gövdeyle 512MB instance'ı OOM'a sürükleyebilir (DoS)
    iller: list[str] | None = Field(None, max_length=81)   # çoklu il seçimi
    ilce: str | None = Field(None, max_length=60)
    turler: list[str] | None = Field(None, max_length=20)  # fen, anadolu, sosyal, imam_hatip, meslek...
    pansiyon: str | None = Field(None, max_length=10)       # 'var' (yatılı) | 'yok' (gündüz) | None


class LgsTrendPoint(BaseModel):
    yil: int
    yuzdelik: float
    puan: float | None = None


class LgsLise(BaseModel):
    okul: str
    il: str = ""
    ilce: str = ""
    tur: str = ""
    dil: str = ""
    taban_puan: float | None = None
    yuzdelik: float | None = None
    kontenjan: int | None = None
    pansiyon: str | None = None
    trend: list[LgsTrendPoint] = []
    # Çok-yıllı arşiv değerlendirmesi: zorlasiyor | kolaylasiyor | istikrarli
    trend_yonu: str | None = None


class LgsOneriResponse(BaseModel):
    yuzdelik: float
    guncelleme: str = ""
    kaynak: str = ""
    not_: str = Field(default="", alias="not")
    yil: int | None = None
    toplam: int | None = None
    sayilar: dict[str, int]
    guvenli: list[LgsLise]
    tutar: list[LgsLise]
    riskli: list[LgsLise]

    model_config = {"populate_by_name": True}


class LgsIllerResponse(BaseModel):
    iller: list[str]


class LgsIlcelerResponse(BaseModel):
    ilceler: list[str]


# === TUS/DUS uzmanlık tercih robotu ===

class TusOneriRequest(BaseModel):
    puan: float = Field(..., ge=0, le=100)      # K veya T puanı
    sinav: Literal["TUS", "DUS"] = "TUS"
    dal: str | None = Field(None, max_length=120)          # uzmanlık dalı (tam eşleşme)
    kontenjan_turu: str | None = Field(None, max_length=40)  # Genel | Yabancı Uyruklu
    kurum: str | None = Field(None, max_length=120)        # kurum adı içinde arama

    @field_validator("sinav", mode="before")
    @classmethod
    def _validate_sinav(cls, v):
        val = (v if v is not None else "TUS")
        norm = str(val).strip().upper()
        if not norm:
            return "TUS"
        if norm not in ("TUS", "DUS"):
            raise ValueError("sinav 'TUS' veya 'DUS' olmalıdır")
        return norm


class TusProgram(BaseModel):
    kod: str = ""
    ad: str = ""
    kurum: str | None = None
    dal: str = ""
    kontenjan_turu: str = ""
    kontenjan: int | None = None
    yerlesen: int | None = None
    bos: int | None = None
    min_puan: float | None = None
    max_puan: float | None = None


class TusOneriResponse(BaseModel):
    sinav: str = "TUS"
    donem: str = ""
    puan: float
    not_: str = Field(default="", alias="not")
    sayilar: dict[str, int]
    guvenli: list[TusProgram]
    tutar: list[TusProgram]
    riskli: list[TusProgram]

    model_config = {"populate_by_name": True}


class TusMetaResponse(BaseModel):
    sinav: str = "TUS"
    donem: str = ""
    guncelleme: str = ""
    kaynak: str = ""
    kaynak_url: str = ""
    toplam: int | None = None
    taban_puanli: int | None = None
    dallar: list[str] = []


# === Kariyer (günlük ilan sinyalleri + kaynak rehberi) ===

class KariyerIlan(BaseModel):
    id: str = ""
    hat: str = ""
    kaynak: str = ""
    baslik: str = ""
    kurum: str = ""
    sehir: str = ""
    tarih: str = ""
    url: str = ""
    ozet: str = ""
    detay: dict = {}
    ilk_gorulme: str = ""
    yeni: bool = False
    bolumler: list[str] = []
    # Şema v2 (eklemeli): eksikler servis tarafında bilinmiyor/null dolar
    kaynak_kod: str = ""
    il: str = ""
    ilce: str = ""
    bolge: str = ""
    calisma_sekli: str = "bilinmiyor"
    istihdam_turu: str = "bilinmiyor"
    deneyim: str = "bilinmiyor"
    pozisyon_etiket: list[str] = []
    kpss: bool | None = None
    maas: dict | None = None
    son_basvuru: str | None = None


class KariyerIlanlarResponse(BaseModel):
    toplam: int
    sayfa: int = 1
    boyut: int = 20
    ilanlar: list[KariyerIlan]


class KariyerKaynak(BaseModel):
    id: str = ""
    hat: str = ""
    tip: str = ""
    ad: str = ""
    url: str = ""
    not_: str = Field(default="", alias="not")

    model_config = {"populate_by_name": True}


class KariyerKaynaklarResponse(BaseModel):
    toplam: int
    kaynaklar: list[KariyerKaynak]


class KariyerMetaResponse(BaseModel):
    toplam: int = 0
    kaynak_sayisi: int = 0
    son_tarih: str = ""
    rehber_kaynak: int = 0
    son_kosu: dict = {}


class KariyerBolum(BaseModel):
    id: str = ""
    label: str = ""
    sayi: int = 0


class KariyerBolumlerResponse(BaseModel):
    toplam: int
    bolumler: list[KariyerBolum]


class KariyerFacetItem(BaseModel):
    id: str = ""
    sayi: int = 0
    bolge: str = ""


class KariyerFiltrelerResponse(BaseModel):
    hat: list[KariyerFacetItem] = []
    bolge: list[KariyerFacetItem] = []
    il: list[KariyerFacetItem] = []
    calisma_sekli: list[KariyerFacetItem] = []
    istihdam_turu: list[KariyerFacetItem] = []
    deneyim: list[KariyerFacetItem] = []
    kaynak: list[KariyerFacetItem] = []
