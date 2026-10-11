"""ASR / TTS / Ask 边界测试。

全部使用 mock，不依赖真实 ASR/TTS/LLM provider。
覆盖：正常输入、无音源、空文件、识别/合成失败、text 兜底降级。
"""

from __future__ import annotations

import io
import struct
import tempfile
from unittest.mock import AsyncMock, MagicMock

import pytest

import httpx

_orig_Client = getattr(httpx, "_original_Client", None)
_orig_AsyncClient = getattr(httpx, "_original_AsyncClient", None)

if _orig_Client is not None:
    httpx.Client = _orig_Client
if _orig_AsyncClient is not None:
    httpx.AsyncClient = _orig_AsyncClient

from fastapi.testclient import TestClient


def _create_wav_bytes(duration_sec: int = 1) -> bytes:
    sample_rate = 16000
    num_samples = sample_rate * duration_sec
    pcm_data = b"\x00\x00" * num_samples

    buf = io.BytesIO()
    buf.write(b"RIFF")
    buf.write(struct.pack("<I", 36 + len(pcm_data)))
    buf.write(b"WAVEfmt ")
    buf.write(struct.pack("<IHHIIHH", 16, 1, 1, sample_rate, sample_rate * 2, 2, 16))
    buf.write(b"data")
    buf.write(struct.pack("<I", len(pcm_data)))
    buf.write(pcm_data)
    return buf.getvalue()


def _build_mock_container():
    container = MagicMock()

    container.asr_service = AsyncMock()
    container.asr_service.transcribe = AsyncMock(return_value="你好世界")

    tmp_audio = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
    tmp_audio.write(b"RIFF" + b"\x00" * 100)
    tmp_audio.close()

    container.tts_service = AsyncMock()
    container.tts_service.synthesize = AsyncMock(return_value=tmp_audio.name)
    container.tts_service.cleanup = AsyncMock()

    container.llm_service = AsyncMock()
    container.llm_service.chat = AsyncMock(return_value="我是小智AI")

    return container


@pytest.fixture()
def mock_container():
    return _build_mock_container()


@pytest.fixture()
def client(mock_container):
    from api.app import app

    async def _noop():
        pass

    app.router.on_startup = [_noop]
    app.router.on_shutdown = [_noop]

    app.state.service_container = mock_container
    app.state.config = {"server": {"auth_key": ""}}

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


class TestASREndpoint:
    def test_asr_normal_audio(self, client):
        wav_data = _create_wav_bytes()
        resp = client.post(
            "/api/v1/asr",
            files={"audio": ("test.wav", wav_data, "audio/wav")},
            data={"audio_format": "wav"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert body["text"] == "你好世界"

    def test_asr_no_audio(self, client):
        resp = client.post("/api/v1/asr")
        assert resp.status_code == 400

    def test_asr_empty_audio(self, client):
        resp = client.post(
            "/api/v1/asr",
            files={"audio": ("empty.wav", b"", "audio/wav")},
            data={"audio_format": "wav"},
        )
        assert resp.status_code == 400

    def test_asr_recognition_failure(self, client, mock_container):
        mock_container.asr_service.transcribe = AsyncMock(return_value=None)
        wav_data = _create_wav_bytes()
        resp = client.post(
            "/api/v1/asr",
            files={"audio": ("test.wav", wav_data, "audio/wav")},
            data={"audio_format": "wav"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "error"
        assert "识别" in body["message"]


class TestTTSEndpoint:
    def test_tts_normal_text(self, client):
        resp = client.post(
            "/api/v1/tts",
            data={"text": "你好世界", "audio_format": "wav"},
        )
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("audio/wav")

    def test_tts_empty_text(self, client):
        resp = client.post("/api/v1/tts", data={"text": ""})
        assert resp.status_code in (400, 422)

    def test_tts_missing_text(self, client):
        resp = client.post("/api/v1/tts")
        assert resp.status_code == 422

    def test_tts_synthesis_failure(self, client, mock_container):
        mock_container.tts_service.synthesize = AsyncMock(return_value=None)
        resp = client.post(
            "/api/v1/tts",
            data={"text": "测试合成失败", "audio_format": "wav"},
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "error"
        assert "合成" in body["message"]


class TestAskBoundary:
    def test_ask_normal_text_input(self, client):
        resp = client.post(
            "/api/v1/ask",
            data={
                "input_type": "text",
                "output_type": "text",
                "text": "你好",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        assert body["text"] == "我是小智AI"

    def test_ask_audio_no_audio_with_text_fallback(self, client, mock_container):
        resp = client.post(
            "/api/v1/ask",
            data={
                "input_type": "audio",
                "output_type": "text",
                "text": "兜底文本",
            },
        )
        if resp.status_code != 200:
            pytest.fail(f"Expected 200, got {resp.status_code}: {resp.text}")
        body = resp.json()
        assert body["status"] == "success"
        mock_container.llm_service.chat.assert_called_once()
        call_args = mock_container.llm_service.chat.call_args
        assert call_args[0][0] == "兜底文本"

    def test_ask_audio_no_audio_no_text(self, client):
        resp = client.post(
            "/api/v1/ask",
            data={
                "input_type": "audio",
                "output_type": "text",
            },
        )
        if resp.status_code != 200:
            pytest.fail(f"Expected 200, got {resp.status_code}: {resp.text}")
        body = resp.json()
        assert body["status"] == "error"
        assert "未检测到音源" in body["message"]

    def test_ask_audio_recognition_fail_with_text_fallback(self, client, mock_container):
        mock_container.asr_service.transcribe = AsyncMock(return_value=None)
        wav_data = _create_wav_bytes()
        resp = client.post(
            "/api/v1/ask",
            files={"audio": ("test.wav", wav_data, "audio/wav")},
            data={
                "input_type": "audio",
                "output_type": "text",
                "text": "兜底文本",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "success"
        call_args = mock_container.llm_service.chat.call_args
        assert call_args[0][0] == "兜底文本"

    def test_ask_audio_recognition_fail_no_text(self, client, mock_container):
        mock_container.asr_service.transcribe = AsyncMock(return_value=None)
        wav_data = _create_wav_bytes()
        resp = client.post(
            "/api/v1/ask",
            files={"audio": ("test.wav", wav_data, "audio/wav")},
            data={
                "input_type": "audio",
                "output_type": "text",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["status"] == "error"
        assert "无文本兜底" in body["message"] or "识别失败" in body["message"]