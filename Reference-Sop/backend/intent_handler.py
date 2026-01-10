"""
意图处理模块 - 集成意图识别到 WebSocket 消息处理

在用户消息到达时进行意图识别，并将结果发送给前端。
"""

import logging
from typing import Dict, Any
from app.web.websocket.connection_manager import ConnectionManager
import sys
import os

# 添加 Reference-Sop 目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from backend.intent_classifier import get_intent_classifier, IntentType

logger = logging.getLogger(__name__)


async def handle_intent_recognition(
    user_message: str,
    client_id: str,
    connection_manager: ConnectionManager,
) -> Dict[str, Any]:
    """处理意图识别

    Args:
        user_message: 用户输入的消息
        client_id: WebSocket 客户端 ID
        connection_manager: WebSocket 连接管理器

    Returns:
        Dict: 意图识别结果
    """
    try:
        # 获取意图分类器
        classifier = get_intent_classifier()

        # 进行意图识别
        result = classifier.classify(user_message)

        # 构建思考过程文本（用于 Thought Process 显示）
        reasoning_text = f"""这是一个{result.intent_type.value}类型的请求，置信度：{result.confidence:.2f}。

根据"Special Exception for Simple Greetings and Casual Conversations"规则：
- 如果是问候或简单对话，应该在Response部分用自然、温暖、热情的方式回应
- 展现个性和真诚的连接感
- 不需要使用ask_human、需求澄清或任务规划
- 应该用中文回复，因为用户用中文提问

推理过程：{result.reasoning}"""

        # 发送意图识别结果到前端
        await connection_manager.send_to_client(
            client_id,
            {
                "type": "intent_result",
                "intent_type": result.intent_type.value,
                "confidence": result.confidence,
                "reasoning": reasoning_text,
            }
        )

        logger.info(f"Intent recognized: {result.intent_type.value} (confidence: {result.confidence:.2f})")

        return {
            "intent_type": result.intent_type.value,
            "confidence": result.confidence,
            "reasoning": result.reasoning,
            "is_greeting_or_casual": result.intent_type in (IntentType.GREETING, IntentType.CASUAL_CHAT),
        }
    except Exception as e:
        logger.error(f"Error in intent recognition: {e}", exc_info=True)
        return {
            "intent_type": "general_chat",
            "confidence": 0.5,
            "reasoning": "意图识别失败，使用默认处理",
            "is_greeting_or_casual": False,
        }


def should_use_casual_response(intent_result: Dict[str, Any]) -> bool:
    """判断是否应该使用简单对话响应方式

    Args:
        intent_result: 意图识别结果

    Returns:
        bool: 如果是问候或简单对话返回 True
    """
    return intent_result.get("is_greeting_or_casual", False)

