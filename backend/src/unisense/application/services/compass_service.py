"""İlgi Pusulası servisi — 3 modlu bölüm önerme.

Mod A (selected): seçilen bölüm adlarının ortalama embeddingi → en yakın bölümler
Mod B (text):     serbest metin → embedding → en yakın bölümler
Mod C (axes):     5-boyutlu kişilik vektörü → bölüm eksen vektörleri ile cosine

Aşağıdakiler ortak:
- Sonuçtan, kullanıcının seçtiği/ipucu verdiği bölümler hariç tutulur
- (opsiyonel) Eğer kullanıcı puan/sıra vermişse, Recommend servisinden program kovaları
"""
from __future__ import annotations

from functools import lru_cache

import numpy as np

from unisense.application.services.compass_interests import (
    get_dept_to_interests,
    get_interests_taxonomy,
)
from unisense.application.services.compass_taxonomy import (
    CATEGORIES,
    axes_to_label,
    get_taxonomy,
)
from unisense.core.config import get_settings
from unisense.core.logging import get_logger

logger = get_logger(__name__)


@lru_cache(maxsize=1)
def _model():
    # Lazy import: sentence_transformers (torch) ağır — modül import edilirken
    # değil, ilk kullanımda yüklensin (test/startup hızı)
    from sentence_transformers import SentenceTransformer

    settings = get_settings()
    return SentenceTransformer(settings.embedding_model)


@lru_cache(maxsize=1)
def _dept_matrix() -> tuple[np.ndarray, list[str]]:
    """358 bölüm için embedding matrisi + isim listesi."""
    tax = get_taxonomy()
    names = [d["name"] for d in tax["departments"]]
    # Embedlemek için: ad + etiketler + kategori label
    texts = []
    for d in tax["departments"]:
        cat_label = CATEGORIES[d["category"]]["label"]
        tag_str = ", ".join(d["tags"])
        texts.append(f"{d['name']} ({cat_label}). {tag_str}.")
    logger.info("compass_embedding_dept_matrix", count=len(texts))
    embs = _model().encode(texts, convert_to_numpy=True, show_progress_bar=False)
    # L2 normalize
    norms = np.linalg.norm(embs, axis=1, keepdims=True) + 1e-9
    return embs / norms, names


@lru_cache(maxsize=1)
def _axes_matrix() -> tuple[np.ndarray, list[str]]:
    """358 bölüm için 5-boyutlu eksen matrisi (1-5 ölçeğinde)."""
    tax = get_taxonomy()
    names = [d["name"] for d in tax["departments"]]
    axes = np.array([d["axes"] for d in tax["departments"]], dtype=np.float32)
    # Merkezle (3 = nötr) ve normalize et
    centered = axes - 3.0
    norms = np.linalg.norm(centered, axis=1, keepdims=True) + 1e-9
    return centered / norms, names


def _normalize_query(text: str) -> np.ndarray:
    emb = _model().encode([text], convert_to_numpy=True, show_progress_bar=False)[0]
    return emb / (np.linalg.norm(emb) + 1e-9)


def _format_dept(name: str, score: float) -> dict:
    """Bölüm adını, kategorisini, etiketlerini döner."""
    tax = get_taxonomy()
    for d in tax["departments"]:
        if d["name"] == name:
            cat = CATEGORIES[d["category"]]
            return {
                "name": d["name"],
                "category": d["category"],
                "category_label": cat["label"],
                "category_emoji": cat["emoji"],
                "tags": d["tags"],
                "axis_summary": axes_to_label(d["axes"]),
                "program_count": d["program_count"],
                "match_score": round(float(score) * 100, 1),
            }
    return {
        "name": name, "category": "diger", "category_label": "Diğer",
        "category_emoji": "⚙️", "tags": [], "axis_summary": "",
        "program_count": 0, "match_score": round(float(score) * 100, 1),
    }


class CompassService:
    """3 modlu ilgi pusulası servisi."""

    def get_taxonomy(self) -> dict:
        """Frontend'in kart UI'ı için tüm bölümleri kategoriye göre döner."""
        tax = get_taxonomy()
        # Kategoriye göre grupla
        by_cat: dict[str, list[dict]] = {k: [] for k in CATEGORIES}
        for d in tax["departments"]:
            by_cat[d["category"]].append({
                "name": d["name"],
                "tags": d["tags"],
                "program_count": d["program_count"],
                "axis_summary": axes_to_label(d["axes"]),
            })
        # Her kategori içinde program sayısına göre sırala
        for k in by_cat:
            by_cat[k].sort(key=lambda x: -x["program_count"])
        return {
            "categories": [
                {
                    "id": k,
                    "label": CATEGORIES[k]["label"],
                    "emoji": CATEGORIES[k]["emoji"],
                    "departments": by_cat[k],
                }
                for k in CATEGORIES
                if by_cat[k]
            ]
        }

    def by_selection(
        self,
        selected: list[str],
        top_k: int = 12,
    ) -> list[dict]:
        """Mod A: seçilen bölümlerin centroid'ine en yakın diğer bölümler."""
        if not selected:
            return []

        emb_matrix, names = _dept_matrix()
        # Seçilenlerin index'leri
        name_to_idx = {n: i for i, n in enumerate(names)}
        sel_idx = [name_to_idx[n] for n in selected if n in name_to_idx]
        if not sel_idx:
            return []

        # Centroid
        centroid = emb_matrix[sel_idx].mean(axis=0)
        centroid = centroid / (np.linalg.norm(centroid) + 1e-9)

        # Cosine sim (zaten normalized) = dot product
        sims = emb_matrix @ centroid
        # Seçilenleri filtrele
        for i in sel_idx:
            sims[i] = -1.0

        top = np.argsort(-sims)[:top_k]
        return [_format_dept(names[i], sims[i]) for i in top]

    def by_text(self, text: str, top_k: int = 15) -> list[dict]:
        """Mod B: serbest metinden ilgili bölümler."""
        text = (text or "").strip()
        if len(text) < 3:
            return []
        emb_matrix, names = _dept_matrix()
        q = _normalize_query(text)
        sims = emb_matrix @ q
        top = np.argsort(-sims)[:top_k]
        return [_format_dept(names[i], sims[i]) for i in top]

    def by_axes(self, axes: list[float], top_k: int = 15) -> list[dict]:
        """Mod C: 5 boyutlu eksenden bölümler.

        axes: [math, human, creative, research, field], her biri 1-5
        """
        if len(axes) != 5:
            raise ValueError("axes 5 boyutlu olmalı")

        ax_matrix, names = _axes_matrix()
        # User'ı da merkezle ve normalize et
        u = np.array(axes, dtype=np.float32) - 3.0
        u_norm = u / (np.linalg.norm(u) + 1e-9)
        sims = ax_matrix @ u_norm
        top = np.argsort(-sims)[:top_k]
        return [_format_dept(names[i], sims[i]) for i in top]

    # === İlgi etiketleri (interest tags) ===

    def get_interests_taxonomy(self) -> dict:
        """Frontend için: kategori → ilgi pill'leri (bölüm adı içermez)."""
        data = get_interests_taxonomy()
        # _dept_interests'i dışarı sızdırma
        return {"categories": data["categories"]}

    def by_interests(
        self,
        interests: list[str],
        top_k: int = 15,
    ) -> list[dict]:
        """Seçilen ilgilere uyan bölümleri öner.

        Skor:
          0.55 * (eşleşen_etiket / kullanıcı_etiket)   ← kapsama
        + 0.30 * (eşleşen_etiket / bölüm_etiket)        ← odaklanma
        + 0.15 * embedding_sim(seçili_ilgiler, bölüm)  ← anlam yakınlığı
        Eşleşen etiketi olmayan bölümleri filtrele (yarı düşük embedding eşiği üstü
        olanlar bonus olarak eklenir).
        """
        if not interests:
            return []

        sel = {s.strip() for s in interests if s.strip()}
        if not sel:
            return []

        dept_interests = get_dept_to_interests()
        emb_matrix, names = _dept_matrix()
        name_to_idx = {n: i for i, n in enumerate(names)}

        # Embedding sorgu (seçilen etiketleri birleştir)
        query_text = ", ".join(sorted(sel))
        q = _normalize_query(query_text)
        emb_sims = emb_matrix @ q  # shape (358,)

        scored: list[tuple[str, float, int]] = []
        for name, divs in dept_interests.items():
            dset = set(divs)
            overlap = sel & dset
            if not overlap:
                continue
            coverage = len(overlap) / max(len(sel), 1)       # kullanıcının istekleri ne kadar karşılandı
            focus = len(overlap) / max(len(dset), 1)         # bölümün etiketleri ne kadar uydu
            idx = name_to_idx.get(name, -1)
            emb_score = float(emb_sims[idx]) if idx >= 0 else 0.0
            score = 0.55 * coverage + 0.30 * focus + 0.15 * emb_score
            scored.append((name, score, len(overlap)))

        scored.sort(key=lambda x: -x[1])

        out: list[dict] = []
        for name, score, n_match in scored[:top_k]:
            item = _format_dept(name, score)
            item["matched_interests"] = sorted(
                set(dept_interests[name]) & sel,
                key=lambda x: list(sel).index(x) if x in sel else 0,
            )
            item["matched_count"] = n_match
            out.append(item)
        return out
