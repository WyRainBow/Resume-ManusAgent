# 复刻 LangChain 上下文机制

**文档版本**: 1.0
**创建日期**: 2026-01-XX
**最后更新**: 2026-01-XX

---

## 目录

1. [概述](#概述)
2. [当前项目上下文机制架构](#当前项目上下文机制架构)
3. [核心组件详解](#核心组件详解)
4. [与 LangChain 对比](#与-langchain-对比)
5. [实现完整性评估](#实现完整性评估)
6. [总结](#总结)

---

## 概述

OpenManus 项目实现了一套完整的上下文管理机制，基于 LangChain 的设计理念，但针对简历优化场景进行了适配。本文档详细描述了当前的实现架构，并与 LangChain 的原始实现进行对比。

### 设计目标

1. **完整复刻 LangChain 核心功能**：消息类型、历史管理、工具调用等
2. **内存存储**：使用内存存储，适合单会话场景
3. **无缝集成**：与 OpenManus 现有系统（Agent、Tool、LLM）无缝集成
4. **上下文传递**：支持跨 WebSocket 连接的上下文恢复

---

## 当前项目上下文机制架构

### 架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    OpenManus 应用层                           │
│  (Agent, WebSocket Server, Tool Execution)                  │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              ChatHistoryManager (包装层)                     │
│  - 提供 OpenManus 兼容接口                                   │
│  - 消息格式转换 (OpenManus ↔ LangChain)                     │
│  - 滑动窗口管理                                              │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│              MessageAdapter (适配器层)                       │
│  - to_langchain(): OpenManus Message → LangChain Message   │
│  - from_langchain(): LangChain Message → OpenManus Message │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ▼
┌─────────────────────────────────────────────────────────────┐
│         LangChain 风格实现 (app/memory/langchain/)           │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  Messages        │  │  ChatHistory     │                │
│  │  - BaseMessage   │  │  - BaseChat...   │                │
│  │  - HumanMessage  │  │  - InMemory...   │                │
│  │  - AIMessage     │  │                  │                │
│  │  - SystemMessage │  │                  │                │
│  │  - ToolMessage   │  │                  │                │
│  │  - *Chunk        │  │                  │                │
│  └──────────────────┘  └──────────────────┘                │
│                                                              │
│  ┌──────────────────┐  ┌──────────────────┐                │
│  │  Tool Calls      │  │  Utils           │                │
│  │  - ToolCall      │  │  - message_to... │                │
│  │  - ToolCallChunk │  │  - messages_...  │                │
│  │  - InvalidTool... │  │  - get_buffer... │                │
│  └──────────────────┘  └──────────────────┘                │
└─────────────────────────────────────────────────────────────┘
```

### 数据流

```
用户输入
    ↓
WebSocket Server
    ↓
ChatHistoryManager.add_message(OpenManus Message)
    ↓
MessageAdapter.to_langchain()
    ↓
InMemoryChatMessageHistory.add_message(LangChain Message)
    ↓
[内存存储]
    ↓
InMemoryChatMessageHistory.messages
    ↓
MessageAdapter.from_langchain()
    ↓
ChatHistoryManager.get_messages()
    ↓
Agent.memory (恢复上下文)
```

---

## 核心组件详解

### 1. 消息类型系统 (`app/memory/langchain/messages/`)

#### 1.1 BaseMessage

**位置**: `app/memory/langchain/messages/base.py`

**功能**:
- 所有消息类型的基类
- 支持 `content` (str | list[str | dict])
- 包含元数据：`id`, `name`, `response_metadata`, `additional_kwargs`
- 提供 `text` 属性用于获取文本内容
- 支持内容合并 (`merge_content`)

**关键字段**:
- `content`: 消息内容（字符串或列表）
- `additional_kwargs`: 额外参数字典
- `response_metadata`: 响应元数据（token 计数、模型名等）
- `type`: 消息类型标识
- `name`: 可选名称
- `id`: 可选唯一标识

#### 1.2 具体消息类型

| 消息类型 | 文件 | 特殊字段 | 用途 |
|---------|------|---------|------|
| `HumanMessage` | `human.py` | - | 用户消息 |
| `AIMessage` | `ai.py` | `tool_calls`, `invalid_tool_calls`, `usage_metadata` | AI 回复，包含工具调用 |
| `SystemMessage` | `system.py` | - | 系统提示词 |
| `ToolMessage` | `tool.py` | `tool_call_id`, `name`, `artifact`, `status` | 工具执行结果 |

#### 1.3 MessageChunk 支持

所有消息类型都有对应的 Chunk 版本，用于流式处理：
- `HumanMessageChunk`
- `AIMessageChunk`
- `SystemMessageChunk`
- `ToolMessageChunk`
- `BaseMessageChunk` (基类)

Chunk 支持 `__add__` 操作，可以合并多个 chunk。

### 2. ToolCall 系统 (`app/memory/langchain/messages/tool.py`)

#### 2.1 类型定义

**ToolCall**: 工具调用请求
- `name`: 工具名称
- `args`: 工具参数
- `id`: 调用 ID
- `type`: "tool_call"

**ToolCallChunk**: 流式工具调用
- `name`: 工具名称（可能为 None）
- `args`: 工具参数（流式时可能是部分 JSON）
- `id`: 调用 ID
- `index`: 在序列中的索引
- `type`: "tool_call_chunk"

**InvalidToolCall**: 解析失败的工具调用
- `name`: 工具名称
- `args`: 原始参数字符串
- `id`: 调用 ID
- `error`: 错误信息
- `type`: "invalid_tool_call"

#### 2.2 工厂函数

- `tool_call()`: 创建 ToolCall
- `tool_call_chunk()`: 创建 ToolCallChunk
- `invalid_tool_call()`: 创建 InvalidToolCall

#### 2.3 解析器

- `default_tool_parser()`: 解析原始工具调用列表，返回 (tool_calls, invalid_tool_calls)
- `default_tool_chunk_parser()`: 解析流式工具调用

### 3. ChatHistory 系统 (`app/memory/langchain/chat_history.py`)

#### 3.1 BaseChatMessageHistory

抽象基类，定义接口：
- `messages`: 属性，返回消息列表
- `add_message()`: 添加单条消息
- `add_messages()`: 批量添加消息
- `clear()`: 清空历史
- `aget_messages()`: 异步获取消息
- `aadd_messages()`: 异步添加消息
- `aclear()`: 异步清空
- `add_user_message()`: 便捷方法
- `add_ai_message()`: 便捷方法

#### 3.2 InMemoryChatMessageHistory

内存实现：
- 使用 `List[BaseMessage]` 存储消息
- 支持所有同步和异步方法
- 适合单会话场景

### 4. 消息工具函数 (`app/memory/langchain/messages/utils.py`)

| 函数 | 功能 | 用途 |
|------|------|------|
| `message_to_dict()` | 消息 → 字典 | 序列化 |
| `messages_to_dict()` | 消息列表 → 字典列表 | 批量序列化 |
| `messages_from_dict()` | 字典列表 → 消息列表 | 反序列化 |
| `get_buffer_string()` | 消息列表 → 格式化字符串 | 用于 LLM 提示 |

### 5. MessageAdapter (`app/memory/message_adapter.py`)

**职责**: 在 OpenManus `Message` 和 LangChain `BaseMessage` 之间转换

**关键方法**:
- `to_langchain()`: OpenManus Message → LangChain Message
- `from_langchain()`: LangChain Message → OpenManus Message
- `batch_to_langchain()`: 批量转换
- `batch_from_langchain()`: 批量转换

**转换规则**:
- `Role.USER` → `HumanMessage`
- `Role.ASSISTANT` → `AIMessage` (保留 `tool_calls`)
- `Role.SYSTEM` → `SystemMessage`
- `Role.TOOL` → `ToolMessage` (保留 `tool_call_id`, `name`)

### 6. ChatHistoryManager (`app/memory/chat_history_manager.py`)

**职责**: 提供 OpenManus 兼容的接口，封装 LangChain 实现

**功能**:
- 滑动窗口：默认保留最后 10 轮对话
- 消息格式转换：自动处理 OpenManus ↔ LangChain 转换
- 上下文检索：`get_recent_context()` 用于格式化上下文字符串

**关键方法**:
- `add_message()`: 添加消息
- `add_messages()`: 批量添加消息
- `get_messages()`: 获取消息（支持窗口大小）
- `get_recent_context()`: 获取格式化的上下文字符串
- `clear()`: 清空历史
- `message_count`: 属性，获取消息数量

---

## 与 LangChain 对比

### 对比表

| 功能模块 | LangChain | OpenManus | 状态 |
|---------|-----------|-----------|------|
| **消息类型** |
| BaseMessage | ✅ | ✅ | 完全实现 |
| HumanMessage | ✅ | ✅ | 完全实现 |
| AIMessage | ✅ | ✅ | 完全实现 |
| SystemMessage | ✅ | ✅ | 完全实现 |
| ToolMessage | ✅ | ✅ | 完全实现 |
| MessageChunk | ✅ | ✅ | 完全实现 |
| **消息字段** |
| id | ✅ | ✅ | 完全实现 |
| name | ✅ | ✅ | 完全实现 |
| response_metadata | ✅ | ✅ | 完全实现 |
| additional_kwargs | ✅ | ✅ | 完全实现 |
| content (str/list) | ✅ | ✅ | 完全实现 |
| **AIMessage 特殊字段** |
| tool_calls | ✅ | ✅ | 完全实现 |
| invalid_tool_calls | ✅ | ✅ | 完全实现 |
| usage_metadata | ✅ | ✅ | 完全实现 |
| **ToolMessage 特殊字段** |
| tool_call_id | ✅ | ✅ | 完全实现 |
| artifact | ✅ | ✅ | 完全实现 |
| status | ✅ | ✅ | 完全实现 |
| **ToolCall 系统** |
| ToolCall | ✅ | ✅ | 完全实现 |
| ToolCallChunk | ✅ | ✅ | 完全实现 |
| InvalidToolCall | ✅ | ✅ | 完全实现 |
| tool_call() | ✅ | ✅ | 完全实现 |
| default_tool_parser() | ✅ | ✅ | 完全实现 |
| **ChatHistory** |
| BaseChatMessageHistory | ✅ | ✅ | 完全实现 |
| InMemoryChatMessageHistory | ✅ | ✅ | 完全实现 |
| add_message() | ✅ | ✅ | 完全实现 |
| add_messages() | ✅ | ✅ | 完全实现 |
| aget_messages() | ✅ | ✅ | 完全实现 |
| aadd_messages() | ✅ | ✅ | 完全实现 |
| add_user_message() | ✅ | ✅ | 完全实现 |
| add_ai_message() | ✅ | ✅ | 完全实现 |
| **消息工具函数** |
| message_to_dict() | ✅ | ✅ | 完全实现 |
| messages_to_dict() | ✅ | ✅ | 完全实现 |
| messages_from_dict() | ✅ | ✅ | 完全实现 |
| get_buffer_string() | ✅ | ✅ | 完全实现 |
| merge_content() | ✅ | ✅ | 完全实现 |
| **高级功能** |
| filter_messages() | ✅ | ❌ | 未实现（可选） |
| trim_messages() | ✅ | ❌ | 未实现（可选） |
| merge_message_runs() | ✅ | ❌ | 未实现（可选） |
| convert_to_messages() | ✅ | ❌ | 未实现（可选） |
| convert_to_openai_messages() | ✅ | ❌ | 未实现（可选） |
| **存储** |
| FileChatMessageHistory | ✅ | ❌ | 未实现（使用内存） |
| RedisChatMessageHistory | ✅ | ❌ | 未实现（使用内存） |
| PostgresChatMessageHistory | ✅ | ❌ | 未实现（使用内存） |
| **内容块支持** |
| ContentBlocks | ✅ | ⚠️ | 部分支持（content 支持 list，但无完整 ContentBlock 类型） |

### 详细对比

#### ✅ 已完全实现的功能

1. **核心消息类型**: 所有基础消息类型和 Chunk 版本
2. **消息字段**: 所有核心字段（id, name, metadata 等）
3. **ToolCall 系统**: 完整的工具调用类型和解析器
4. **ChatHistory**: 内存实现的完整功能
5. **序列化**: 消息的序列化和反序列化
6. **异步支持**: 所有异步方法

#### ⚠️ 部分实现的功能

1. **ContentBlocks**:
   - ✅ 支持 `content: list[str | dict]`
   - ❌ 无完整的 ContentBlock TypedDict 定义
   - ❌ 无 ContentBlock 工厂函数
   - **影响**: 不影响核心功能，多模态内容可通过 dict 传递

#### ❌ 未实现的功能（可选）

1. **高级工具函数**:
   - `filter_messages()`: 按类型/ID/名称过滤消息
   - `trim_messages()`: 基于 token 计数修剪消息
   - `merge_message_runs()`: 合并连续的同类型消息
   - `convert_to_messages()`: 从多种格式转换为消息
   - `convert_to_openai_messages()`: 转换为 OpenAI 格式

2. **持久化存储**:
   - `FileChatMessageHistory`: 文件存储
   - `RedisChatMessageHistory`: Redis 存储
   - `PostgresChatMessageHistory`: PostgreSQL 存储
   - **原因**: 当前使用内存存储，适合单会话场景

---

## 实现完整性评估

### 核心功能完整性: 100%

所有核心功能已完全实现：
- ✅ 消息类型系统
- ✅ ToolCall 系统
- ✅ ChatHistory 系统
- ✅ 序列化/反序列化
- ✅ 异步支持

### 高级功能完整性: 0%

高级功能未实现，但这些都是可选功能：
- ❌ 消息过滤和修剪
- ❌ 消息格式转换工具
- ❌ 持久化存储

### 总体评估

**核心功能**: ✅ **完全复刻** (100%)
**高级功能**: ⚠️ **未实现** (0%，但为可选功能)
**总体**: ✅ **核心功能完全复刻，满足项目需求**

### 设计决策

1. **内存存储**: 选择内存存储而非持久化，因为：
   - 单会话场景，无需跨进程持久化
   - 简化实现，减少依赖
   - 性能更好

2. **未实现高级功能**: 这些功能在 LangChain 中也是高级特性：
   - 项目当前不需要消息过滤/修剪
   - 可通过现有 API 实现类似功能
   - 需要时可按需添加

---

## 总结

### 实现成果

1. ✅ **完全复刻 LangChain 核心功能**
   - 所有消息类型和字段
   - 完整的 ToolCall 系统
   - ChatHistory 的完整实现
   - 序列化/反序列化支持

2. ✅ **针对项目优化**
   - 内存存储，适合单会话
   - MessageAdapter 无缝集成
   - ChatHistoryManager 提供便捷接口

3. ✅ **代码质量**
   - 无冗余代码
   - 清晰的架构分层
   - 完整的类型定义

### 与 LangChain 的关系

- **核心功能**: 100% 复刻
- **高级功能**: 未实现（可选）
- **存储方式**: 内存存储（而非持久化）

### 结论

OpenManus 的上下文机制**完全复刻了 LangChain 的核心功能**，所有必需的特性都已实现。未实现的高级功能（如消息过滤、持久化存储）是可选特性，不影响核心使用场景。

当前实现**完全满足项目需求**，支持：
- ✅ 完整的消息类型系统
- ✅ 工具调用和结果传递
- ✅ 上下文跨连接恢复
- ✅ 消息序列化/反序列化

---

**文档维护**: 如有功能更新，请及时更新本文档。

