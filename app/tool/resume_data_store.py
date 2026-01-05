"""
共享的简历数据存储

所有简历相关工具（cv_reader_agent, cv_analyzer_agent, cv_editor_agent）
共享同一个简历数据源，确保数据一致性。
"""

from typing import Optional


class ResumeDataStore:
    """共享的简历数据存储"""

    _data: Optional[dict] = None

    @classmethod
    def set_data(cls, resume_data: dict):
        """设置简历数据"""
        cls._data = resume_data

    @classmethod
    def get_data(cls) -> Optional[dict]:
        """获取简历数据"""
        return cls._data

    @classmethod
    def clear_data(cls):
        """清空简历数据"""
        cls._data = None
