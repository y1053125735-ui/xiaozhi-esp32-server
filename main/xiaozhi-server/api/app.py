from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger
from config.config_loader import load_config
from api.routes import ask, health
from api.dependencies import ServiceContainer
from core.utils.util import check_ffmpeg_installed
import uuid

TAG = __name__

app = FastAPI(
    title="小智 AI 服务 API",
    description="提供 ASR、LLM、TTS 一体化服务，支持文本和语音输入输出",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup_event():
    from config.logger import setup_logging
    check_ffmpeg_installed()
    config = await load_config()

    setup_logger = setup_logging(config)

    auth_key = config["server"].get("auth_key", "")
    if not auth_key or len(auth_key) == 0 or "你" in auth_key:
        auth_key = config.get("manager-api", {}).get("secret", "")
        if not auth_key or len(auth_key) == 0 or "你" in auth_key:
            auth_key = str(uuid.uuid4().hex)
    config["server"]["auth_key"] = auth_key

    service_container = ServiceContainer(config)
    await service_container.initialize()
    app.state.service_container = service_container
    app.state.config = config

    logger.bind(tag=TAG).info("FastAPI 服务启动成功")
    logger.bind(tag=TAG).info("API 文档地址: http://localhost:8004/docs")
    logger.bind(tag=TAG).info(f"API Key: {auth_key}")

@app.on_event("shutdown")
async def shutdown_event():
    if hasattr(app.state, "service_container"):
        await app.state.service_container.cleanup()
    logger.bind(tag=TAG).info("FastAPI 服务已关闭")


app.include_router(health.router, tags=["健康检查"])
app.include_router(ask.router, prefix="/api/v1", tags=["问答接口"])