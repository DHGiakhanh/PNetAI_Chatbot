"""Summarize session use case."""

from __future__ import annotations

import logging

from pydantic import UUID4

from pnetai_chatbot.application.ports.history_repo_port import IHistoryRepository
from pnetai_chatbot.application.ports.llm_port import ILLMAdapter
from pnetai_chatbot.application.ports.session_repo_port import ISessionRepository

logger = logging.getLogger(__name__)


class SummarizeSessionUseCase:
    """Use case to compress conversation logs into a concise session context summary."""

    def __init__(
        self,
        session_repository: ISessionRepository,
        history_repository: IHistoryRepository,
        llm: ILLMAdapter,
    ) -> None:
        """Initialize the SummarizeSessionUseCase.

        Args:
            session_repository: The session database repository port.
            history_repository: The message history database repository port.
            llm: The LLM adapter used to generate the summary text.
        """
        self._session_repo = session_repository
        self._history_repo = history_repository
        self._llm = llm

    async def execute(self, session_id: UUID4) -> str:
        """Execute the use case to generate and persist a session summary.

        Args:
            session_id: The unique identifier of the session.

        Returns:
            The generated summary text.
        """
        logger.info("Auto-summarizing chat session: %s", session_id)

        # 1. Fetch the last 20 messages for context
        messages = await self._history_repo.get_by_session(
            session_id=session_id, limit=20
        )
        if not messages:
            logger.info("No messages found in history. Skipping summarization.")
            return ""

        # 2. Retrieve existing summary as context
        session = await self._session_repo.get_by_id(session_id)
        existing_summary = session.summary if session else ""

        # 3. Format history for the LLM
        history_str = ""
        for msg in messages:
            role_val = msg.role.value if hasattr(msg.role, "value") else str(msg.role)
            history_str += f"- {role_val.capitalize()}: {msg.content}\n"

        prompt = (
            f"Bản tóm tắt cũ (nếu có):\n{existing_summary or 'Chưa có tóm tắt.'}\n\n"
            f"Các tin nhắn mới nhất trong hội thoại:\n{history_str}\n\n"
            "Hãy tạo một bản tóm tắt ngắn gọn và súc tích (dưới 300 từ) "
            "bằng tiếng Việt ghi nhận:\n"
            "- Các chủ đề chính người dùng đang quan tâm (nhu cầu dinh dưỡng, "
            "triệu chứng bệnh, v.v.).\n"
            "- Thông tin cá nhân đã chia sẻ (loại thú cưng, giống, tên, tuổi).\n"
            "- Các sản phẩm hoặc dịch vụ cụ thể đã hỏi.\n"
            "- Trạng thái vấn đề (đã giải quyết xong hay đang chờ thêm tư vấn).\n"
            "Đảm bảo bản tóm tắt khách quan, tập trung vào sự thật "
            "và không chứa lời thoại thừa."
        )

        try:
            response = await self._llm.chat(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
            )
            summary_text = response.text.strip()
            # 4. Update the summary in the database
            await self._session_repo.update_summary(session_id, summary_text)
            logger.info(
                "Successfully generated and saved summary for session %s",
                session_id,
            )
            return summary_text
        except Exception as e:
            logger.error("LLM generation failed in SummarizeSessionUseCase: %s", e)
            return existing_summary or ""
