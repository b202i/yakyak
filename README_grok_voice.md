# Supporting Grok Voice API in YakYak

This document tracks verified facts, open questions, and integration tasks for
adding xAI Grok Voice as a TTS backend in YakYak.

---

## ✅ Verified Facts (as of March 2026)

| Item | Detail |
|------|--------|
| Correct REST endpoint | `POST https://api.x.ai/v1/audio/speech` |
| Streaming transport | WebSocket (e.g., via LiveKit plugin) |
| Authentication | xAI API key (Bearer token), same key as chat API |
| xAI founded | March 2023 |

---

## ❓ Open Questions (unconfirmed — do not assume)

| Item | Status |
|------|--------|
| Pricing (e.g., per character or per second) | **Unconfirmed** — check console.x.ai |
| Rate limits (RPM / TPM) | **Unconfirmed** — check xAI docs or dashboard |
| Supported voices / voice IDs | **Unconfirmed** |
| Speed/pitch control parameters | **Unconfirmed** — do not assume 0.5x–2x |
| Output audio formats (mp3, wav, pcm…) | **Unconfirmed** |
| Beta vs. GA status of TTS endpoint | **Unconfirmed** |
| Streaming chunk format over WebSocket | **Unconfirmed** |

---

## Research Tasks (prioritized)

1. **Hit the real endpoint** — make a minimal authenticated `POST` to
   `https://api.x.ai/v1/audio/speech` with a short test string and inspect
   the actual response: format, headers, audio encoding.

2. **Check console.x.ai** — find the TTS section for pricing, rate limits,
   and available voice IDs.

3. **Review xAI API changelog / docs** — confirm whether the endpoint is
   stable or still in beta.

4. **Test WebSocket / streaming path** — determine if real-time streaming
   requires LiveKit or if a plain WebSocket works.

5. **Capture error responses** — document actual HTTP error codes and
   payloads for rate-limit, auth failure, and bad-request cases.

---

## Integration Plan

### New class: `GrokTtsClient` (in `yakyak/yakyak.py`)

Model it after the existing `WyomingTtsClient`:

```python
class GrokTtsClient:
    def __init__(self, api_key: str, voice: str = "...", model: str = "...") -> None:
        ...

    async def get_tts_audio(self, message: str) -> tuple[bytes | None, str | None]:
        """POST to https://api.x.ai/v1/audio/speech, return raw audio bytes."""
        ...
```

Key implementation points:
- Read `XAI_API_KEY` from environment (never hard-code)
- Return the same `(audio_bytes, format)` tuple that `WyomingTtsClient` returns
  so the rest of the pipeline is unchanged
- Handle `429 Too Many Requests` with exponential backoff
- Raise a clear exception (not a silent `None`) on auth failure

### CLI changes (`__main__.py`)

Add a `--backend` flag: `wyoming` (default) | `grok`

```
yakyak --backend grok --voice <voice-id> "Hello world"
```

When `--backend grok` is selected, skip the Wyoming/Piper server check entirely.

### Backward compatibility

Wyoming-Piper path must remain **completely unchanged**. The `--backend` flag
defaults to `wyoming` so existing users see no difference.

---

## Testing Plan

| Test | Type | Notes |
|------|------|-------|
| `GrokTtsClient` with mocked HTTP | Unit | No real API key needed |
| Live round-trip (short string → mp3) | Integration | Requires `XAI_API_KEY` in env |
| `--backend grok` CLI smoke test | Integration | |
| Wyoming path still works after changes | Regression | |
| Missing / invalid API key error message | Unit | |

---

## Version and PyPI

- Bump version to next minor (e.g., `0.x.0 → 0.(x+1).0`) in `pyproject.toml` and `setup.py`
- Add `httpx` (or `aiohttp`) to `requirements.txt` for async HTTP to xAI REST endpoint
- Follow existing `PYPI_UPLOAD_GUIDE.md` steps — no changes needed there

---

## Estimated Effort

| Task | Effort |
|------|--------|
| Verify open questions (endpoint, pricing, voices) | 0.5 day |
| Implement `GrokTtsClient` | 1–2 days |
| CLI `--backend` flag | 0.5 day |
| Unit + integration tests | 1–2 days |
| Docs + PyPI publish | 0.5 day |
| **Total** | **~3.5–5 days** |
