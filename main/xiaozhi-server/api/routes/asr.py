import uuid
from fastapi import APIRouter, Request, HTTPException, File, UploadFile, Form, Depends
from typing import Optional, Union
from loguru import logger
from api.schemas.response import ASRResponse, ResponseType
from api.auth import verify_api_key

TAG = __name__
router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.post("/asr", response_model=ASRResponse, summary="语音识别（ASR）")
async def asr(
    request: Request,
    audio: Optional[Union[UploadFile, str]] = File(default=None),
    audio_format: str = Form(default="wav"),
    session_id: Optional[str] = Form(default=None),
):
    """
    语音识别接口

    - **audio**: 音频文件（必填，支持 wav/mp3/pcm）
    - **audio_format**: 音频格式（wav / mp3 / pcm）
    - **session_id**: 会话ID（可选）
    """
    try:
        if isinstance(audio, str):
            audio = None

        if not audio:
            raise HTTPException(status_code=400, detail="音频文件必填，请上传音频文件")

        service_container = request.app.state.service_container

        if not session_id:
            session_id = str(uuid.uuid4())

        audio_data = await audio.read()
        if not audio_data:
            raise HTTPException(status_code=400, detail="上传的音频文件为空，请检查输入")

        user_text = await service_container.asr_service.transcribe(
            audio_data, audio_format
        )

        if not user_text:
            return ASRResponse(
                status=ResponseType.ERROR,
                message="语音识别失败，未识别到有效内容",
            )

        return ASRResponse(
            status=ResponseType.SUCCESS,
            text=user_text,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.bind(tag=TAG).error(f"/asr 接口错误: {e}")
        import traceback
        logger.bind(tag=TAG).error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))