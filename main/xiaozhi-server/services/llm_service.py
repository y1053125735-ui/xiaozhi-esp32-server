from typing import Optional, Dict
from loguru import logger
from core.utils.dialogue import Message, Dialogue

TAG = __name__

MAX_SESSIONS = 1000
SESSION_TTL_SECONDS = 3600


class LLMService:
    def __init__(self, llm_provider, memory_provider, config: dict):
        self.llm = llm_provider
        self.memory = memory_provider
        self.config = config
        self.dialogues: Dict[str, Dialogue] = {}
        self.session_timestamps: Dict[str, float] = {}

    def _cleanup_expired_sessions(self):
        """清理过期会话"""
        import time
        current_time = time.time()
        expired_sessions = [
            session_id
            for session_id, timestamp in self.session_timestamps.items()
            if current_time - timestamp > SESSION_TTL_SECONDS
        ]
        for session_id in expired_sessions:
            self.dialogues.pop(session_id, None)
            self.session_timestamps.pop(session_id, None)

        if len(self.dialogues) > MAX_SESSIONS:
            sorted_sessions = sorted(
                self.session_timestamps.items(),
                key=lambda x: x[1]
            )
            to_remove = len(self.dialogues) - MAX_SESSIONS
            for session_id, _ in sorted_sessions[:to_remove]:
                self.dialogues.pop(session_id, None)
                self.session_timestamps.pop(session_id, None)

    async def chat(
            self,
            text: str,
            session_id: str,
            system_prompt: Optional[str] = None,
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
            import time
            self._cleanup_expired_sessions()

            if session_id not in self.dialogues:
                self.dialogues[session_id] = Dialogue()
                prompt = system_prompt or self.config.get("prompt", "你是一个智能助手。")
                self.dialogues[session_id].put(
                    Message(role="system", content=prompt)
                )

            self.session_timestamps[session_id] = time.time()

            dialogue = self.dialogues[session_id]
            dialogue.put(Message(role="user", content=text))

            memory_str = ""
            if self.memory:
                try:
                    memory_str = await self.memory.get_memory_text(session_id)
                except Exception:
                    memory_str = ""

            llm_dialogue = dialogue.get_llm_dialogue_with_memory(
                memory_str if memory_str else None
            )

            response_text = ""
            for token in self.llm.response(session_id, llm_dialogue):
                response_text += token

            dialogue.put(Message(role="assistant", content=response_text))

            if self.memory:
                try:
                    await self.memory.add_memory(
                        session_id,
                        [
                            {"role": "user", "content": text},
                            {"role": "assistant", "content": response_text},
                        ],
                    )
                except Exception:
                    pass

            return response_text

        except Exception as e:
            logger.bind(tag=TAG).error(f"LLM 对话失败: {e}")
            import traceback
            logger.bind(tag=TAG).error(traceback.format_exc())
            return "抱歉，我暂时无法回答您的问题。"

    def clear_session(self, session_id: str):
        """清除指定会话"""
        if session_id in self.dialogues:
            del self.dialogues[session_id]
        if session_id in self.session_timestamps:
            del self.session_timestamps[session_id]