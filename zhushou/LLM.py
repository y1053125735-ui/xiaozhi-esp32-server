"""LLM 服务 - 封装大语言模型对话逻辑"""
from typing import Optional, List, Dict, Any
from config.logger import setup_logging
from core.utils.dialogue import Message, Dialogue

TAG = __name__
logger = setup_logging()


class LLMService:
    """LLM 服务类"""

    def __init__(self, llm_provider, memory_provider, config: dict):
        self.llm = llm_provider
        self.memory = memory_provider
        self.config = config
        self.logger = setup_logging()
        self.dialogues: Dict[str, Dialogue] = {}

    async def chat(
            self,
            text: str,
            session_id: str,
            system_prompt: Optional[str] = None
    ) -> str:
        """
        与 LLM 进行对话

        Args:
            text: 用户输入文本
            session_id: 会话ID
            system_prompt: 系统提示词（可选）

        Returns:
            LLM 回复文本
        """
        try:
            if session_id not in self.dialogues:
                self.dialogues[session_id] = Dialogue()

                if system_prompt:
                    self.dialogues[session_id].put(
                        Message(role="system", content=system_prompt)
                    )
                elif "prompt" in self.config:
                    self.dialogues[session_id].put(
                        Message(role="system", content=self.config["prompt"])
                    )

            dialogue = self.dialogues[session_id]
            dialogue.put(Message(role="user", content=text))

            memory_str = ""
            if self.memory:
                memory_str = await self.memory.get_memory_text(session_id)

            response = await self.llm.response(
                None,
                dialogue,
                memory_str if memory_str else None
            )

            response_text = response.content if hasattr(response, 'content') else str(response)
            dialogue.put(Message(role="assistant", content=response_text))

            if self.memory:
                await self.memory.add_memory(
                    session_id,
                    [{"role": "user", "content": text},
                     {"role": "assistant", "content": response_text}]
                )

            return response_text

        except Exception as e:
            logger.bind(tag=TAG).error(f"LLM 对话失败: {e}")
            return "抱歉，我暂时无法回答您的问题。"

    def clear_session(self, session_id: str):
        """清除会话历史"""
        if session_id in self.dialogues:
            del self.dialogues[session_id]