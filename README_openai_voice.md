# Supporting OpenAI TTS / Voice Engine in YakYak

This document tracks verified facts, open questions, and integration tasks for
adding OpenAI TTS as a backend in YakYak.

---

## ✅ Verified Facts (as of March 2026)

| Item | Detail |
|------|--------|
| REST endpoint | `POST https://api.openai.com/v1/audio/speech` |
| SDK | `openai` Python package (`openai.audio.speech.create(...)`) |
| Authentication | OpenAI API key (`OPENAI_API_KEY` env var) |
| Models available | `tts-1` (fast/low-latency), `tts-1-hd` (higher quality) |
| Built-in voices | `alloy`, `echo`, `fable`, `onyx`, `nova`, `shimmer` |
| Output formats | `mp3`, `opus`, `aac`, `flac`, `wav`, `pcm` |
| Streaming | Chunked HTTP response (no separate WebSocket required) |
| Source model | Closed source / proprietary |
| Voice cloning | "Voice Engine" (custom voice cloning) — limited beta access |

---

## 💰 Pricing (as of March 2026)

| Model | Price |
|-------|-------|
| `tts-1` | ~$15 / 1M characters |
| `tts-1-hd` | ~$30 / 1M characters |
| Voice Engine (cloning) | Separate access program; pricing varies |

> **Note:** Verify current prices at https://openai.com/pricing before billing decisions.

---

## 🚦 Rate Limits

| Tier | Limit |
|------|-------|
| Free / Tier 1 | 3 RPM, 200 requests/day |
| Tier 2+ | Higher limits — see https://platform.openai.com/docs/guides/rate-limits |

---

## ❓ Open Questions

| Item | Status |
|------|--------|
| Voice Engine (cloning) API availability | **Limited beta** — apply at platform.openai.com |
| Custom voice upload endpoint | **Unconfirmed for GA** |
| Per-character vs. per-second billing for future models | **Watch for changes** |

---

## Integration Plan

### New class: `OpenAITtsClient` (in `yakyak/yakyak.py`)

```python
class OpenAITtsClient:
    def __init__(self, api_key: str, voice: str = "nova", model: str = "tts-1") -> None:
        ...

    async def get_tts_audio(self, message: str) -> tuple[bytes | None, str | None]:
        """POST to https://api.openai.com/v1/audio/speech, return raw audio bytes."""
        ...
```

Key implementation points:
- Read `OPENAI_API_KEY` from environment
- Default voice: `nova`; default model: `tts-1`
- Return `(audio_bytes, "mp3")` to match the existing pipeline tuple contract
- Handle `429 Too Many Requests` with exponential backoff
- Raise a clear exception on auth failure (`401`)

### CLI

```
yakyak --backend openai --voice nova "Hello world"
yakyak --backend openai --voice alloy --model tts-1-hd "Hello world"
```

---

## Testing Plan

| Test | Type | Notes |
|------|------|-------|
| `OpenAITtsClient` with mocked HTTP | Unit | No real API key needed |
| Live round-trip (short string → mp3) | Integration | Requires `OPENAI_API_KEY` |
| `--backend openai` CLI smoke test | Integration | |
| Wyoming path regression | Regression | Must remain unchanged |

---

## Estimated Effort

| Task | Effort |
|------|--------|
| Implement `OpenAITtsClient` | 0.5–1 day |
| CLI flag wiring | 0.25 day |
| Unit + integration tests | 0.5–1 day |
| Docs | 0.25 day |
| **Total** | **~1.5–2.5 days** |

> OpenAI TTS is the **fastest to integrate** due to the mature Python SDK and
> extensive documentation.

