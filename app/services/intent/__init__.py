"""
Intent Recognition Service - 增强意图识别系统

融合 OpenManus 和 Sophia-Pro 的意图识别架构：
- 两阶段分类：规则匹配 + LLM 增强
- 工具注册表：自动发现 + 配置文件覆盖
- 意图增强器：自动添加工具标记
"""

from app.services.intent.intent_classifier import IntentClassifier, IntentType, IntentResult
from app.services.intent.intent_enhancer import AgentIntentEnhancer
from app.services.intent.tool_registry import ToolRegistry, ToolMetadata
from app.services.intent.rule_matcher import RuleMatcher
from app.services.intent.weights import IntentScoreWeights

__all__ = [
    "IntentClassifier",
    "IntentType",
    "IntentResult",
    "AgentIntentEnhancer",
    "ToolRegistry",
    "ToolMetadata",
    "RuleMatcher",
    "IntentScoreWeights",
]


