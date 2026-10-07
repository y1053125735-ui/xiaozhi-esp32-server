import os
import uuid
import time
import tempfile
from typing import Optional
from loguru import logger

TAG = __name__


class TTSService:
    def __init__(self, tts_provider, config: dict):
        self.tts = tts_provider
        self.config = config
        self.audio_dir = os.path.join(
            tempfile.gettempdir(), f"xiaozhi_tts_{os.getpid()}"
        )
        os.makedirs(self.audio_dir, exist_ok=True)

    async def synthesize(
        self,
        text: str,
        output_format: str = "wav",
        voice_id: Optional[str] = None,
    ) -> Optional[str]:
        """
        将文本转换为语音文件

        Args:
            text: 要转换的文本
            output_format: 输出格式（wav/mp3）
            voice_id: 语音ID（可选，保留扩展）

        Returns:
            音频文件路径，失败返回 None
        """
        try:
            audio_file = os.path.join(
                self.audio_dir,
                f"{uuid.uuid4().hex}.{output_format}",
            )

            result = await self.tts.text_to_speak(text, audio_file)

            if result is None:
                audio_bytes = result
                if audio_bytes and isinstance(audio_bytes, bytes):
                    with open(audio_file, "wb") as f:
                        f.write(audio_bytes)
                else:
                    logger.bind(tag=TAG).warning("TTS 返回空结果，尝试使用 to_tts 方法")
                    audio_file = self.tts.to_tts(text)
                    if not audio_file or not os.path.exists(audio_file):
                        return None

            if os.path.exists(audio_file):
                return audio_file
            return None

        except Exception as e:
            logger.bind(tag=TAG).error(f"TTS 合成失败: {e}")
            import traceback
            logger.bind(tag=TAG).error(traceback.format_exc())
            return None

    async def cleanup(self):
        """清理临时音频文件"""
        try:
            if os.path.exists(self.audio_dir):
                current_time = time.time()
                for filename in os.listdir(self.audio_dir):
                    file_path = os.path.join(self.audio_dir, filename)
                    if os.path.isfile(file_path):
                        file_age_hours = (current_time - os.path.getmtime(file_path)) / 3600
                        if file_age_hours > 1:
                            os.remove(file_path)
        except Exception as e:
            logger.bind(tag=TAG).error(f"TTS 清理临时文件失败: {e}")