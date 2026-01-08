
本文档详细说明如何在 OpenManus 项目中复刻 sophia-pro 的核心功能：
- **意图识别**（通过 prompt 规则）
- **Thought Process**（AI 思考过程展示）
- **流式输出**（实时响应）
- **Markdown 渲染**（格式化显示）

## 🎯 解决的问题

### 问题 1：硬编码的意图识别和回复

**之前的问题：**
- OpenManus 使用硬编码的意图分类器判断问候
- 问候回复是固定的模板，缺乏个性
- 无法展示 AI 的思考过程

**解决方案：**
- 使用 sophia-pro 的 `greeting_exception` prompt 规则
- 让 LLM 自己判断意图并生成个性化回复
- 通过 `Thought:` 和 `Response:` 格式展示思考过程


### 1. 意图识别（Prompt 规则方式）

#### 1.1 核心规则：`greeting_exception`

**位置：** `app/prompt/manus.py`

```python
<greeting_exception>
**Special Exception for Simple Greetings and Casual Conversations:**
For simple greetings, casual conversations, emotional support requests, or non-task-related messages (like "你好", "hello", "hi", "谢谢", casual conversation or basic chitchat), respond completely in the "Response" section with natural, warm, enthusiastic, and engaging content. Show personality, humor when appropriate, and genuine interest in connecting with the user. Make responses feel like chatting with an energetic, helpful friend rather than a formal assistant. Make responses feel like receiving counsel from a wise, caring goddess who truly sees and values each person. Do not use ask_human, requirements clarification, or task planning for these cases.
</greeting_exception>
```

**关键点：**
- 不是独立的分类器，而是通过 prompt 规则让 LLM 自己判断
- 适用于简单问候、休闲对话、情感支持等场景
- 要求回复自然、温暖、热情，展现个性
- 不使用工具、需求澄清或任务规划

#### 1.2 输出格式要求

**位置：** `app/prompt/manus.py`

```python
## Output Format (CRITICAL - Must Follow)

At each step, you MUST follow this exact format:

1. **Thought:** sequence - Your internal reasoning towards solving the task. Explain what you're thinking and why. This will be shown to the user as "Thought Process".

2. **Response:** sequence - Your response to the user. This should be conversational and user-friendly.

Example:
```
Thought: 这是一个简单的问候请求,属于casual conversation类型。根据greeting_exception规则,我应该用自然、温暖、热情的方式回应,展现个性和真诚的连接感。
Response: 你好呀！很高兴见到你！✨ 我是 OpenManus...
```
```

**关键点：**
- 强制要求 LLM 输出 `Thought:` 和 `Response:` 两部分
- `Thought:` 部分会显示给用户（作为 Thought Process）
- `Response:` 部分是实际回复内容

#### 1.3 移除硬编码处理

**位置：** `app/agent/manus.py`

**之前（硬编码）：**
```python
# 🎯 GREETING 意图：直接回复问候
if intent == Intent.GREETING:
    greeting_content = "你好！我是 OpenManus，您的简历优化助手。\n\n我可以帮您：\n- 📊 分析简历质量\n- ✏️ 优化简历内容\n- 💡 提供求职建议\n\n请告诉我您的需求，比如「分析简历」或「优化教育经历」。"
    self.memory.add_message(Message.assistant_message(greeting_content))
    logger.info("👋 GREETING: 直接返回问候并终止")
    from app.schema import AgentState
    self.state = AgentState.FINISHED
    return False
```

**现在（交给 LLM）：**
```python
# 🎯 GREETING 意图：让 LLM 处理（通过 prompt 中的 greeting_exception 规则）
# 不再硬编码回复，让 LLM 根据 prompt 规则自己生成 Thought 和 Response
if intent == Intent.GREETING:
    logger.info("👋 GREETING: 交给 LLM 处理（遵循 greeting_exception 规则）")
    # 继续往下走，让 LLM 处理
```

---
