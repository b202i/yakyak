# Supporting Piper TTS in YakYak

This document tracks verified facts, open questions, and integration tasks for
Piper TTS — YakYak's **current default** TTS backend (via Wyoming protocol).

---

## ✅ Verified Facts (as of March 2026)

| Item | Detail |
|------|--------|
| Project | [rhasspy/piper](https://github.com/rhasspy/piper) |
| Transport | Wyoming protocol (TCP socket) — already integrated in YakYak |
| Python SDK | `wyoming` (`pip install wyoming`) |
| Authentication | None — local service, no API key |
| Voices | 900+ ONNX voice models across 50+ languages |
| Voice quality levels | `x_low`, `low`, `medium`, `high` (`.onnx` model files) |
| Output format | WAV (16-bit PCM) |
| Inference | Local CPU / GPU (no cloud dependency) |
| Source model | **Open source** — Apache 2.0 |
| Cost | **Free** — no per-character or per-request charges |
| Rate limits | None — limited only by local hardware |
| Deployment | Docker (`docker run rhasspy/wyoming-piper ...`) or native binary |

---

## 💰 Pricing

**Free.** Runs entirely on local hardware. No API calls, no per-character billing,
no vendor lock-in.

---

## 🚦 Rate Limits

None. Throughput is bounded only by the host machine's CPU/GPU.

---

## ❓ Open Questions

| Item | Status |
|------|--------|
| GPU-accelerated inference on Apple Silicon | **Partial** — tested on x86; MPS path experimental |
| Voice fine-tuning / custom training | **Supported** — see piper-train repo; effort ~1–5 days |
| SSML support | **Minimal** — basic pause/rate tags only |

---

## Current Integration in YakYak

Piper is already supported via `WyomingTtsClient` in `yakyak/yakyak.py`.
No new implementation is needed. This document exists for comparison purposes.

Default usage:

```bash
# Start Piper via Docker
docker run -it -p 10200:10200 rhasspy/wyoming-piper \
  --voice en_US-lessac-medium

# Run YakYak (default backend = wyoming/piper)
yakyak "Hello world"
```

---

## Strengths vs. Cloud Providers

| Factor | Piper | Cloud TTS |
|--------|-------|-----------|
| Cost | Free | $4–$300 / 1M chars |
| Privacy | 100% local | Data sent to vendor |
| Latency | <100 ms (local) | 200–800 ms (network) |
| Voice quality | Good (`high` models) | Excellent (Neural/Studio) |
| Voice cloning | Not supported | Supported (some providers) |
| Offline use | ✅ Yes | ❌ No |
| Setup effort | Docker required | API key only |

---

## Estimated Effort to Maintain

Already integrated. Ongoing effort is minimal:
- Model updates: download new `.onnx` files as rhasspy releases them
- Wyoming protocol: stable; no breaking changes expected

