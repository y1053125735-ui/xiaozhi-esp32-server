import uuid
from fastapi import APIRouter, Request, HTTPException, File, UploadFile, Form, Depends
from fastapi.responses import FileResponse
from typing import Optional, Union
from loguru import logger
from api.schemas.request import InputType, OutputType
from api.schemas.response import AskResponse, ResponseType
from api.auth import verify_api_key

TAG = __name__
router = APIRouter(dependencies=[Depends(verify_api_key)])


@router.post("/ask", response_model=AskResponse, summary="智能问答接口")
async def ask(
    request: Request,
    input_type: InputType = Form(default=InputType.TEXT),
    output_type: OutputType = Form(default=OutputType.TEXT),
    text: Optional[str] = Form(default=None),
    audio: Optional[Union[UploadFile, str]] = File(default=None),
    session_id: Optional[str] = Form(default=None),
    voice_id: Optional[str] = Form(default=None),
    audio_format: str = Form(default="wav"),
):
    """
    智能问答接口

    - **input_type**: 输入类型（text / audio）
    - **output_type**: 输出类型（text / audio）
    - **text**: 文本输入（input_type=text 时必填）
    - **audio**: 音频文件（input_type=audio 时必填，支持 wav/mp3/pcm）
    - **session_id**: 会话ID（可选，用于维持上下文）
    - **voice_id**: 语音ID（可选，TTS 音色选择）
    - **audio_format**: 音频格式（wav / mp3 / pcm）
    """
    try:
        if isinstance(audio, str):
            audio = None

        service_container = request.app.state.service_container

        if not session_id:
            session_id = str(uuid.uuid4())

        if input_type == InputType.TEXT:
            if not text:
                raise HTTPException(status_code=400, detail="文本输入时 text 参数必填")
            user_text = text

        elif input_type == InputType.AUDIO:
            if not audio:
                raise HTTPException(status_code=400, detail="语音输入时 audio 文件必填")
            audio_data = await audio.read()
            user_text = await service_container.asr_service.transcribe(
                audio_data, audio_format
            )
            if not user_text:
                return AskResponse(
                    status=ResponseType.ERROR,
                    output_type=output_type.value,
                    session_id=session_id,
                    message="语音识别失败",
                )
        else:
            raise HTTPException(status_code=400, detail=f"不支持的输入类型: {input_type}")

        llm_response = await service_container.llm_service.chat(user_text, session_id)

        if output_type == OutputType.TEXT:
            return AskResponse(
                status=ResponseType.SUCCESS,
                output_type="text",
                text=llm_response,
                session_id=session_id,
            )

        else:
            audio_file = await service_container.tts_service.synthesize(
                llm_response, audio_format, voice_id
            )
            if not audio_file:
                return AskResponse(
                    status=ResponseType.ERROR,
                    output_type=output_type.value,
                    text=llm_response,
                    session_id=session_id,
                    message="语音合成失败，返回文本结果",
                )
            return FileResponse(
                audio_file,
                media_type=f"audio/{audio_format}",
                headers={
                    "X-Session-ID": session_id,
                    "X-Response-Text": llm_response,
                },
            )

    except HTTPException:
        raise
    except Exception as e:
        logger.bind(tag=TAG).error(f"/ask 接口错误: {e}")
        import traceback
        logger.bind(tag=TAG).error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))