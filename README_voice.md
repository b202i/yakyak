# TTS Backend Comparison for YakYak

This document compares all TTS backends evaluated for YakYak integration.
Each provider has a dedicated deep-dive README linked in the table below.

---

## Provider Comparison Table

| Provider | Source | Cost (approx.) | Rate Limits | Voice Cloning | Streaming | Effort to Integrate | Detail |
|----------|--------|----------------|-------------|---------------|-----------|---------------------|--------|
| **Piper** (current default) | Open source (Apache 2.0) | **Free** — local inference | None (hardware-bound) | ❌ | WAV stream via Wyoming | ✅ Already integrated | [README_piper_voice.md](README_piper_voice.md) |
| **OpenAI TTS** | Closed / proprietary | `tts-1`: ~$15/1M chars · `tts-1-hd`: ~$30/1M chars | Free: 3 RPM / 200 req/day · Tier 2+: higher | ⚠️ Voice Engine (limited beta) | Chunked HTTP | **~1.5–2.5 days** | [README_openai_voice.md](README_openai_voice.md) |
| **Google Cloud TTS** | Closed / proprietary | Standard: $4/1M · WaveNet/Neural2: $16/1M · Studio: $160/1M | 1,000 RPM default | ❌ (no public cloning API) | gRPC streaming | **~2.5–3 days** | [README_google_voice.md](README_google_voice.md) |
| **Amazon Polly** | Closed / proprietary | Standard: $4/1M · Neural: $16/1M · Long-Form: $100/1M · Generative: $30/1M | 100 TPS default · 3,000 chars/req (sync) | ❌ | Sync stream / async S3 | **~2–3 days** | [README_polly_voice.md](README_polly_voice.md) |
| **Azure AI Speech** | Closed / proprietary | Neural: $16/1M · Neural HD: $24/1M · Personal Voice: ~$100/1M | 200 TPS default · 10,000 chars/req | ✅ Personal Voice (GA) | SDK real-time streaming | **~2–3 days** | [README_azure_voice.md](README_azure_voice.md) |
| **ElevenLabs** | Closed / proprietary | Free: 10K chars/mo · Starter: $5/30K · Pro: $99/500K · overage ~$200–300/1M | 2–10 concurrent requests (plan-dependent) | ✅ Instant + Professional cloning | `/stream` endpoint | **~1.5–2.5 days** | [README_elevenlabs_voice.md](README_elevenlabs_voice.md) |
| **Grok Voice (xAI)** | Closed / proprietary | **Unconfirmed** — check console.x.ai | **Unconfirmed** | **Unconfirmed** | WebSocket (LiveKit) | **~3.5–5 days** (includes research) | [README_grok_voice.md](README_grok_voice.md) |

---

## Cost at Scale (1 Million Characters)

| Provider | Cheapest option | Best quality option |
|----------|----------------|---------------------|
| Piper | **$0** | **$0** |
| OpenAI TTS | $15 (`tts-1`) | $30 (`tts-1-hd`) |
| Google Cloud TTS | $4 (Standard) | $160 (Studio) |
| Amazon Polly | $4 (Standard) | $100 (Long-Form) |
| Azure AI Speech | $16 (Neural) | ~$100 (Personal Voice) |
| ElevenLabs | ~$200 (Creator overage) | ~$300 (Pro overage) |
| Grok Voice (xAI) | Unconfirmed | Unconfirmed |

---

## Integration Effort Summary

| Provider | Effort | Key Complexity |
|----------|--------|----------------|
| Piper | ✅ Done | Wyoming protocol already integrated |
| OpenAI TTS | ~1.5–2.5 days | Mature SDK, minimal friction |
| ElevenLabs | ~1.5–2.5 days | Good SDK; cost is the main concern |
| Amazon Polly | ~2–3 days | `boto3` async wrapper + IAM setup |
| Azure AI Speech | ~2–3 days | Region config + large voice catalog |
| Google Cloud TTS | ~2.5–3 days | GCP auth (ADC / service accounts) |
| Grok Voice (xAI) | ~3.5–5 days | Endpoint/pricing still unconfirmed; WebSocket path |

---

## Recommended Integration Order

For the best return on effort, prioritize:

1. **OpenAI TTS** — fastest to ship, well-known to users, 6 built-in voices
2. **ElevenLabs** — best voice quality/cloning, strong community demand
3. **Amazon Polly** — widely used in enterprise; `boto3` familiar to AWS users
4. **Azure AI Speech** — largest voice catalog, best multilingual coverage
5. **Google Cloud TTS** — solid option if users already have GCP credentials
6. **Grok Voice (xAI)** — hold until pricing/rate limits are confirmed

> **Piper remains the default** for all offline / privacy-first / zero-cost use cases.
> Cloud backends are additive via `--backend <name>` CLI flag.

---

## Open Research Tasks (cross-provider)

- [ ] Confirm Grok Voice pricing and rate limits at console.x.ai
- [ ] Evaluate `eleven_flash_v2_5` latency for real-time use cases
- [ ] Test Google Neural2 vs. Azure Neural on the same text sample
- [ ] Benchmark Piper `high` quality models vs. OpenAI `tts-1` perceptual quality
- [ ] Decide on a unified `--backend` flag design before implementing any cloud provider

