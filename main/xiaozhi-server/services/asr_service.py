import io
import wave
import tempfile
import os
from typing import Optional, List
from loguru import logger

TAG = __name__


class ASRService:
    def __init__(self, asr_provider, config: dict):
        self.asr = asr_provider
        self.config = config

    async def transcribe(
        self,
        audio_data: bytes,
        audio_format: str = "wav",
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
                pcm_data = self._convert_to_pcm(audio_data, audio_format)

            pcm_frames = [
                pcm_data[i : i + 1920] for i in range(0, len(pcm_data), 1920)
            ]

            result, _ = await self.asr.speech_to_text_wrapper(
                pcm_frames, session_id="api"
            )

            if isinstance(result, dict):
                return result.get("content", "")
            return result

        except Exception as e:
            logger.bind(tag=TAG).error(f"ASR 转写失败: {e}")
            import traceback
            logger.bind(tag=TAG).error(traceback.format_exc())
            return None

    def _convert_to_pcm(self, audio_data: bytes, audio_format: str) -> bytes:
        from pydub import AudioSegment

        tmp_path = None
        try:
            suffix = f".{audio_format}"
            with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
                tmp.write(audio_data)
                tmp_path = tmp.name

            audio = AudioSegment.from_file(tmp_path, format=audio_format)
            audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
            return audio.raw_data
        finally:
            if tmp_path and os.path.exists(tmp_path):
                os.unlink(tmp_path)