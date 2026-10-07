from pydantic import BaseModel, Field
from typing import Optional, Literal
from enum import Enum


class ResponseType(str, Enum):
    SUCCESS = "success"
    ERROR = "error"


class AskResponse(BaseModel):
    status: ResponseType = Field(
        default=ResponseType.SUCCESS,
        description="响应状态",
    )
    output_type: Literal["text", "audio"] = Field(
        description="输出类型",
    )
    text: Optional[str] = Field(
        default=None,
        description="文本输出内容（output_type=text 时返回，或语音识别的原始文本）",
    )
    session_id: str = Field(
        description="会话ID",
    )
    message: Optional[str] = Field(
        default=None,
        description="额外消息（如错误信息）",
    )