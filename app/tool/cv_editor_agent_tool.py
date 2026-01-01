"""
CVEditor Agent Tool - 将 CVEditor Agent 包装成 Manus 可调用的工具

参考 MCPAgent 的集成方式，这个工具内部使用 CVEditor Agent 来处理简历编辑任务。
Manus 可以委托简历修改任务给这个工具。
"""

from typing import Optional, Any
import json
from app.tool.base import BaseTool, ToolResult


class CVEditorAgentTool(BaseTool):
    """CVEditor Agent 工具

    这是一个特殊的工具，它内部使用 CVEditor Agent 来处理简历编辑任务。
    Manus 可以委托简历修改任务给这个工具，CVEditor 会以 Agent 的方式处理。

    使用场景：
    - 用户要求修改简历中的某个字段
    - 用户要求添加新的工作经历
    - 用户要求删除某个项目
    - 用户要求重新格式化简历
    """

    name: str = "cv_editor_agent"
    description: str = """Edit and modify CV/Resume data through the CVEditor Agent.

Use this tool when the user wants to:
- Update personal information (name, email, phone, title)
- Add new entries (education, experience, projects, awards)
- Delete unnecessary information
- Reformat or restructure resume data

The tool requires:
- path: JSON path to the field (e.g., 'basic.name', 'education[0].school')
- action: Operation type - 'update', 'add', or 'delete'
- value: New value (required for update/add operations)

Examples:
- Update name: path='basic.name', action='update', value='张三'
- Add education: path='education', action='add', value={school:'北京大学', major:'计算机', ...}
- Delete item: path='experience[1]', action='delete'"""

    parameters: dict = {
        "type": "object",
        "properties": {
            "path": {
                "type": "string",
                "description": "JSON path to the resume field. Examples: 'basic.name', 'education[0].school', 'experience'"
            },
            "action": {
                "type": "string",
                "enum": ["update", "add", "delete"],
                "description": "Operation type: 'update' to modify, 'add' to append to array, 'delete' to remove"
            },
            "value": {
                "type": ["object", "string", "number", "array", "boolean", "null"],
                "description": "New value for update/add operations. For add, provide complete object. For update, provide the new value."
            }
        },
        "required": ["path", "action"]
    }

    # 全局简历数据引用（通过 server.py 设置）
    _global_resume_data_ref: Optional[dict] = None

    class Config:
        arbitrary_types_allowed = True

    @classmethod
    def set_resume_data(cls, resume_data: dict):
        """设置全局简历数据引用 - 这会被 server.py 调用"""
        cls._global_resume_data_ref = resume_data

    @classmethod
    def get_resume_data(cls) -> Optional[dict]:
        """获取当前简历数据"""
        return cls._global_resume_data_ref

    async def execute(self, path: str, action: str, value: Any = None) -> ToolResult:
        """执行简历编辑

        内部创建 CVEditor Agent 并运行它来处理编辑任务
        """
        if not self._global_resume_data_ref:
            return ToolResult(
                output="No resume data loaded. Please use load_resume_data tool first."
            )

        try:
            # 延迟导入避免循环依赖
            from app.agent.cv_editor import CVEditor

            # 创建 CVEditor Agent 实例
            cv_editor = CVEditor()

            # 加载简历数据（传入引用，所以修改会直接影响原始数据）
            cv_editor.load_resume(self._global_resume_data_ref)

            # 执行编辑操作
            result = await cv_editor.edit_resume(path, action, value)

            if result.get("success"):
                # 格式化成功消息
                output = f"✅ {result.get('message', 'Edit completed')}"
                if "new_value" in result:
                    new_val = result["new_value"]
                    if isinstance(new_val, dict):
                        new_val_str = json.dumps(new_val, ensure_ascii=False)
                    else:
                        new_val_str = str(new_val)
                    output += f"\nNew value: {new_val_str}"
                if "new_index" in result:
                    output += f"\nIndex: {result['new_index']}"
                return ToolResult(output=output)
            else:
                return ToolResult(
                    error=f"❌ Edit failed: {result.get('message', 'Unknown error')}"
                )

        except Exception as e:
            return ToolResult(error=f"CVEditor Agent error: {str(e)}")


class GetResumeStructure(BaseTool):
    """获取简历结构工具

    用于查看简历的当前结构和字段
    """

    name: str = "get_resume_structure"
    description: str = """Get the current structure and fields of the loaded resume.

Use this tool to:
- See what fields are available in the resume
- Understand the resume data structure
- Identify paths for editing

Returns a hierarchical view of all resume fields."""

    parameters: dict = {
        "type": "object",
        "properties": {},
    }

    async def execute(self) -> ToolResult:
        """获取简历结构"""
        # 使用类方法获取简历数据
        resume_data = CVEditorAgentTool.get_resume_data()
        if not resume_data:
            return ToolResult(
                output="No resume data loaded. Please use load_resume_data tool first."
            )

        def format_structure(data: dict, prefix: str = "", max_depth: int = 3, current_depth: int = 0) -> list:
            """递归格式化数据结构"""
            if current_depth >= max_depth:
                return []

            lines = []
            for key, value in data.items():
                if key.startswith("_"):  # 跳过私有字段
                    continue
                path = f"{prefix}.{key}" if prefix else key
                if isinstance(value, dict):
                    lines.append(f"📁 {path}/")
                    lines.extend(format_structure(value, path, max_depth, current_depth + 1))
                elif isinstance(value, list):
                    if value and isinstance(value[0], dict):
                        lines.append(f"📋 {path}[{len(value)} items]")
                        if value:
                            lines.extend(format_structure(value[0], f"{path}[0]", max_depth, current_depth + 1))
                            if len(value) > 1:
                                lines.append(f"  ... and {len(value) - 1} more items")
                    else:
                        lines.append(f"📋 {path}[{len(value)}] = {value}")
                else:
                    value_str = str(value)[:50]
                    if len(str(value)) > 50:
                        value_str = value_str + "..."
                    lines.append(f"📄 {path} = {value_str}")

            return lines

        try:
            lines = format_structure(resume_data)
            output = "📋 Resume Structure:\n\n" + "\n".join(lines)
            return ToolResult(output=output)
        except Exception as e:
            return ToolResult(error=f"Failed to get structure: {str(e)}")
