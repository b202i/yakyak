# Supporting Google Cloud Text-to-Speech in YakYak

This document tracks verified facts, open questions, and integration tasks for
adding Google Cloud TTS as a backend in YakYak.

---

## ✅ Verified Facts (as of March 2026)

| Item | Detail |
|------|--------|
| REST endpoint | `POST https://texttospeech.googleapis.com/v1/text:synthesize` |
| Python SDK | `google-cloud-texttospeech` |
| Authentication | Google service account JSON or Application Default Credentials |
| Voice families | Standard, WaveNet, Neural2, Studio, Polyglot |
| Languages supported | 60+ languages / 380+ voices |
| Output formats | LINEAR16 (WAV), MP3, OGG_OPUS, MULAW, ALAW |
| Streaming | Streaming synthesis available via `streamingSynthesize` RPC (gRPC) |
| Source model | Closed source / proprietary |
| Duet AI / Gemini integration | Google's conversational AI uses the same TTS infrastructure |

---

## 💰 Pricing (as of March 2026)

| Voice type | Free tier | Paid |
|------------|-----------|------|
| Standard | 4M chars/month | $4.00 / 1M chars |
| WaveNet | 1M chars/month | $16.00 / 1M chars |
| Neural2 | 1M chars/month | $16.00 / 1M chars |
| Studio | 100K chars/month | $160.00 / 1M chars |

> **Note:** Verify at https://cloud.google.com/text-to-speech/pricing

---

## 🚦 Rate Limits

| Limit | Value |
|-------|-------|
| Requests per minute (default) | 1,000 RPM |
| Characters per request | 5,000 bytes |
| Characters per minute | ~1M (varies by quota) |

---

## ❓ Open Questions

| Item | Status |
|------|--------|
| Studio voice GA status | **GA as of 2024** — confirm availability in target regions |
| gRPC streaming setup complexity | **Moderate** — requires additional gRPC dep |
| Gemini Live / Duet AI TTS separate endpoint | **Unconfirmed for API access** |

---

## Integration Plan

### New class: `GoogleTtsClient` (in `yakyak/yakyak.py`)

```python
class GoogleTtsClient:
    def __init__(self, credentials_path: str | None = None,
                 voice_name: str = "en-US-Neural2-C",
                 language_code: str = "en-US") -> None:
        ...

    async def get_tts_audio(self, message: str) -> tuple[bytes | None, str | None]:
        """Call Google Cloud TTS, return raw MP3 bytes."""
        ...
```

Key implementation points:
- Support `GOOGLE_APPLICATION_CREDENTIALS` env var (standard ADC pattern)
- Default to Neural2 voice for quality/cost balance
- Return `(audio_bytes, "mp3")`
- Add `google-cloud-texttospeech` to `requirements.txt`

### CLI

```
yakyak --backend google --voice en-US-Neural2-C "Hello world"
```

---

## Testing Plan

| Test | Type | Notes |
|------|------|-------|
| `GoogleTtsClient` with mocked SDK | Unit | Mock `google.cloud.texttospeech` |
| Live round-trip | Integration | Requires GCP credentials |
| CLI smoke test | Integration | |
| Wyoming regression | Regression | |

---

## Estimated Effort

| Task | Effort |
|------|--------|
| Implement `GoogleTtsClient` | 1 day |
| GCP auth setup / docs | 0.5 day |
| CLI wiring | 0.25 day |
| Unit + integration tests | 0.5–1 day |
| Docs | 0.25 day |
| **Total** | **~2.5–3 days** |

> Main complexity is GCP authentication setup (service accounts vs. ADC) and
> the large voice catalog requiring sensible defaults.

