# Supporting Microsoft Azure AI Speech in YakYak

This document tracks verified facts, open questions, and integration tasks for
adding Azure AI Speech (Cognitive Services TTS) as a backend in YakYak.

---

## ✅ Verified Facts (as of March 2026)

| Item | Detail |
|------|--------|
| REST endpoint | `POST https://<region>.tts.speech.microsoft.com/cognitiveservices/v1` |
| Python SDK | `azure-cognitiveservices-speech` (Speech SDK) |
| Authentication | Azure subscription key (`AZURE_SPEECH_KEY`) + region |
| Voice families | Standard, Neural, Neural HD, Personal Voice (cloning) |
| Languages supported | 140+ languages, 400+ voices |
| Output formats | MP3, WAV, OGG, RIFF, raw PCM |
| Streaming | SDK-native real-time streaming synthesis |
| SSML support | Full SSML 1.0 support for fine-grained control |
| Source model | Closed source / proprietary |

---

## 💰 Pricing (as of March 2026)

| Voice type | Free tier | Paid |
|------------|-----------|------|
| Neural (standard) | 0.5M chars/month | $16.00 / 1M chars |
| Neural HD | None | $24.00 / 1M chars |
| Personal Voice (cloning) | None | ~$100.00 / 1M chars (varies) |
| Custom Neural Voice | None | Contact Microsoft |

> **Note:** Verify at https://azure.microsoft.com/en-us/pricing/details/cognitive-services/speech-services/

---

## 🚦 Rate Limits

| Limit | Value |
|-------|-------|
| Transactions per second (TPS) | 200 TPS (default; can be raised) |
| Concurrent connections (SDK) | 20 (default) |
| Max input length (REST) | 10,000 characters |

---

## ❓ Open Questions

| Item | Status |
|------|--------|
| Personal Voice cloning GA status | **GA as of 2024** — check regional availability |
| Avatar / video synthesis via same key | **Separate feature** — out of scope for audio-only YakYak |
| OpenAI-compatible endpoint on Azure | **Available** — Azure OpenAI Service also offers TTS |

---

## Integration Plan

### New class: `AzureTtsClient` (in `yakyak/yakyak.py`)

```python
class AzureTtsClient:
    def __init__(self, subscription_key: str, region: str,
                 voice_name: str = "en-US-JennyNeural") -> None:
        ...

    async def get_tts_audio(self, message: str) -> tuple[bytes | None, str | None]:
        """Call Azure Speech REST API, return MP3 bytes."""
        ...
```

Key implementation points:
- Read `AZURE_SPEECH_KEY` and `AZURE_SPEECH_REGION` from environment
- Default voice: `en-US-JennyNeural`
- REST call is straightforward (no separate SDK required for basic use)
- Return `(audio_bytes, "mp3")`
- Add `azure-cognitiveservices-speech` (or just `httpx` for REST-only) to `requirements.txt`

### CLI

```
yakyak --backend azure --voice en-US-JennyNeural "Hello world"
```

---

## Testing Plan

| Test | Type | Notes |
|------|------|-------|
| `AzureTtsClient` with mocked HTTP | Unit | Mock REST endpoint |
| Live round-trip | Integration | Requires `AZURE_SPEECH_KEY` + region |
| CLI smoke test | Integration | |
| Wyoming regression | Regression | |

---

## Estimated Effort

| Task | Effort |
|------|--------|
| Implement `AzureTtsClient` | 0.5–1 day |
| Azure auth / region setup docs | 0.5 day |
| CLI wiring | 0.25 day |
| Unit + integration tests | 0.5–1 day |
| Docs | 0.25 day |
| **Total** | **~2–3 days** |

> Azure has the largest voice catalog (400+ voices, 140+ languages). Main
> complexity is region configuration and the SSML input format.

