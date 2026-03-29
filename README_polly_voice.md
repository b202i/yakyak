# Supporting Amazon Polly in YakYak

This document tracks verified facts, open questions, and integration tasks for
adding Amazon Polly as a TTS backend in YakYak.

---

## ✅ Verified Facts (as of March 2026)

| Item | Detail |
|------|--------|
| AWS service name | Amazon Polly |
| Python SDK | `boto3` (`polly_client.synthesize_speech(...)`) |
| Authentication | AWS credentials (`AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` or IAM role) |
| Voice engines | Standard, Neural (NTTS), Long-Form, Generative |
| Languages supported | 30+ languages, 60+ voices |
| Output formats | MP3, OGG_VORBIS, PCM |
| Streaming | `start_speech_synthesis_task` for async S3 delivery; synchronous stream also available |
| Source model | Closed source / proprietary |
| Compliance | SOC 2, HIPAA-eligible, PCI DSS — runs on AWS infrastructure |

---

## 💰 Pricing (as of March 2026)

| Engine | Free tier (first 12 months) | Standard paid |
|--------|----------------------------|---------------|
| Standard | 5M chars/month | $4.00 / 1M chars |
| Neural (NTTS) | 1M chars/month | $16.00 / 1M chars |
| Long-Form | None | $100.00 / 1M chars |
| Generative | None | $30.00 / 1M chars |

> **Note:** Verify at https://aws.amazon.com/polly/pricing/

---

## 🚦 Rate Limits

| Limit | Value |
|-------|-------|
| `SynthesizeSpeech` requests | 100 TPS (default; can be raised) |
| Max characters per request | 3,000 (standard) / 100,000 (async task) |
| Concurrent synthesis tasks | 10 default |

---

## ❓ Open Questions

| Item | Status |
|------|--------|
| Generative engine regional availability | **Limited regions** — check AWS console |
| Long-Form engine voice list | **Growing** — confirm current voices |
| Polly real-time streaming vs. pre-synthesis | **Depends on use case** |

---

## Integration Plan

### New class: `PollyTtsClient` (in `yakyak/yakyak.py`)

```python
class PollyTtsClient:
    def __init__(self, region: str = "us-east-1",
                 voice_id: str = "Joanna",
                 engine: str = "neural") -> None:
        ...

    async def get_tts_audio(self, message: str) -> tuple[bytes | None, str | None]:
        """Call Amazon Polly SynthesizeSpeech, return MP3 bytes."""
        ...
```

Key implementation points:
- Use `boto3` with standard AWS credential chain (env vars → `~/.aws/credentials` → IAM role)
- Default engine: `neural`; default voice: `Joanna`
- Run `boto3` call in `asyncio.to_thread(...)` since it's synchronous
- Return `(audio_bytes, "mp3")`
- Add `boto3` to `requirements.txt`

### CLI

```
yakyak --backend polly --voice Joanna "Hello world"
yakyak --backend polly --voice Matthew --engine generative "Hello world"
```

---

## Testing Plan

| Test | Type | Notes |
|------|------|-------|
| `PollyTtsClient` with mocked `boto3` | Unit | `unittest.mock.patch('boto3.client')` |
| Live round-trip | Integration | Requires AWS credentials |
| CLI smoke test | Integration | |
| Wyoming regression | Regression | |

---

## Estimated Effort

| Task | Effort |
|------|--------|
| Implement `PollyTtsClient` | 0.5–1 day |
| AWS auth docs / setup | 0.5 day |
| CLI wiring | 0.25 day |
| Unit + integration tests | 0.5–1 day |
| Docs | 0.25 day |
| **Total** | **~2–3 days** |

> `boto3` is a stable, well-documented SDK. Main effort is IAM permissions
> documentation and async wrapper for the synchronous SDK calls.

