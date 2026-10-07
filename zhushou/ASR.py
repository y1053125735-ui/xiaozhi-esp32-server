"""ASR 服务 - 封装语音识别逻辑"""
import io
import wave
import tempfile
from typing import Optional, Tuple
from config.logger import setup_logging
from core.providers.asr.base import ASRProviderBase

TAG = __name__
logger = setup_logging()


class ASRService:
    """ASR 服务类"""

    def __init__(self, asr_provider: ASRProviderBase, config: dict):
        self.asr = asr_provider
        self.config = config
        self.logger = setup_logging()

    async def transcribe(
            self,
            audio_data: bytes,
            audio_format: str = "wav"
    ) -> Optional[str]:
        """
        将音频转换为文本

        Args:
            audio_data: 音频二进制数据
            audio_format: 音频格式（wav/mp3/pcm）

        Returns:
            识别出的文本，失败返回 None
        """
        try:
            if audio_format == "pcm":
                pcm_data = audio_data
            else:
                pcm_data = await self._convert_to_pcm(audio_data, audio_format)

            pcm_frames = [pcm_data[i:i + 1920] for i in range(0, len(pcm_data), 1920)]

            result = await self.asr.speech_to_text_wrapper(
                pcm_frames,
                session_id=None
            )

            if isinstance(result, tuple) and len(result) >= 1:
                text = result[0]
                if isinstance(text, dict):
                    return text.get("content", "")
                return text

            return None

        except Exception as e:
            logger.bind(tag=TAG).error(f"ASR 转写失败: {e}")
            return None

    async def _convert_to_pcm(self, audio_data: bytes, audio_format: str) -> bytes:
        """将音频格式转换为 PCM"""
        from pydub import AudioSegment

        with tempfile.NamedTemporaryFile(suffix=f".{audio_format}", delete=False) as tmp_file:
            tmp_file.write(audio_data)
            tmp_file_path = tmp_file.name

        try:
            audio = AudioSegment.from_file(tmp_file_path, format=audio_format)
            audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            return audio.raw_data
        finally:
            import os
            os.unlink(tmp_file_path)