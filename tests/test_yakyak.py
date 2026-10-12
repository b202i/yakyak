import asyncio
import io
import os
import sys
import unittest
import wave
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

from wyoming.audio import AudioChunk, AudioStart, AudioStop
from wyoming.tts import Synthesize

from yakyak.__main__ import main
from yakyak.yakyak import WyomingTtsClient, kokoro_tts_server, run_test


class FakeAsyncTcpClient:
    def __init__(self, host, port, responses):
        self.host = host
        self.port = port
        self.responses = iter(responses)
        self.written_event = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_value, traceback):
        return False

    async def write_event(self, event):
        self.written_event = event

    async def read_event(self):
        return next(self.responses, None)


class WyomingTtsClientTests(unittest.TestCase):
    def test_sends_voice_and_assembles_audio_chunks_as_wav(self):
        audio_bytes = b"\x01\x00\x02\x00"
        client = FakeAsyncTcpClient(
            "test-host",
            10210,
            [
                AudioStart(rate=24000, width=2, channels=1).event(),
                AudioChunk(rate=24000, width=2, channels=1, audio=audio_bytes).event(),
                AudioStop().event(),
            ],
        )

        with mock.patch("yakyak.yakyak.AsyncTcpClient", return_value=client):
            audio_format, wav_data = asyncio.run(
                WyomingTtsClient("test-host", 10210).get_tts_audio(
                    "Hello Kokoro", voice_name="af_heart"
                )
            )

        request = Synthesize.from_event(client.written_event)
        self.assertEqual(request.text, "Hello Kokoro")
        self.assertEqual(request.voice.name, "af_heart")
        self.assertEqual(audio_format, "wav")
        with wave.open(io.BytesIO(wav_data), "rb") as wav_file:
            self.assertEqual(wav_file.getframerate(), 24000)
            self.assertEqual(wav_file.getnchannels(), 1)
            self.assertEqual(wav_file.getsampwidth(), 2)
            self.assertEqual(wav_file.readframes(wav_file.getnframes()), audio_bytes)


class RunTestTests(unittest.TestCase):
    def test_rejects_unsupported_audio_format(self):
        with self.assertRaises(ValueError):
            run_test("localhost", 10200, "ogg")

    def test_offline_service_returns_failure_without_synthesis(self):
        with mock.patch("yakyak.yakyak.is_server_online", return_value=False):
            with mock.patch("yakyak.yakyak.piper_tts_server") as synthesize:
                result = run_test("localhost", 10210, "wav", "af_heart")

        self.assertEqual(result, (False, "Server localhost:10210 is offline"))
        synthesize.assert_not_called()

    def test_success_uses_selected_voice_and_removes_temporary_output(self):
        synthesized = {}

        async def fake_synthesis(host, port, text, output_file, audio_format, voice):
            synthesized.update(
                host=host,
                port=port,
                text=text,
                output_file=output_file,
                audio_format=audio_format,
                voice=voice,
            )
            with open(output_file, "wb") as output:
                output.write(b"audio")

        with mock.patch("yakyak.yakyak.is_server_online", return_value=True):
            with mock.patch("yakyak.yakyak.piper_tts_server", new=fake_synthesis):
                result = run_test("localhost", 10210, "wav", "af_heart")

        self.assertEqual(result, (True, "Success, test: wav"))
        self.assertEqual(synthesized["voice"], "af_heart")
        self.assertEqual(synthesized["audio_format"], "wav")
        self.assertFalse(os.path.exists(synthesized["output_file"]))

    def test_empty_synthesis_output_returns_failure(self):
        async def fake_synthesis(host, port, text, output_file, audio_format, voice):
            return None

        with mock.patch("yakyak.yakyak.is_server_online", return_value=True):
            with mock.patch("yakyak.yakyak.piper_tts_server", new=fake_synthesis):
                result = run_test("localhost", 10210, "wav", "af_heart")

        self.assertEqual(result, (False, "Fail, test: wav"))


class CliTests(unittest.TestCase):
    def test_test_command_forwards_selected_voice(self):
        arguments = [
            "yakyak",
            "--host", "localhost",
            "--port", "10210",
            "--voice", "af_heart",
            "--test", "wav",
        ]
        with mock.patch.object(sys, "argv", arguments):
            with mock.patch("yakyak.__main__.run_test") as run_test_mock:
                main()

        run_test_mock.assert_called_once_with("localhost", 10210, "wav", "af_heart")

    def test_kokoro_backend_routes_to_local_test(self):
        arguments = ["yakyak", "--backend", "kokoro", "--test", "wav"]
        with mock.patch.object(sys, "argv", arguments):
            with mock.patch("yakyak.__main__.run_kokoro_test") as test_mock:
                main()

        test_mock.assert_called_once_with("wav", "af_heart", "en-us", 1.0)

    def test_kokoro_invalid_voice_returns_error_status(self):
        arguments = ["yakyak", "--backend", "kokoro", "--voice", "en_GB-cori-medium"]
        with mock.patch.object(sys, "argv", arguments):
            with mock.patch("yakyak.__main__.get_stdin", return_value="Hello"):
                with mock.patch(
                    "yakyak.__main__.kokoro_tts_server",
                    side_effect=ValueError("Voice en_GB-cori-medium not found"),
                ):
                    result = main()

        self.assertEqual(result, 1)


class KokoroTests(unittest.TestCase):
    def test_synthesizes_with_requested_voice_language_and_speed(self):
        fake_kokoro = mock.Mock()
        fake_kokoro.create.return_value = ([0.1, -0.1], 24000)
        fake_module = SimpleNamespace(Kokoro=mock.Mock(return_value=fake_kokoro))
        fake_soundfile = SimpleNamespace(
            write=mock.Mock(side_effect=lambda output, audio, rate, format: output.write(b"wav"))
        )

        with mock.patch.dict(sys.modules, {
            "kokoro_onnx": fake_module,
            "soundfile": fake_soundfile,
        }):
            with mock.patch("yakyak.yakyak._download_kokoro_assets", return_value=(Path("model.onnx"), Path("voices.bin"))):
                with mock.patch("builtins.open", mock.mock_open()) as output_file:
                    asyncio.run(
                        kokoro_tts_server(
                            "Hello", "speech.wav", "wav", "af_bella", "en-us", 1.2
                        )
                    )

        fake_module.Kokoro.assert_called_once_with("model.onnx", "voices.bin")
        fake_kokoro.create.assert_called_once_with(
            "Hello", voice="af_bella", speed=1.2, lang="en-us"
        )
        output_file().write.assert_called_once_with(b"wav")

    def test_rejects_unsupported_format_before_loading_runtime(self):
        with self.assertRaises(ValueError):
            asyncio.run(kokoro_tts_server("Hello", "speech.ogg", "ogg"))


if __name__ == "__main__":
    unittest.main()
