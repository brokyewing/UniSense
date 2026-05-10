# UniSense Qwen Fine-Tuning

Bu klasör Qwen3-4B-Instruct modelini UniSense'e özelleştirmek için
hazırlanmış eğitim verilerini içerir.

## Veri

`qwen_finetune.jsonl` — ShareGPT formatında 2.6k+ Q/A çifti:

| Kategori | Örnek sayısı |
|---|---:|
| Üniversite özetleri (227 üni × 3 soru) | ~680 |
| Bölüm/üni eşleştirmeleri | ~1500 |
| Sıra/puan/filtre kombinasyonları | ~450 |
| Coğrafi sorular (deniz/merkez/metropol) | ~25 |
| İlgi → bölüm eşleştirmeleri | ~10 |
| **Toplam** | **~2654** |

Her örnek 3 mesajdan oluşur:
1. **system** — UniSense system prompt'u
2. **user** — kullanıcı sorusu
3. **assistant** — yapısal veriden sentezlenmiş cevap

## Veriyi Yenile / Genişlet

```bash
cd backend
python scripts/generate_training_data.py
```

Üretici fonksiyonlarını `scripts/generate_training_data.py` içinde:
- `gen_university_summaries(n_per_uni=3)` — üni özetleri
- `gen_department_at_uni(n_samples=1500)` — program bilgisi
- `gen_rank_filter_questions(n_samples=600)` — sıra+filtre
- `gen_geo_questions()` — coğrafi
- `gen_compass_interest_questions()` — ilgi → bölüm

İstersen yeni `gen_*` fonksiyonu yazıp `main()`'e ekle.

## Eğitim — 3 yol

### A) Unsloth (en hızlı, Colab/RunPod)

```python
from unsloth import FastLanguageModel
from datasets import load_dataset
from trl import SFTTrainer, SFTConfig

# Model yükle (4-bit QLoRA)
model, tokenizer = FastLanguageModel.from_pretrained(
    "unsloth/Qwen3-4B-Instruct-bnb-4bit",
    max_seq_length=2048,
    load_in_4bit=True,
)
model = FastLanguageModel.get_peft_model(
    model,
    r=16,
    target_modules=["q_proj","k_proj","v_proj","o_proj",
                    "gate_proj","up_proj","down_proj"],
    lora_alpha=16,
    lora_dropout=0,
    use_gradient_checkpointing="unsloth",
)

# Veriyi yükle
ds = load_dataset("json", data_files="qwen_finetune.jsonl", split="train")

# Format
def fmt(ex):
    text = tokenizer.apply_chat_template(
        ex["messages"], tokenize=False, add_generation_prompt=False
    )
    return {"text": text}
ds = ds.map(fmt)

# Train
trainer = SFTTrainer(
    model=model,
    tokenizer=tokenizer,
    train_dataset=ds,
    dataset_text_field="text",
    max_seq_length=2048,
    args=SFTConfig(
        per_device_train_batch_size=2,
        gradient_accumulation_steps=4,
        warmup_steps=10,
        num_train_epochs=2,
        learning_rate=2e-4,
        fp16=False, bf16=True,
        logging_steps=10,
        optim="adamw_8bit",
        output_dir="qwen-unisense-lora",
    ),
)
trainer.train()
model.save_pretrained_merged("qwen-unisense-merged", tokenizer, save_method="merged_16bit")
```

**GPU gereksinimi:** 8GB VRAM (T4/RTX 3060 yeterli)
**Süre:** 2 epoch × ~2.6k örnek ≈ **40-60 dakika**

### B) Axolotl (config dosyası ile)

```yaml
# qwen_unisense.yml
base_model: Qwen/Qwen3-4B-Instruct
load_in_4bit: true
adapter: qlora
lora_r: 16
lora_alpha: 16
sequence_len: 2048
datasets:
  - path: qwen_finetune.jsonl
    type: chat_template
    chat_template: qwen3
num_epochs: 2
learning_rate: 2e-4
micro_batch_size: 2
gradient_accumulation_steps: 4
optimizer: adamw_8bit
output_dir: ./qwen-unisense-axolotl
```

```bash
accelerate launch -m axolotl.cli.train qwen_unisense.yml
```

### C) HuggingFace TRL (manuel)

```python
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import LoraConfig, get_peft_model
from trl import SFTTrainer
# (yukarıdaki Unsloth örneğine benzer, daha fazla manuel kod)
```

## Eğitim Sonrası — Servis Entegrasyonu

LoRA adapter (~80MB) eğitildikten sonra:

### Seçenek 1: vLLM (production, hızlı)
```bash
pip install vllm
python -m vllm.entrypoints.openai.api_server \
    --model qwen-unisense-merged \
    --enable-lora \
    --port 8003
```

### Seçenek 2: llama.cpp (CPU + GPU, lokal)
```bash
# GGUF'a çevir
python convert.py qwen-unisense-merged --outtype q4_k_m
./llama-server -m qwen-unisense-merged.gguf -c 4096 --port 8003
```

### Seçenek 3: Cloudflare Tunnel (eski AFET projesi gibi)
```bash
cloudflared tunnel --url http://localhost:8003
```

## Backend'e Bağlama

`backend/src/unisense/infrastructure/llm/qwen.py` ekle:

```python
import requests
from unisense.application.interfaces.llm_provider import LLMProvider

class QwenProvider(LLMProvider):
    name = "qwen-unisense"

    def __init__(self, base_url: str = "http://localhost:8003"):
        self._base = base_url

    def generate(self, query: str, context: str | None = None) -> str:
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"KAYNAKLAR:\n{context}\n\nSORU: {query}"}
            if context else
            {"role": "user", "content": query}
        ]
        r = requests.post(f"{self._base}/v1/chat/completions", json={
            "model": "qwen-unisense",
            "messages": messages,
            "max_tokens": 512,
            "temperature": 0.3,
        })
        return r.json()["choices"][0]["message"]["content"]
```

DI container'da Gemini → Qwen fallback:

```python
@lru_cache(maxsize=1)
def get_llm_provider() -> LLMProvider:
    from unisense.infrastructure.llm.gemini import GeminiProvider
    from unisense.infrastructure.llm.qwen import QwenProvider
    primary = GeminiProvider()
    fallback = QwenProvider()
    return MultiLLMRouter(primary=primary, fallback=fallback)
```

## A/B Karşılaştırma (eski AFET RAG projesindeki gibi)

`/api/v1/compare` endpoint'i 3 LLM cevabını yan yana döner:
- Gemini + RAG
- Gemini (no RAG, plain)
- Qwen + RAG

Frontend'de 3 sütun karşılaştırma → kalite ölçümü.

## Notlar

- **Veri kalitesi**: Bu sentetik veri **structured ground truth**'a dayanıyor (rankings.json'dan direkt).
  Gemini cevapları gibi LLM-distillation'a göre daha güvenilir, ama tarz olarak "soğuk" olabilir.
  İdeali: %70 sentetik + %30 Gemini-distilled karışım.
- **Türkçe karakterler**: JSONL UTF-8, sorun yok.
- **Lisans**: Qwen3-4B Apache 2.0 — ticari kullanıma uygun.
- **Maliyet**: A100 1 saat ~$1.50 (RunPod), Colab Pro ücretsiz seçenek.
