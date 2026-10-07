"""
FastAPI 应用入口 - 提供 RESTful API 接口
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from config.logger import setup_logging
from config.settings import load_config
from api.routes import ask, health
from api.dependencies import get_service_container
from core.utils.util import check_ffmpeg_installed

TAG = __name__
logger = setup_logging()

app = FastAPI(
    title="小智 AI 服务 API",
    description="提供 ASR、LLM、TTS 一体化服务，支持文本和语音输入输出",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

service_container = None


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化"""
    global service_container
    check_ffmpeg_installed()
    config = await load_config()

    auth_key = config["server"].get("auth_key", "")
    if not auth_key or len(auth_key) == 0 or "你" in auth_key:
        import uuid
        auth_key = str(uuid.uuid4().hex)
    config["server"]["auth_key"] = auth_key

    service_container = await get_service_container(config)
    app.state.service_container = service_container
    app.state.config = config

    logger.bind(tag=TAG).info("FastAPI 服务启动成功")
    logger.bind(tag=TAG).info("API 文档地址: http://localhost:8004/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    if service_container:
        await service_container.cleanup()
    logger.bind(tag=TAG).info("FastAPI 服务已关闭")


app.include_router(health.router, tags=["健康检查"])
app.include_router(ask.router, prefix="/api/v1", tags=["问答接口"])