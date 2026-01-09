# Sophia-Pro 功能复刻指南

## 📋 概述

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

### 问题 2：缺少 Thought Process 展示

**之前的问题：**
- 用户看不到 AI 的思考过程
- 无法理解 AI 为什么这样回复

**解决方案：**
- 解析 LLM 输出中的 `Thought:` 部分
- 在前端以灰色、可折叠的方式展示
- 复刻 sophia-pro 的视觉样式

### 问题 3：流式输出体验不佳

**之前的问题：**
- 回复一次性显示，没有打字机效果
- 无法实时看到 AI 的思考过程

**解决方案：**
- 实现 WebSocket 流式传输
- 前端实现打字机效果
- 实时显示 Thought 和 Response

### 问题 4：Markdown 渲染不完整

**之前的问题：**
- 简单的 Markdown 渲染
- 缺少代码块、列表等高级格式支持

**解决方案：**
- 使用 `react-markdown` 完整渲染
- 自定义组件样式
- 支持代码高亮、列表、链接等

---

## 🔧 实现细节

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

### 2. Thought Process 解析和展示

#### 2.1 后端解析逻辑

**位置：** `app/web/streaming/agent_stream.py`

**解析函数：**
```python
def parse_thought_response(content: str) -> Tuple[Optional[str], Optional[str]]:
    """
    解析 LLM 输出中的 Thought 和 Response 部分
    复刻自 sophia-pro 的输出格式解析
    
    Returns:
        (thought, response) - 如果没有找到对应部分则为 None
    """
    thought = None
    response = None
    
    # 使用更严谨的正则表达式匹配 Thought: 和 Response:
    # 考虑可能存在的换行和空格
    thought_match = re.search(r'Thought:\s*(.*?)(?=\n*Response:|$)', content, re.DOTALL | re.IGNORECASE)
    response_match = re.search(r'Response:\s*(.*)', content, re.DOTALL | re.IGNORECASE)
    
    if thought_match:
        thought = thought_match.group(1).strip()
    
    if response_match:
        response = response_match.group(1).strip()
    
    # 如果找到了 Thought 但没找到 Response（还在生成中），或者找到了 Response
    if thought or response:
        return thought, response
    
    # 如果都没有找到格式化的输出，返回原始内容作为 response
    return None, content
```

**关键点：**
- 使用正则表达式匹配 `Thought:` 和 `Response:` 标记
- 支持多行内容（`re.DOTALL`）
- 忽略大小写（`re.IGNORECASE`）
- 处理边界情况（没有格式化输出时返回原始内容）

**在 FINISHED 状态时解析：**
```python
if self.agent.state == SchemaAgentState.FINISHED:
    # 获取最终答案
    final_answer = None
    for msg in reversed(self.agent.memory.messages):
        if msg.role == "assistant" and msg.content:
            final_answer = msg.content
            break

    if final_answer and not self._answer_sent_in_loop:
        # 🎯 解析 Thought 和 Response（复刻自 sophia-pro）
        thought_part, response_part = parse_thought_response(final_answer)
        
        # 先发送 Thought（如果有）
        if thought_part:
            yield ThoughtEvent(
                thought=thought_part,
                session_id=self._session_id,
            )
        
        # 再发送 Response
        final_content = response_part if response_part else final_answer
        yield AnswerEvent(
            content=final_content,
            is_complete=True,
            session_id=self._session_id,
        )
```

#### 2.2 前端展示组件

**位置：** `frontend/src/pages/SophiaChat.jsx`

**ThoughtProcess 组件：**
```jsx
function ThoughtProcess({ content, isStreaming }) {
  const [expanded, setExpanded] = useState(true);
  
  if (!content) return null;
  
  return (
    <div className="mb-4">
      <div 
        className="cursor-pointer flex items-center gap-2 py-1"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex gap-1 items-center">
          <span className="text-slate-400 text-sm font-normal">Thought Process</span>
          <svg 
            className={`w-3 h-3 text-slate-400 transition-transform duration-200 ${expanded ? '' : 'rotate-180'}`}
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
          </svg>
        </div>
        {isStreaming && (
          <div className="flex gap-1 ml-1">
            <span className="w-1 h-1 bg-slate-300 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
            <span className="w-1 h-1 bg-slate-300 rounded-full animate-bounce" style={{ animationDelay: '100ms' }}></span>
            <span className="w-1 h-1 bg-slate-300 rounded-full animate-bounce" style={{ animationDelay: '200ms' }}></span>
          </div>
        )}
      </div>
      
      {expanded && (
        <div className="text-slate-400 text-sm leading-relaxed pl-0 font-normal">
          {content}
        </div>
      )}
    </div>
  );
}
```

**关键点：**
- 使用 `text-slate-400` 实现灰色文字（复刻 sophia-pro 样式）
- 可折叠功能（点击展开/收起）
- 流式显示时显示加载动画
- 默认展开状态

---

### 3. 流式输出和打字机效果

#### 3.1 后端流式传输

**位置：** `app/web/streaming/agent_stream.py`

**实时发送 Thought 和 Response：**
```python
# 处理新消息
for msg in new_messages:
    if msg.role == "assistant":
        if msg.content:
            # 🎯 解析 Thought 和 Response 格式（复刻自 sophia-pro）
            thought_part, response_part = parse_thought_response(msg.content)
            
            # 先发送 Thought（如果有）
            if thought_part:
                logger.info(f"[Thought Process] {thought_part[:100]}...")
                yield ThoughtEvent(
                    thought=thought_part,
                    session_id=self._session_id,
                )

            # 再发送 Response/Answer
            if response_part:
                yield AnswerEvent(
                    content=response_part,
                    is_complete=False,  # 流式传输中
                    session_id=self._session_id,
                )
```

**WebSocket 事件类型：**
```python
# app/web/streaming/events.py
class ThoughtEvent(StreamEvent):
    type: str = EventType.THOUGHT
    data: Dict[str, Any]

class AnswerEvent(StreamEvent):
    type: str = EventType.ANSWER
    data: Dict[str, Any]
    is_complete: bool = False
```

#### 3.2 前端打字机效果

**位置：** `frontend/src/pages/SophiaChat.jsx`

**打字机 Hook：**
```jsx
function useTypewriter(text, speed = 25, enabled = true) {
  const [displayedText, setDisplayedText] = useState('');
  const [isComplete, setIsComplete] = useState(false);
  const indexRef = useRef(0);
  const timerRef = useRef(null);
  
  useEffect(() => {
    if (!enabled || !text) {
      setDisplayedText(text || '');
      setIsComplete(true);
      return;
    }
    
    setDisplayedText('');
    setIsComplete(false);
    indexRef.current = 0;
    
    const typeNext = () => {
      if (indexRef.current < text.length) {
        // 每次添加 1-3 个字符，模拟更自然的打字效果
        const chunk = Math.min(
          Math.floor(Math.random() * 3) + 1,
          text.length - indexRef.current
        );
        indexRef.current += chunk;
        setDisplayedText(text.slice(0, indexRef.current));
        // 随机延迟，让打字更自然
        timerRef.current = setTimeout(typeNext, speed + Math.random() * 15);
      } else {
        setIsComplete(true);
      }
    };
    
    timerRef.current = setTimeout(typeNext, 50);
    return () => clearTimeout(timerRef.current);
  }, [text, speed, enabled]);
  
  return { displayedText, isComplete };
}
```

**关键点：**
- 每次显示 1-3 个随机字符，模拟真实打字
- 随机延迟（`speed + Math.random() * 15`）
- 支持启用/禁用
- 完成后触发回调

**在消息组件中使用：**
```jsx
function ChatMessage({ message, isLatest, isStreaming }) {
  const { displayedText, isComplete } = useTypewriter(
    message.content,
    20,
    message.role === 'assistant' && isLatest && isStreaming
  );
  
  // 显示打字机效果或完整文本
  const textToShow = isLatest && isStreaming ? displayedText : message.content;
  
  return (
    <div>
      {message.thought && (
        <ThoughtProcess 
          content={message.thought} 
          isStreaming={isLatest && isStreaming && !message.content}
        />
      )}
      {textToShow && (
        <MarkdownContent>{textToShow}</MarkdownContent>
      )}
      {isLatest && isStreaming && !isComplete && (
        <span className="inline-block w-0.5 h-4 bg-gray-400 animate-pulse ml-0.5" />
      )}
    </div>
  );
}
```

---

### 4. Markdown 渲染

#### 4.1 使用 react-markdown

**安装依赖：**
```bash
npm install react-markdown
```

**位置：** `frontend/src/pages/SophiaChat.jsx`

**MarkdownContent 组件：**
```jsx
import ReactMarkdown from 'react-markdown';

function MarkdownContent({ children, className = '' }) {
  return (
    <div className={`markdown-content ${className}`}>
      <ReactMarkdown
        components={{
          p: ({ children }) => (
            <p className="mb-4 text-gray-800 leading-relaxed">{children}</p>
          ),
          strong: ({ children }) => (
            <strong className="font-bold text-gray-900">{children}</strong>
          ),
          em: ({ children }) => (
            <em className="italic">{children}</em>
          ),
          ul: ({ children }) => (
            <ul className="mb-4 space-y-2">{children}</ul>
          ),
          ol: ({ children }) => (
            <ol className="mb-4 space-y-2 list-decimal ml-6">{children}</ol>
          ),
          li: ({ children }) => (
            <li className="text-gray-800 leading-relaxed pl-1">{children}</li>
          ),
          h1: ({ children }) => (
            <h1 className="text-xl font-bold text-gray-900 mb-4 mt-6">{children}</h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-lg font-bold text-gray-900 mb-3 mt-5">{children}</h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-base font-bold text-gray-900 mb-2 mt-4">{children}</h3>
          ),
          code: ({ inline, children }) => (
            inline ? (
              <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono text-gray-800">
                {children}
              </code>
            ) : (
              <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg text-sm font-mono overflow-x-auto mb-4">
                <code>{children}</code>
              </pre>
            )
          ),
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-gray-300 pl-4 italic text-gray-600 my-4">
              {children}
            </blockquote>
          ),
          a: ({ href, children }) => (
            <a 
              href={href} 
              className="text-blue-600 hover:underline" 
              target="_blank" 
              rel="noopener noreferrer"
            >
              {children}
            </a>
          ),
        }}
      >
        {children}
      </ReactMarkdown>
    </div>
  );
}
```

**关键点：**
- 自定义所有 Markdown 元素的样式
- 内联代码和代码块分别处理
- 链接自动在新标签页打开
- 使用 Tailwind CSS 类名

---

## 🚀 未来规划：模块化可复用组件

### 目标架构

将以下功能拆分为独立的、可复用的模块：

```
shared/
├── prompts/
│   ├── greeting_exception.py      # 问候异常规则
│   └── thought_response_format.py  # Thought/Response 格式定义
├── backend/
│   ├── parsers/
│   │   └── thought_response_parser.py  # 解析器（可复用）
│   └── streaming/
│       └── thought_response_stream.py   # 流式处理（可复用）
└── frontend/
    ├── components/
    │   ├── ThoughtProcess.jsx      # Thought Process 组件（可复用）
    │   ├── StreamingText.jsx       # 打字机效果组件（可复用）
    │   └── MarkdownRenderer.jsx    # Markdown 渲染组件（可复用）
    └── hooks/
        └── useTypewriter.js        # 打字机 Hook（可复用）
```

### 1. 意图识别模块化

**文件：** `shared/prompts/greeting_exception.py`

```python
"""
问候和简单对话异常规则 - 可复用模块

使用方法：
from shared.prompts.greeting_exception import GREETING_EXCEPTION_PROMPT

SYSTEM_PROMPT = f"""
{基础提示词}

{GREETING_EXCEPTION_PROMPT}
"""
"""

GREETING_EXCEPTION_PROMPT = """<greeting_exception>
**Special Exception for Simple Greetings and Casual Conversations:**
For simple greetings, casual conversations, emotional support requests, or non-task-related messages (like "你好", "hello", "hi", "谢谢", casual conversation or basic chitchat), respond completely in the "Response" section with natural, warm, enthusiastic, and engaging content. Show personality, humor when appropriate, and genuine interest in connecting with the user. Make responses feel like chatting with an energetic, helpful friend rather than a formal assistant. Make responses feel like receiving counsel from a wise, caring goddess who truly sees and values each person. Do not use ask_human, requirements clarification, or task planning for these cases.
</greeting_exception>"""
```

### 2. Thought/Response 格式定义

**文件：** `shared/prompts/thought_response_format.py`

```python
"""
Thought/Response 输出格式定义 - 可复用模块

使用方法：
from shared.prompts.thought_response_format import THOUGHT_RESPONSE_FORMAT

SYSTEM_PROMPT = f"""
{基础提示词}

{THOUGHT_RESPONSE_FORMAT}
"""
"""

THOUGHT_RESPONSE_FORMAT = """## Output Format (CRITICAL - Must Follow)

At each step, you MUST follow this exact format:

1. **Thought:** sequence - Your internal reasoning towards solving the task. Explain what you're thinking and why. This will be shown to the user as "Thought Process".

2. **Response:** sequence - Your response to the user. This should be conversational and user-friendly.

Example:
```
Thought: [Your internal reasoning here]
Response: [Your response to the user]
```
"""
```

### 3. 后端解析器模块化

**文件：** `shared/backend/parsers/thought_response_parser.py`

```python
"""
Thought/Response 解析器 - 可复用模块

使用方法：
from shared.backend.parsers.thought_response_parser import parse_thought_response

thought, response = parse_thought_response(llm_output)
"""

import re
from typing import Optional, Tuple

def parse_thought_response(content: str) -> Tuple[Optional[str], Optional[str]]:
    """
    解析 LLM 输出中的 Thought 和 Response 部分
    
    Args:
        content: LLM 的原始输出
        
    Returns:
        (thought, response) - 如果没有找到对应部分则为 None
    """
    thought = None
    response = None
    
    # 匹配 Thought: 和 Response: 格式
    thought_match = re.search(
        r'Thought:\s*(.*?)(?=\n*Response:|$)', 
        content, 
        re.DOTALL | re.IGNORECASE
    )
    response_match = re.search(
        r'Response:\s*(.*)', 
        content, 
        re.DOTALL | re.IGNORECASE
    )
    
    if thought_match:
        thought = thought_match.group(1).strip()
    
    if response_match:
        response = response_match.group(1).strip()
    
    if thought or response:
        return thought, response
    
    # 如果没有找到格式化的输出，返回原始内容作为 response
    return None, content
```

### 4. 前端 Thought Process 组件模块化

**文件：** `shared/frontend/components/ThoughtProcess.jsx`

```jsx
/**
 * Thought Process 组件 - 可复用模块
 * 
 * 使用方法：
 * import ThoughtProcess from '@/shared/frontend/components/ThoughtProcess';
 * 
 * <ThoughtProcess 
 *   content={thoughtContent} 
 *   isStreaming={isStreaming}
 *   defaultExpanded={true}
 *   className="custom-class"
 * />
 */

import React, { useState } from 'react';

export default function ThoughtProcess({ 
  content, 
  isStreaming = false,
  defaultExpanded = true,
  className = '',
  onToggle = null
}) {
  const [expanded, setExpanded] = useState(defaultExpanded);
  
  if (!content) return null;
  
  const handleToggle = () => {
    const newExpanded = !expanded;
    setExpanded(newExpanded);
    onToggle?.(newExpanded);
  };
  
  return (
    <div className={`mb-4 ${className}`}>
      <div 
        className="cursor-pointer flex items-center gap-2 py-1"
        onClick={handleToggle}
      >
        <div className="flex gap-1 items-center">
          <span className="text-slate-400 text-sm font-normal">Thought Process</span>
          <svg 
            className={`w-3 h-3 text-slate-400 transition-transform duration-200 ${expanded ? '' : 'rotate-180'}`}
            fill="none" 
            stroke="currentColor" 
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
          </svg>
        </div>
        {isStreaming && (
          <div className="flex gap-1 ml-1">
            <span className="w-1 h-1 bg-slate-300 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
            <span className="w-1 h-1 bg-slate-300 rounded-full animate-bounce" style={{ animationDelay: '100ms' }}></span>
            <span className="w-1 h-1 bg-slate-300 rounded-full animate-bounce" style={{ animationDelay: '200ms' }}></span>
          </div>
        )}
      </div>
      
      {expanded && (
        <div className="text-slate-400 text-sm leading-relaxed pl-0 font-normal">
          {content}
        </div>
      )}
    </div>
  );
}
```

### 5. 打字机效果 Hook 模块化

**文件：** `shared/frontend/hooks/useTypewriter.js`

```jsx
/**
 * 打字机效果 Hook - 可复用模块
 * 
 * 使用方法：
 * import useTypewriter from '@/shared/frontend/hooks/useTypewriter';
 * 
 * const { displayedText, isComplete } = useTypewriter(text, speed, enabled);
 */

import { useState, useEffect, useRef } from 'react';

export default function useTypewriter(text, speed = 25, enabled = true, onComplete = null) {
  const [displayedText, setDisplayedText] = useState('');
  const [isComplete, setIsComplete] = useState(false);
  const indexRef = useRef(0);
  const timerRef = useRef(null);
  
  useEffect(() => {
    if (!enabled || !text) {
      setDisplayedText(text || '');
      setIsComplete(true);
      onComplete?.();
      return;
    }
    
    setDisplayedText('');
    setIsComplete(false);
    indexRef.current = 0;
    
    const typeNext = () => {
      if (indexRef.current < text.length) {
        // 每次添加 1-3 个字符，模拟更自然的打字效果
        const chunk = Math.min(
          Math.floor(Math.random() * 3) + 1,
          text.length - indexRef.current
        );
        indexRef.current += chunk;
        setDisplayedText(text.slice(0, indexRef.current));
        // 随机延迟，让打字更自然
        timerRef.current = setTimeout(typeNext, speed + Math.random() * 15);
      } else {
        setIsComplete(true);
        onComplete?.();
      }
    };
    
    timerRef.current = setTimeout(typeNext, 50);
    return () => {
      if (timerRef.current) {
        clearTimeout(timerRef.current);
      }
    };
  }, [text, speed, enabled, onComplete]);
  
  return { displayedText, isComplete };
}
```

### 6. Markdown 渲染组件模块化

**文件：** `shared/frontend/components/MarkdownRenderer.jsx`

```jsx
/**
 * Markdown 渲染组件 - 可复用模块
 * 
 * 使用方法：
 * import MarkdownRenderer from '@/shared/frontend/components/MarkdownRenderer';
 * 
 * <MarkdownRenderer>{markdownText}</MarkdownRenderer>
 */

import React from 'react';
import ReactMarkdown from 'react-markdown';

export default function MarkdownRenderer({ 
  children, 
  className = '',
  customComponents = {}
}) {
  const defaultComponents = {
    p: ({ children }) => (
      <p className="mb-4 text-gray-800 leading-relaxed">{children}</p>
    ),
    strong: ({ children }) => (
      <strong className="font-bold text-gray-900">{children}</strong>
    ),
    em: ({ children }) => (
      <em className="italic">{children}</em>
    ),
    ul: ({ children }) => (
      <ul className="mb-4 space-y-2">{children}</ul>
    ),
    ol: ({ children }) => (
      <ol className="mb-4 space-y-2 list-decimal ml-6">{children}</ol>
    ),
    li: ({ children }) => (
      <li className="text-gray-800 leading-relaxed pl-1">{children}</li>
    ),
    h1: ({ children }) => (
      <h1 className="text-xl font-bold text-gray-900 mb-4 mt-6">{children}</h1>
    ),
    h2: ({ children }) => (
      <h2 className="text-lg font-bold text-gray-900 mb-3 mt-5">{children}</h2>
    ),
    h3: ({ children }) => (
      <h3 className="text-base font-bold text-gray-900 mb-2 mt-4">{children}</h3>
    ),
    code: ({ inline, children }) => (
      inline ? (
        <code className="bg-gray-100 px-1.5 py-0.5 rounded text-sm font-mono text-gray-800">
          {children}
        </code>
      ) : (
        <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg text-sm font-mono overflow-x-auto mb-4">
          <code>{children}</code>
        </pre>
      )
    ),
    blockquote: ({ children }) => (
      <blockquote className="border-l-4 border-gray-300 pl-4 italic text-gray-600 my-4">
        {children}
      </blockquote>
    ),
    a: ({ href, children }) => (
      <a 
        href={href} 
        className="text-blue-600 hover:underline" 
        target="_blank" 
        rel="noopener noreferrer"
      >
        {children}
      </a>
    ),
  };
  
  const finalComponents = { ...defaultComponents, ...customComponents };
  
  return (
    <div className={`markdown-content ${className}`}>
      <ReactMarkdown components={finalComponents}>
        {children}
      </ReactMarkdown>
    </div>
  );
}
```

---

## 📝 使用示例

### 完整集成示例

**后端（FastAPI）：**
```python
from shared.backend.parsers.thought_response_parser import parse_thought_response
from shared.prompts.greeting_exception import GREETING_EXCEPTION_PROMPT
from shared.prompts.thought_response_format import THOUGHT_RESPONSE_FORMAT

# 构建系统提示词
SYSTEM_PROMPT = f"""
You are an AI assistant.

{THOUGHT_RESPONSE_FORMAT}

{GREETING_EXCEPTION_PROMPT}
"""

# 解析 LLM 输出
thought, response = parse_thought_response(llm_output)

# 发送到前端
yield ThoughtEvent(thought=thought)
yield AnswerEvent(content=response)
```

**前端（React）：**
```jsx
import ThoughtProcess from '@/shared/frontend/components/ThoughtProcess';
import MarkdownRenderer from '@/shared/frontend/components/MarkdownRenderer';
import useTypewriter from '@/shared/frontend/hooks/useTypewriter';

function ChatMessage({ message }) {
  const { displayedText, isComplete } = useTypewriter(
    message.content,
    20,
    message.isStreaming
  );
  
  return (
    <div>
      {message.thought && (
        <ThoughtProcess 
          content={message.thought}
          isStreaming={message.isStreaming}
        />
      )}
      <MarkdownRenderer>
        {displayedText}
      </MarkdownRenderer>
    </div>
  );
}
```

---

## 🎨 样式定制

所有组件都支持通过 `className` 和 `customComponents` 进行样式定制：

```jsx
// 自定义 Thought Process 样式
<ThoughtProcess 
  content={thought}
  className="my-custom-thought"
/>

// 自定义 Markdown 组件样式
<MarkdownRenderer
  customComponents={{
    p: ({ children }) => <p className="my-custom-p">{children}</p>,
    strong: ({ children }) => <strong className="text-red-500">{children}</strong>
  }}
>
  {content}
</MarkdownRenderer>
```

---

## ✅ 总结

通过模块化设计，这些功能可以：

1. **独立使用**：每个模块都可以单独导入和使用
2. **易于维护**：修改一处，所有使用的地方都会更新
3. **跨项目复用**：其他项目可以直接导入使用
4. **灵活定制**：支持样式和行为定制

**下一步：**
1. 创建 `shared/` 目录结构
2. 将现有代码迁移到模块化文件
3. 更新导入路径
4. 编写单元测试
5. 创建使用文档

---

## 📚 参考

- [sophia-pro 原始实现](https://github.com/your-org/sophia-pro)
- [react-markdown 文档](https://github.com/remarkjs/react-markdown)
- [Tailwind CSS 文档](https://tailwindcss.com/docs)

