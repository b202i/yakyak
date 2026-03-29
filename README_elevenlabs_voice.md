# Supporting ElevenLabs TTS in YakYak

This document tracks verified facts, open questions, and integration tasks for
adding ElevenLabs as a TTS backend in YakYak.

---

## ✅ Verified Facts (as of March 2026)

| Item | Detail |
|------|--------|
| REST endpoint | `POST https://api.elevenlabs.io/v1/text-to-speech/{voice_id}` |
| Python SDK | `elevenlabs` (`pip install elevenlabs`) |
| Authentication | `ELEVEN_API_KEY` env var |
| Voice catalog | 1,000+ pre-made voices + instant/professional cloning |
| Output formats | MP3 (128kbps), MP3 (44.1kHz/192kbps), PCM, μ-law |
| Streaming | `/v1/text-to-speech/{voice_id}/stream` endpoint |
| Models | `eleven_multilingual_v2`, `eleven_turbo_v2`, `eleven_flash_v2_5` |
| Languages | 32 languages (multilingual model) |
| Source model | Closed source / proprietary |
| Voice cloning | Instant cloning (short sample) and Professional cloning (higher fidelity) |

---

## 💰 Pricing (as of March 2026)

| Plan | Monthly cost | Characters included | Overage |
|------|-------------|---------------------|---------|
| Free | $0 | 10,000 chars/month | Not available |
| Starter | $5 | 30,000 chars/month | $0.30 / 1K chars |
| Creator | $22 | 100,000 chars/month | $0.30 / 1K chars |
| Pro | $99 | 500,000 chars/month | $0.24 / 1K chars |
| Scale | $330 | 2M chars/month | $0.20 / 1K chars |
| Business | $1,320 | 10M chars/month | $0.18 / 1K chars |

> At paid tiers overage is ~$200–$300 / 1M chars — significantly more expensive
> than OpenAI TTS or Google Neural2, but voice quality and cloning are industry-leading.
>
> **Note:** Verify at https://elevenlabs.io/pricing

---

## 🚦 Rate Limits

| Plan | Concurrent requests |
|------|---------------------|
| Free | 2 |
| Starter–Creator | 3–5 |
| Pro+ | 10+ |

> Character quotas reset monthly. No hard RPM limit documented; practical
> throughput gated by concurrency limits.

---

## ❓ Open Questions

| Item | Status |
|------|--------|
| `eleven_flash_v2_5` latency vs. quality trade-off | **Test required** |
| Professional voice clone turn-around time | **~4 hours per voice** — confirm current SLA |
| Websocket streaming stability | **Available** — stability at scale unconfirmed |

---

## Integration Plan

### New class: `ElevenLabsTtsClient` (in `yakyak/yakyak.py`)

```python
class ElevenLabsTtsClient:
    def __init__(self, api_key: str,
                 voice_id: str = "Rachel",
                 model_id: str = "eleven_multilingual_v2") -> None:
        ...

    async def get_tts_audio(self, message: str) -> tuple[bytes | None, str | None]:
        """POST to ElevenLabs TTS endpoint, return MP3 bytes."""
        ...
```

Key implementation points:
- Read `ELEVEN_API_KEY` from environment
- Accept voice by name or by ID (SDK handles name→ID lookup)
- Default model: `eleven_multilingual_v2`
- Return `(audio_bytes, "mp3")`
- Add `elevenlabs` to `requirements.txt`

### CLI

```
yakyak --backend elevenlabs --voice Rachel "Hello world"
yakyak --backend elevenlabs --voice <voice_id> --model eleven_turbo_v2 "Hello world"
```

---

## Testing Plan

| Test | Type | Notes |
|------|------|-------|
| `ElevenLabsTtsClient` with mocked HTTP | Unit | Mock REST endpoint |
| Live round-trip | Integration | Requires `ELEVEN_API_KEY` |
| CLI smoke test | Integration | |
| Wyoming regression | Regression | |

---

## Estimated Effort

| Task | Effort |
|------|--------|
| Implement `ElevenLabsTtsClient` | 0.5–1 day |
| Voice ID / name resolution | 0.25 day |
| CLI wiring | 0.25 day |
| Unit + integration tests | 0.5–1 day |
| Docs | 0.25 day |
| **Total** | **~1.5–2.5 days** |

> ElevenLabs has an excellent Python SDK that makes integration straightforward.
> The main consideration is cost — substantially higher per-character than
> cloud-provider alternatives, but unmatched voice quality and cloning fidelity.

