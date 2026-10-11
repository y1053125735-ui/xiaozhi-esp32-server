import uuid
from fastapi import APIRouter, Request, HTTPException, Form, Depends
from fastapi.responses import FileResponse
from typing import Optional
from urllib.parse import quote
from loguru import logger
from api.schemas.response import TTSResponse, ResponseType
from api.auth import verify_api_key

TAG = __name__
router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.post("/tts", summary="语音合成（TTS）")
async def tts(
    request: Request,
    text: str = Form(..., description="要转换为语音的文本"),
    audio_format: str = Form(default="wav", description="输出音频格式（wav/mp3）"),
    voice_id: Optional[str] = Form(default=None, description="语音ID（TTS 音色选择）"),
    session_id: Optional[str] = Form(default=None, description="会话ID（可选）"),
):
    """
    语音合成接口

    - **text**: 要转换的文本（必填）
    - **audio_format**: 输出音频格式（wav / mp3）
    - **voice_id**: 语音ID（可选，TTS 音色选择）
    - **session_id**: 会话ID（可选）
    """
    try:
        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="text 参数必填且不能为空")

        service_container = request.app.state.service_container

        if not session_id:
            session_id = str(uuid.uuid4())

        audio_file = await service_container.tts_service.synthesize(
            text, audio_format, voice_id
        )

        if not audio_file:
            return TTSResponse(
                status=ResponseType.ERROR,
                message="语音合成失败，请稍后重试",
            )

        return FileResponse(
            audio_file,
            media_type=f"audio/{audio_format}",
            headers={
                "X-Session-ID": session_id,
                "X-Response-Text": quote(text),
            },
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.bind(tag=TAG).error(f"/tts 接口错误: {e}")
        import traceback
        logger.bind(tag=TAG).error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))