from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum


class InputType(str, Enum):
    TEXT = "text"
    AUDIO = "audio"


class OutputType(str, Enum):
    TEXT = "text"
    AUDIO = "audio"


class AskRequest(BaseModel):
    input_type: InputType = Field(
        default=InputType.TEXT,
        description="输入类型：text（文本）或 audio（语音）",
    )
    output_type: OutputType = Field(
        default=OutputType.TEXT,
        description="输出类型：text（文本）或 audio（语音）",
    )
    text: Optional[str] = Field(
        default=None,
        description="文本输入内容（input_type=text 时必填）",
    )
    audio_format: Optional[Literal["wav", "mp3", "pcm"]] = Field(
        default="wav",
        description="音频格式（input_type=audio 时使用）",
    )
    session_id: Optional[str] = Field(
        default=None,
        description="会话ID，用于维持上下文（可选）",
    )
    voice_id: Optional[str] = Field(
        default=None,
        description="语音ID，用于TTS音色选择（可选）",
    )