from app.tool.base import BaseTool
from app.tool.bash import Bash
from app.tool.browser_use_tool import BrowserUseTool
from app.tool.create_chat_completion import CreateChatCompletion
from app.tool.cv_analyzer_agent_tool import CVAnalyzerAgentTool
from app.tool.cv_editor_agent_tool import CVEditorAgentTool, GetResumeStructure
from app.tool.cv_reader_agent_tool import CVReaderAgentTool
from app.tool.cv_reader_tool import ReadCVContext
from app.tool.planning import PlanningTool
from app.tool.str_replace_editor import StrReplaceEditor
from app.tool.terminate import Terminate
from app.tool.tool_collection import ToolCollection
from app.tool.web_search import WebSearch

# Crawl4ai 可能有额外依赖，设为可选
try:
    from app.tool.crawl4ai import Crawl4aiTool
except ImportError:
    Crawl4aiTool = None


__all__ = [
    "BaseTool",
    "Bash",
    "BrowserUseTool",
    "Terminate",
    "StrReplaceEditor",
    "WebSearch",
    "ToolCollection",
    "CreateChatCompletion",
    "PlanningTool",
    "ReadCVContext",
    "CVReaderAgentTool",
    "CVAnalyzerAgentTool",
    "CVEditorAgentTool",
    "GetResumeStructure",
]

if Crawl4aiTool:
    __all__.append("Crawl4aiTool")
