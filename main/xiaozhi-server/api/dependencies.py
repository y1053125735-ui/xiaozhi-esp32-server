from typing import Dict, Any
from loguru import logger
from services.asr_service import ASRService
from services.llm_service import LLMService
from services.tts_service import TTSService

TAG = __name__


class ServiceContainer:
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.asr_service = None
        self.llm_service = None
        self.tts_service = None

    async def initialize(self):
        from config.logger import setup_logging
        from core.utils.modules_initialize import initialize_modules

        setup_logger = setup_logging(self.config)

        modules = initialize_modules(
            setup_logger,
            self.config,
            init_vad=False,
            init_asr=True,
            init_llm=True,
            init_tts=True,
            init_memory=True,
            init_intent=False,
        )

        asr = modules.get("asr")
        llm = modules.get("llm")
        tts = modules.get("tts")
        memory = modules.get("memory")

        self.asr_service = ASRService(asr, self.config)
        self.llm_service = LLMService(llm, memory, self.config)
        self.tts_service = TTSService(tts, self.config)

        logger.bind(tag=TAG).info("服务容器初始化完成")

    async def cleanup(self):
        if self.tts_service:
            await self.tts_service.cleanup()
        logger.bind(tag=TAG).info("服务容器资源已释放")