# Agent 幻觉问题分析

## 问题描述

**症状**：LLM 在处理请求时会错误地认为"用户已经说了'优化'"，即使用户只是说"分析一下教育经历"。

### 复现场景

```
用户: "分析一下教育经历"
   ↓
Agent (期望): 调用 education_analyzer
   ↓
Agent (实际): 可能直接调用 cv_editor_agent 或询问"是否要优化"
```

---

## 可能的原因

### 1. 提示词中的误导性信息

**位置**: `app/prompt/manus.py`

当前提示词中包含以下内容：

```python
## Task Completion Flow:
- After analysis tools (education_analyzer, cv_analyzer_agent) complete and return results:
  1. Present the analysis results to the user
  2. Ask the user: "是否要优化这段教育经历？"
  3. Wait for user's response:
     - If user says "优化" / "要" / "yes" → Call cv_editor_agent()
```

**问题**：Agent 可能将这些"未来步骤"理解为"当前步骤"，导致：
- 在分析完成前就询问优化
- 直接跳过分析步骤

---

### 2. 历史对话上下文干扰

如果之前的对话中用户说过"优化"，Agent 可能：
- 从历史消息中提取到"优化"关键词
- 错误地认为当前请求也是优化请求

---

### 3. LLM 模型的行为特性

某些模型倾向于：
- 主动提供"帮助"行为
- 提前执行用户可能需要的操作
- 对模糊请求做出过度解读

---

## 解决方案

### 方案 1: 强化"当前请求"检测

在提示词中明确区分"分析请求"和"优化请求"：

```python
## Request Type Detection:

**Analysis Requests** (分析类):
- "分析教育经历" / "分析教育" / "看看教育背景"
- "分析简历" / "全面分析"
- → Action: Call analyzer ONLY, output results, STOP

**Optimization Requests** (优化类):
- "优化教育经历" / "优化教育背景"
- "修改教育经历" / "改一下教育"
- → Action: Get optimization suggestions, ask user, wait for confirmation

**CRITICAL**: If user says "分析" but NOT "优化", treat as ANALYSIS request.
DO NOT ask about optimization until analysis is complete AND user confirms.
```

---

### 方案 2: 简化提示词，移除前瞻性内容

移除提示词中的"未来步骤"描述，只保留当前步骤：

```python
## Current Request Rules:

1. Read the CURRENT user message carefully
2. Identify the EXACT action requested:
   - "分析" → Call analyzer
   - "优化" → Get suggestions + ask user
3. Execute ONLY the requested action
4. STOP after completion
```

---

### 方案 3: 添加验证检查点

在 Agent 的 `think()` 方法中添加验证：

```python
async def think(self) -> bool:
    user_input = self._get_last_user_message()

    # 验证：如果用户说"分析"但 Agent 要调用 editor
    if "分析" in user_input and self._pending_tool == "cv_editor_agent":
        logger.warning(f"⚠️ 检测到不匹配：用户说'分析'但 Agent 准备调用 editor")
        # 强制使用 analyzer
        self._pending_tool = "education_analyzer"
```

---

### 方案 4: 使用 Few-Shot 示例

在提示词中添加明确的示例：

```python
## Examples:

Example 1:
User: "分析教育经历"
Agent: [Call education_analyzer]
Agent: [Output analysis results]
STOP

Example 2:
User: "优化教育经历"
Agent: [Get optimization suggestions]
Agent: "是否要优化这段教育经历？"
User: "要"
Agent: [Call cv_editor_agent]

Example 3 (WRONG):
User: "分析教育经历"
Agent: "是否要优化？" ❌ WRONG - user didn't ask for optimization
```

---

### 方案 5: 调整 Temperature

对于需要精确遵循指令的任务，使用较低的 temperature：

```python
# education_analyzer 等分析任务
temperature = 0

# 内容生成任务
temperature = 0.7
```

---

## 当前状态

| 方案 | 优先级 | 预期效果 | 实施难度 |
|------|--------|----------|----------|
| 方案 1: 强化请求类型检测 | 高 | 高 | 低 |
| 方案 2: 简化提示词 | 中 | 中 | 低 |
| 方案 3: 添加验证检查点 | 高 | 高 | 中 |
| 方案 4: Few-Shot 示例 | 中 | 高 | 低 |
| 方案 5: 调整 Temperature | 低 | 中 | 低 |

---

## 实施建议

**立即实施**：
1. 在 `manus.py` 中添加"请求类型检测"部分
2. 添加 Few-Shot 示例

**后续优化**：
1. 在 Agent 代码中添加验证逻辑
2. 测试不同 Temperature 设置

---

## 相关文件

| 文件 | 作用 |
|------|------|
| `app/prompt/manus.py` | 主提示词，需要添加请求类型检测 |
| `app/agent/manus.py` | Agent 实现，可添加验证逻辑 |
| `app/llm.py` | LLM 调用，可调整 Temperature |

---

## 测试用例

| 用户输入 | 期望行为 | 当前行为 | 状态 |
|----------|----------|----------|------|
| "分析教育经历" | 调用 education_analyzer | 可能跳过分析 | ❌ |
| "分析一下教育背景" | 调用 education_analyzer | 可能跳过分析 | ❌ |
| "优化教育经历" | 获取建议并询问确认 | 正确处理 | ✅ |
| "分析并优化" | 先分析，询问后再优化 | 可能直接优化 | ❌ |
