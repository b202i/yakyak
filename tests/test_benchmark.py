import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest import mock
import wave

from yakyak.__main__ import main
from yakyak.benchmark import BENCHMARK_TEXT, run_benchmark, wav_duration


def wav_bytes(frames=1000):
    output = io.BytesIO()
    with wave.open(output, "wb") as audio:
        audio.setnchannels(1)
        audio.setsampwidth(2)
        audio.setframerate(100)
        audio.writeframes(b"\0\0" * frames)
    return output.getvalue()


class BenchmarkTests(unittest.TestCase):
    def setUp(self):
        self.output = io.StringIO()
        self.stdout = contextlib.redirect_stdout(self.output)
        self.stdout.__enter__()
        self.addCleanup(self.stdout.__exit__, None, None, None)
        self.options = dict(backend="kokoro", host="localhost", port=10200,
                            voice="af_heart", language="en-us", speed=1.0)

    def synthesize(self, command, **kwargs):
        kwargs["stdout"].write(wav_bytes())
        return subprocess.CompletedProcess(command, 0, stderr=b"")

    def test_warmup_is_excluded_and_ratio_uses_summed_times(self):
        # Ten seconds of speech per attempt; cold warm-up takes 100 seconds.
        with mock.patch("yakyak.benchmark.subprocess.run", side_effect=self.synthesize) as run:
            with mock.patch("yakyak.benchmark.time.perf_counter",
                            side_effect=[0, 100, 100, 105, 105, 115, 115, 120]):
                result = run_benchmark(**self.options)
        self.assertEqual(result, 0)
        self.assertIn("Warm-up (excluded)", self.output.getvalue())
        self.assertIn("Overall ratio: 1.500x (30.000s speech / 20.000s wall; 3 measured runs)",
                      self.output.getvalue())
        self.assertEqual(run.call_count, 4)
        for call in run.call_args_list:
            command = call.args[0]
            self.assertEqual(command[:3], [sys.executable, "-m", "yakyak"])
            self.assertNotIn("--benchmark", command)
            self.assertNotIn("-b", command)
            self.assertEqual(command[command.index("--voice") + 1], "af_heart")
            self.assertEqual(command[command.index("--audio-format") + 1], "wav")
            self.assertEqual(call.kwargs["input"], BENCHMARK_TEXT.encode())
            self.assertFalse(Path(call.kwargs["stdout"].name).exists())

    def test_example_ratios(self):
        for elapsed, ratio in ((10, "1.000x"), (5, "2.000x")):
            with self.subTest(elapsed=elapsed):
                self.output.seek(0)
                self.output.truncate()
                with mock.patch("yakyak.benchmark.measure", return_value=(10, elapsed)):
                    self.assertEqual(run_benchmark(**self.options, runs=1), 0)
                self.assertIn("Overall ratio: " + ratio, self.output.getvalue())

    def test_wyoming_forwards_endpoint_and_voice(self):
        self.options.update(backend="wyoming", host="test-host", port=10210,
                            voice="en_US-amy-medium")
        with mock.patch("yakyak.benchmark.subprocess.run", side_effect=self.synthesize) as run:
            self.assertEqual(run_benchmark(**self.options, runs=1), 0)
        command = run.call_args.args[0]
        self.assertEqual(command[command.index("--host") + 1], "test-host")
        self.assertEqual(command[command.index("--port") + 1], "10210")
        self.assertNotIn("--language", command)

    def test_empty_invalid_and_truncated_audio_fail_even_with_exit_zero(self):
        for data in (b"", b"not audio", wav_bytes(0), wav_bytes()[:-2]):
            with self.subTest(length=len(data)):
                def invalid_output(command, **kwargs):
                    kwargs["stdout"].write(data)
                    return subprocess.CompletedProcess(command, 0, stderr=b"synthesis failed")
                with mock.patch("yakyak.benchmark.subprocess.run", side_effect=invalid_output) as run:
                    with self.assertLogs(level="ERROR") as logs:
                        self.assertEqual(run_benchmark(**self.options), 1)
                self.assertEqual(run.call_count, 1)
                self.assertIn("invalid synthesis output", " ".join(logs.output))
                self.assertNotIn("Overall ratio", self.output.getvalue())

    def test_nonzero_exit_rejects_even_valid_audio(self):
        def failed(command, **kwargs):
            kwargs["stdout"].write(wav_bytes())
            return subprocess.CompletedProcess(command, 7, stderr=b"bad voice")
        with mock.patch("yakyak.benchmark.subprocess.run", side_effect=failed):
            with self.assertLogs(level="ERROR") as logs:
                self.assertEqual(run_benchmark(**self.options), 1)
        self.assertIn("synthesis exited 7: bad voice", " ".join(logs.output))

    def test_timeout_is_failure_and_stops_benchmark(self):
        with mock.patch("yakyak.benchmark.subprocess.run",
                        side_effect=subprocess.TimeoutExpired("yakyak", 2)) as run:
            with self.assertLogs(level="ERROR"):
                self.assertEqual(run_benchmark(**self.options, timeout=2), 1)
        self.assertEqual(run.call_count, 1)
        self.assertNotIn("Overall ratio", self.output.getvalue())

    def test_later_failure_does_not_report_partial_summary(self):
        with mock.patch("yakyak.benchmark.measure", side_effect=[(10, 5), (10, 5), ValueError("failed")]):
            with self.assertLogs(level="ERROR"):
                self.assertEqual(run_benchmark(**self.options), 1)
        self.assertNotIn("Overall ratio", self.output.getvalue())

    def test_blank_text_fails_without_synthesis(self):
        with mock.patch("yakyak.benchmark.measure") as measure:
            with self.assertLogs(level="ERROR"):
                self.assertEqual(run_benchmark(**self.options, text="  \n"), 1)
        measure.assert_not_called()

    def test_wav_duration_uses_sample_rate(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.wav"
            path.write_bytes(wav_bytes())
            self.assertEqual(wav_duration(path), 10)


class BenchmarkCliTests(unittest.TestCase):
    def test_both_aliases_use_default_text_without_reading_stdin(self):
        for flag in ("-b", "--benchmark"):
            with self.subTest(flag=flag):
                with mock.patch.object(sys, "argv", ["yakyak", flag, "--backend", "kokoro"]):
                    with mock.patch("yakyak.__main__.get_stdin", side_effect=AssertionError("stdin read")):
                        with mock.patch("yakyak.__main__.run_benchmark", return_value=0) as run:
                            self.assertEqual(main(), 0)
                run.assert_called_once_with("kokoro", "localhost", 10200, "af_heart", "en-us", 1.0,
                                            runs=3, timeout=600.0, text=BENCHMARK_TEXT)

    def test_custom_voice_file_and_run_options(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "passage.txt"
            path.write_text("A custom passage.")
            args = ["yakyak", "-b", "--backend", "kokoro", "--voice", "af_bella",
                    "--language", "en-gb", "--speed", "1.2", "-i", str(path),
                    "--benchmark-runs", "5", "--benchmark-timeout", "1200"]
            with mock.patch.object(sys, "argv", args):
                with mock.patch("yakyak.__main__.run_benchmark", return_value=1) as run:
                    self.assertEqual(main(), 1)
        run.assert_called_once_with("kokoro", "localhost", 10200, "af_bella", "en-gb", 1.2,
                                    runs=5, timeout=1200.0, text="A custom passage.")

    def test_default_backend_and_remote_host_are_preserved(self):
        with mock.patch.object(sys, "argv", ["yakyak", "-b", "--host", "flik.local", "-p", "10210"]):
            with mock.patch("yakyak.__main__.run_benchmark", return_value=0) as run:
                self.assertEqual(main(), 0)
        self.assertEqual(run.call_args.args[:4], ("wyoming", "flik.local", 10210, "en_US-amy-medium"))

    def test_bad_arguments_are_rejected(self):
        for extra in (["--benchmark-runs", "0"], ["--benchmark-runs", "-1"],
                      ["--benchmark-timeout", "nan"], ["--benchmark-timeout", "0"],
                      ["--benchmark-timeout", "inf"], ["--test", "wav"], ["--docker"],
                      ["--output-raw"], ["-o", "speech.wav"],
                      ["--backend", "kokoro", "--speed", "nan"]):
            with self.subTest(extra=extra):
                with mock.patch.object(sys, "argv", ["yakyak", "-b", *extra]):
                    with contextlib.redirect_stderr(io.StringIO()):
                        with self.assertRaises(SystemExit) as error:
                            main()
                self.assertEqual(error.exception.code, 2)

    def test_missing_input_file_returns_failure(self):
        with mock.patch.object(sys, "argv", ["yakyak", "-b", "-i", "missing-passage.txt"]):
            with self.assertLogs(level="ERROR"):
                self.assertEqual(main(), 1)


if __name__ == "__main__":
    unittest.main()
