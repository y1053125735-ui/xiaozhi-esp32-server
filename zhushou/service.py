"""依赖注入 - 服务容器"""
from typing import Dict, Any
from config.logger import setup_logging
from core.utils.modules_initialize import initialize_modules
from services.asr_service import ASRService
from services.llm_service import LLMService
from services.tts_service import TTSService

TAG = __name__
logger = setup_logging()


class ServiceContainer:
    """服务容器，管理所有业务服务"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = setup_logging(config)

        modules = initialize_modules(
            self.logger,
            config,
            init_vad=False,
            init_asr=True,
            init_llm=True,
            init_tts=True,
            init_memory=True,
            init_intent=False,
        )

        self.asr = modules.get("asr")
        self.llm = modules.get("llm")
        self.tts = modules.get("tts")
        self.memory = modules.get("memory")

        self.asr_service = ASRService(self.asr, config)
        self.llm_service = LLMService(self.llm, self.memory, config)
        self.tts_service = TTSService(self.tts, config)

        logger.bind(tag=TAG).info("服务容器初始化完成")

    async def cleanup(self):
        """清理资源"""
        if hasattr(self.asr, 'close'):
            await self.asr.close()
        if hasattr(self.tts, 'close'):
            await self.tts.close()


async def get_service_container(config: Dict[str, Any]) -> ServiceContainer:
    """获取服务容器实例"""
    return ServiceContainer(config)