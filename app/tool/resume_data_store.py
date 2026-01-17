"""
共享的简历数据存储

所有简历相关工具（cv_reader_agent, cv_analyzer_agent, cv_editor_agent）
共享同一个简历数据源，确保数据一致性。
"""

from typing import Optional, Dict

from app.agent.shared_state import AgentSharedState


class ResumeDataStore:
    """共享的简历数据存储"""

    _data: Optional[dict] = None
    _data_by_session: Dict[str, dict] = {}
    _shared_state_by_session: Dict[str, AgentSharedState] = {}

    @classmethod
    def set_data(cls, resume_data: dict, session_id: Optional[str] = None):
        """设置简历数据"""
        cls._data = resume_data
        if session_id:
            cls._data_by_session[session_id] = resume_data
            shared_state = cls._shared_state_by_session.get(session_id)
            if shared_state:
                shared_state.set("resume_data", resume_data)

    @classmethod
    def get_data(cls, session_id: Optional[str] = None) -> Optional[dict]:
        """获取简历数据"""
        if session_id:
            shared_state = cls._shared_state_by_session.get(session_id)
            if shared_state and shared_state.has("resume_data"):
                return shared_state.get("resume_data")
            if session_id in cls._data_by_session:
                return cls._data_by_session[session_id]
        return cls._data

    @classmethod
    def clear_data(cls, session_id: Optional[str] = None):
        """清空简历数据"""
        cls._data = None
        if session_id and session_id in cls._data_by_session:
            cls._data_by_session.pop(session_id, None)
            shared_state = cls._shared_state_by_session.get(session_id)
            if shared_state:
                shared_state.delete("resume_data")

    @classmethod
    def set_shared_state(cls, session_id: str, state: AgentSharedState):
        """绑定会话级 shared_state"""
        cls._shared_state_by_session[session_id] = state
