"""
Conversation State Manager - Manages conversation state and intent recognition

This module preserves the logic from the original conversation_manager.py,
separated from the message history management.
"""

from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field
from datetime import datetime
import json

from app.logger import logger


class ConversationState(str, Enum):
    """对话状态"""
    IDLE = "idle"
    GREETING = "greeting"
    RESUME_LOADED = "resume_loaded"
    ANALYZING = "analyzing"
    OPTIMIZING = "optimizing"
    WAITING_ANSWER = "waiting_answer"
    EDITING = "editing"


class Intent(str, Enum):
    """用户意图"""
    GREETING = "greeting"
    LOAD_RESUME = "load_resume"
    VIEW_RESUME = "view_resume"
    ANALYZE = "analyze"
    OPTIMIZE = "optimize"
    OPTIMIZE_SECTION = "optimize_section"
    ANSWER_QUESTION = "answer_question"
    CONFIRM = "confirm"
    CANCEL = "cancel"
    UNKNOWN = "unknown"


class OptimizationContext(BaseModel):
    """优化上下文 - 追踪优化流程状态"""
    section: str = ""
    current_question: int = 0
    answers: Dict[str, str] = Field(default_factory=dict)
    started_at: Optional[datetime] = None


class ConversationContext(BaseModel):
    """对话上下文"""
    state: ConversationState = ConversationState.IDLE
    resume_loaded: bool = False
    last_tool_used: str = ""
    last_ai_response: str = ""
    optimization: OptimizationContext = Field(default_factory=OptimizationContext)
    history_summary: str = ""
    turn_count: int = 0


class ConversationStateManager:
    """
    对话状态管理器

    与原 ConversationManager 的区别：
    - 不管理消息历史（由 ChatHistoryManager 负责）
    - 只负责状态机和意图识别
    """

    def __init__(self, llm=None):
        """
        初始化对话状态管理器

        Args:
            llm: LLM 客户端实例，用于意图识别
        """
        self.context = ConversationContext()
        self.llm = llm

    async def classify_intent_with_llm(
        self,
        user_input: str,
        conversation_history: List[Any] = None,
        last_ai_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        使用 LLM 进行意图分类

        Args:
            user_input: 用户输入
            conversation_history: 对话历史（Message 对象列表）
            last_ai_message: 最后一条 AI 消息内容

        Returns:
            {
                "intent": Intent,
                "confidence": float,
                "extracted_info": {
                    "section": str,
                    "question": str,
                    "answer_type": str
                },
                "reasoning": str
            }
        """
        if not self.llm:
            logger.warning("LLM 客户端未设置，回退到默认意图")
            return {
                "intent": Intent.UNKNOWN,
                "confidence": 0.0,
                "extracted_info": {},
                "reasoning": "LLM 客户端未设置"
            }

        # 构建对话历史摘要
        history_text = ""
        if conversation_history:
            recent_messages = conversation_history[-5:]
            history_parts = []
            for msg in recent_messages:
                if hasattr(msg, 'role') and hasattr(msg, 'content'):
                    role = "用户" if msg.role == "user" else "AI"
                    content = msg.content[:200] if msg.content else ""
                    if content:
                        history_parts.append(f"{role}: {content}")
            history_text = "\n".join(history_parts)

        # 构建意图识别提示词
        prompt = f"""你是一个专业的意图识别助手。根据用户输入和对话上下文，准确识别用户的真实意图。

## 对话历史
{history_text if history_text else "无"}

## 最后一条AI消息
{last_ai_message if last_ai_message else "无"}

## 用户当前输入
"{user_input}"

## 意图类型说明
- greeting: 问候（你好、hi、hello等）
- load_resume: 加载简历（加载、上传、导入简历等）
- view_resume: 查看/介绍简历（看看简历、介绍简历、简历内容等）
- analyze: 分析简历（分析、诊断、评估简历等）
- optimize: 优化简历（整体优化，不指定具体模块）
- optimize_section: 优化特定模块（如"优化工作经历"、"优化个人总结"、"优化技能"等）
- answer_question: 回答AI的问题（当AI问了"问题1"、"问题2"、"问题3"后，用户的回答）
- confirm: 确认（可以、好的、确认、开始、继续等简短确认词）
- cancel: 取消（取消、不要、算了、停止等）
- unknown: 其他未知意图

## 识别规则
1. **回答识别**：如果最后一条AI消息包含"问题1"、"问题2"、"问题3"，且用户输入是回答（不是新问题），则识别为 answer_question
2. **模块优化识别**：如果用户说"优化XX"（XX是具体模块名），则识别为 optimize_section
3. **确认识别**：如果用户输入是简短确认词（1-3个字），且上下文中有待确认的内容，则识别为 confirm
4. **上下文理解**：必须考虑对话历史，不要只看当前输入

## 输出格式（必须是有效的JSON）
{{
    "intent": "意图类型（小写）",
    "confidence": 0.0-1.0,
    "extracted_info": {{
        "section": "模块名（如果是optimize_section，如：工作经历、个人总结）",
        "question": "问题编号（如果是answer_question，如：问题1、问题2、问题3）",
        "answer_type": "回答类型（如果是answer_question：duties/results/technologies）"
    }},
    "reasoning": "识别理由（简短，1-2句话）"
}}

请只返回JSON，不要其他内容。"""

        try:
            response = await self.llm.ask(
                messages=[{"role": "user", "content": prompt}],
                stream=False,
                temperature=0.1
            )

            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]
            response = response.strip()

            result = json.loads(response)

            intent_str = result.get("intent", "unknown")
            try:
                intent = Intent(intent_str)
            except ValueError:
                logger.warning(f"未知的意图类型: {intent_str}，使用 UNKNOWN")
                intent = Intent.UNKNOWN

            return {
                "intent": intent,
                "confidence": result.get("confidence", 0.5),
                "extracted_info": result.get("extracted_info", {}),
                "reasoning": result.get("reasoning", "")
            }

        except json.JSONDecodeError as e:
            logger.error(f"LLM 返回的 JSON 解析失败: {e}")
            return {
                "intent": Intent.UNKNOWN,
                "confidence": 0.0,
                "extracted_info": {},
                "reasoning": f"JSON 解析失败: {str(e)}"
            }
        except Exception as e:
            logger.error(f"LLM 意图识别失败: {e}")
            return {
                "intent": Intent.UNKNOWN,
                "confidence": 0.0,
                "extracted_info": {},
                "reasoning": f"识别失败: {str(e)}"
            }

    async def detect_intent(
        self,
        user_input: str,
        conversation_history: List[Any] = None,
        last_ai_message: Optional[str] = None
    ) -> Tuple[Intent, Dict[str, Any]]:
        """使用 LLM 检测用户意图"""
        llm_result = await self.classify_intent_with_llm(
            user_input=user_input,
            conversation_history=conversation_history,
            last_ai_message=last_ai_message
        )

        intent = llm_result["intent"]
        extracted_info = llm_result.get("extracted_info", {})

        logger.info(f"🧠 LLM 意图识别: {intent.value}, 置信度: {llm_result.get('confidence', 0):.2f}")

        return intent, extracted_info

    async def process_input(
        self,
        user_input: str,
        conversation_history: List[Any] = None,
        last_ai_message: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        处理用户输入，返回处理建议

        Returns:
            {
                "intent": Intent,
                "tool": str,
                "tool_args": dict,
                "context_prompt": str,
                "should_skip_llm": bool,
            }
        """
        self.context.turn_count += 1

        intent, info = await self.detect_intent(
            user_input=user_input,
            conversation_history=conversation_history,
            last_ai_message=last_ai_message
        )

        result = {
            "intent": intent,
            "tool": None,
            "tool_args": {},
            "context_prompt": "",
            "should_skip_llm": False,
        }

        if intent == Intent.GREETING:
            result["tool"] = None
            self.context.state = ConversationState.GREETING
        elif intent == Intent.LOAD_RESUME:
            # 加载简历 → 调用 cv_reader_agent
            result["tool"] = "cv_reader_agent"
            # 如果 extracted_info 中有文件路径，使用它
            if info.get("file_path"):
                result["tool_args"] = {"file_path": info["file_path"]}
        elif intent == Intent.VIEW_RESUME:
            result["tool"] = "cv_reader_agent"
        elif intent == Intent.ANALYZE:
            result["tool"] = "cv_analyzer_agent"
            self.context.state = ConversationState.ANALYZING
        elif intent == Intent.OPTIMIZE:
            # 优化请求 → 先用 Analyzer 分析并给出建议
            result["tool"] = "cv_analyzer_agent"
            result["tool_args"] = {"mode": "optimize"}
            self.context.state = ConversationState.OPTIMIZING
        elif intent == Intent.OPTIMIZE_SECTION:
            # 优化特定模块 → 先用 Analyzer 分析该模块
            section = info.get("section", "工作经历")
            result["tool"] = "cv_analyzer_agent"
            result["tool_args"] = {
                "mode": "optimize_section",
                "section": section
            }
            self.context.state = ConversationState.OPTIMIZING
            self.context.optimization.section = section
            self.context.optimization.started_at = datetime.now()
        elif intent == Intent.CONFIRM:
            result = self._handle_confirm()
        elif intent == Intent.CANCEL:
            self._reset_optimization()
            result["context_prompt"] = "用户取消了当前操作。"
        else:
            result["context_prompt"] = self._generate_context_prompt()

        return result

    def _handle_confirm(self) -> Dict[str, Any]:
        """处理确认意图 - 用户同意建议后直接编辑"""
        result = {
            "intent": Intent.CONFIRM,
            "tool": None,
            "tool_args": {},
            "context_prompt": "",
            "should_skip_llm": False,
        }

        last_tool = self.context.last_tool_used
        last_response = self.context.last_ai_response

        # 如果是 Analyzer 分析后用户确认，则调用 Editor 直接应用修改
        if "analyzer" in last_tool or "分析" in last_response:
            result["tool"] = "cv_editor_agent"
            # 根据上一条 AI 响应判断要编辑哪个模块
            if "工作经历" in last_response:
                result["tool_args"] = {"action": "edit", "section": "工作经历"}
            elif "个人总结" in last_response:
                result["tool_args"] = {"action": "edit", "section": "个人总结"}
            elif "技能" in last_response:
                result["tool_args"] = {"action": "edit", "section": "技能"}
            else:
                result["tool_args"] = {"action": "auto_apply"}

        return result

    def _generate_context_prompt(self) -> str:
        """生成上下文提示"""
        parts = []

        parts.append(f"当前状态: {self.context.state.value}")

        if self.context.resume_loaded:
            parts.append("简历已加载")
        else:
            parts.append("简历未加载")

        if self.context.state in [ConversationState.OPTIMIZING, ConversationState.WAITING_ANSWER]:
            opt = self.context.optimization
            if opt.section:
                parts.append(f"正在优化: {opt.section}")
                parts.append(f"当前问题: 问题{opt.current_question}")

        return "\n".join(parts)

    def update_after_tool(self, tool_name: str, result: str):
        """工具执行后更新状态"""
        self.context.last_tool_used = tool_name
        self.context.last_ai_response = result[:500]

        if "我最建议先回答问题" in result or "请回答" in result:
            self.context.state = ConversationState.WAITING_ANSWER
            import re
            match = re.search(r'问题[一二三123]', result)
            if match:
                q_map = {"一": 1, "二": 2, "三": 3, "1": 1, "2": 2, "3": 3}
                q_char = match.group().replace("问题", "")
                self.context.optimization.current_question = q_map.get(q_char, 1)

    def update_resume_loaded(self, loaded: bool):
        """更新简历加载状态"""
        self.context.resume_loaded = loaded
        if loaded:
            self.context.state = ConversationState.RESUME_LOADED

    def _reset_optimization(self):
        """重置优化状态"""
        self.context.optimization = OptimizationContext()
        self.context.state = ConversationState.RESUME_LOADED if self.context.resume_loaded else ConversationState.IDLE

    def get_state_for_prompt(self) -> str:
        """获取用于提示词的状态描述"""
        return self._generate_context_prompt()

    def should_use_tool_directly(self, intent: Intent) -> bool:
        """判断是否应该直接使用工具"""
        direct_intents = [
            Intent.LOAD_RESUME,
            Intent.VIEW_RESUME,
            Intent.ANALYZE,
            Intent.OPTIMIZE,
            Intent.OPTIMIZE_SECTION,
            Intent.ANSWER_QUESTION,
        ]
        return intent in direct_intents
