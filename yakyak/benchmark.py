"""CLI benchmark: generated speech seconds per wall-clock second."""

import logging
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import wave


BENCHMARK_TEXT = (
    "The quick brown fox jumps over the lazy dog. "
    "On a quiet morning, a friendly voice reads the news and explains a simple idea. "
    "At seven thirty, the train leaves the station. "
    "Which platform should we use? "
    "Clear speech should handle short sentences, longer phrases, and natural pauses."
)


def wav_duration(path):
    """Check the PCM data, not just the header or the CLI's exit status."""
    with wave.open(str(path), "rb") as audio:
        frames = audio.getnframes()
        rate = audio.getframerate()
        if frames <= 0 or rate <= 0:
            raise ValueError("synthesis produced an empty WAV")
        expected_bytes = frames * audio.getnchannels() * audio.getsampwidth()
        received_bytes = sum(len(chunk) for chunk in iter(lambda: audio.readframes(65536), b""))
        if received_bytes != expected_bytes:
            raise ValueError("synthesis produced a truncated WAV")
        return frames / rate


def measure(command, text, timeout):
    with tempfile.TemporaryDirectory(prefix="yakyak-benchmark-") as directory:
        output_path = Path(directory) / "speech.wav"
        with output_path.open("wb") as output:
            start = time.perf_counter()
            result = subprocess.run(
                command, input=text.encode("utf-8"), stdout=output,
                stderr=subprocess.PIPE, timeout=timeout, check=False,
            )
            elapsed = time.perf_counter() - start
        diagnostics = result.stderr.decode("utf-8", errors="replace").strip()
        if result.returncode:
            raise ValueError("synthesis exited {}: {}".format(result.returncode, diagnostics[-2000:]))
        try:
            duration = wav_duration(output_path)
        except (OSError, EOFError, wave.Error, ValueError) as error:
            raise ValueError("invalid synthesis output: {}\n{}".format(error, diagnostics[-2000:])) from error
        return duration, elapsed


def run_benchmark(backend, host, port, voice, language, speed,
                  runs=3, timeout=600.0, text=BENCHMARK_TEXT):
    """Print one excluded warm-up and measured runs; return a CLI exit status."""
    if not text.strip():
        logging.error("Benchmark input text must not be empty")
        return 1

    # A fresh CLI process includes startup and model loading in every timing.
    # The benchmark flag is deliberately omitted to avoid recursive benchmarks.
    command = [
        sys.executable, "-m", "yakyak", "--backend", backend,
        "--voice", voice, "--audio-format", "wav", "--output-file", "stdout",
    ]
    if backend == "kokoro":
        command += ["--language", language, "--speed", str(speed)]
    else:
        command += ["--host", host, "--port", str(port)]

    print("Benchmark: backend={}, voice={}".format(backend, voice), flush=True)
    print("Ratio = speech seconds / wall seconds; higher is faster.", flush=True)
    total_speech = 0.0
    total_wall = 0.0
    try:
        for index in range(runs + 1):
            label = "Warm-up (excluded)" if index == 0 else "Run {}".format(index)
            print("{}: synthesizing...".format(label), flush=True)
            duration, elapsed = measure(command, text, timeout)
            print("  speech={:.3f}s  wall={:.3f}s  ratio={:.3f}x".format(
                duration, elapsed, duration / elapsed), flush=True)
            if index:
                total_speech += duration
                total_wall += elapsed
    except subprocess.TimeoutExpired:
        logging.error("Benchmark synthesis timed out after %gs", timeout)
        return 1
    except (OSError, ValueError) as error:
        logging.error("Benchmark failed: %s", error)
        return 1
    except KeyboardInterrupt:
        logging.error("Benchmark interrupted")
        return 1

    print("Overall ratio: {:.3f}x ({:.3f}s speech / {:.3f}s wall; {} measured runs)".format(
        total_speech / total_wall, total_speech, total_wall, runs), flush=True)
    return 0
