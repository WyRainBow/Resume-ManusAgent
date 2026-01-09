---
name: 流式输出和Markdown渲染优化计划
overview: 基于对比分析文档，分阶段优化 OpenManus 的流式输出、Markdown 渲染和打字机效果，从核心功能增强到高级功能，最终完成 TypeScript 转换和架构优化。
todos:
  - id: stage1-integrate-components
    content: 阶段1.1：集成 Reference-Sop 组件到主应用（复制组件文件并更新 SophiaChat）
    status: completed
  - id: stage1-thought-typewriter
    content: 阶段1.2：实现 Thought Process 打字机效果
    status: completed
    dependencies:
      - stage1-integrate-components
  - id: stage1-thought-markdown
    content: 阶段1.3：修复 Thought Process Markdown 渲染
    status: completed
    dependencies:
      - stage1-integrate-components
  - id: stage1-cleanup-old-code
    content: 阶段1.4：删除旧的冗余代码（移除 SophiaChat 中的内联 useTypewriter、ThoughtProcess、MarkdownContent 组件）
    status: completed
    dependencies:
      - stage1-integrate-components
      - stage1-thought-typewriter
      - stage1-thought-markdown
  - id: stage2-code-highlight
    content: 阶段2.1：添加代码高亮支持（集成 react-syntax-highlighter 或 shiki）
    status: completed
    dependencies:
      - stage1-integrate-components
  - id: stage2-pause-resume
    content: 阶段2.2：实现暂停/恢复功能（在 useTextStream 中添加控制方法）
    status: completed
    dependencies:
      - stage1-integrate-components
  - id: stage2-async-iterable
    content: 阶段2.3：支持 AsyncIterable 流式输入（完善 WebSocket 流处理）
    status: completed
    dependencies:
      - stage1-integrate-components
  - id: stage3-modularize
    content: 阶段3.1：模块化组件分离（重构目录结构，提取 hooks 和组件）
    status: completed
    dependencies:
      - stage1-integrate-components
      - stage2-code-highlight
  - id: stage3-typescript
    content: 阶段3.2：TypeScript 转换（创建类型定义，转换所有文件为 .tsx）
    status: completed
    dependencies:
      - stage3-modularize
  - id: stage3-unify-interfaces
    content: 阶段3.3：统一组件接口（定义统一的 Props 接口，添加 JSDoc）
    status: completed
    dependencies:
      - stage3-typescript
  - id: stage4-mermaid
    content: 阶段4.1：Mermaid 图表支持（安装依赖，创建 MermaidBlock 组件）
    status: completed
    dependencies:
      - stage3-typescript
  - id: stage4-custom-renderer
    content: 阶段4.2：自定义代码渲染器（实现 component 语言支持和渲染器注册）
    status: completed
    dependencies:
      - stage3-typescript
  - id: stage4-cltp-protocol
    content: 阶段4.3：CLTP 协议支持（研究协议规范，实现 CLTP 客户端，迁移 WebSocket 逻辑）
    status: completed
    dependencies:
      - stage3-typescript
---

# 流式输出和 Markdown 渲染优化计划

## 计划概述

本计划按照对比分析文档的改进建议，分4个优先级阶段优化 OpenManus 的流式输出、Markdown 渲染和打字机效果功能，最终完成 TypeScript 转换和架构优化。

## 阶段1：核心功能增强（优先级1）

### 1.1 集成 Reference-Sop 组件到主应用

**目标**：使用已有的参考实现组件替换内联实现

**文件变更**：

- 复制 `Reference-Sop/frontend/components/ResponseStream.jsx` → `frontend/src/components/ResponseStream.tsx`
- 复制 `Reference-Sop/frontend/components/EnhancedMarkdown.jsx` → `frontend/src/components/EnhancedMarkdown.tsx`
- 复制 `Reference-Sop/frontend/components/ThoughtProcess.jsx` → `frontend/src/components/ThoughtProcess.tsx`

**修改文件**：

- `frontend/src/pages/SophiaChat.jsx` → `frontend/src/pages/SophiaChat.tsx`
  - 移除内联的 `useTypewriter`、`ThoughtProcess`、`MarkdownContent` 组件
  - 导入并使用新的模块化组件
  - 更新 WebSocket 消息处理逻辑以适配新的流式组件

**关键改进**：

- 使用 `requestAnimationFrame` 替代 `setTimeout`（性能提升）
- 支持 `AsyncIterable<string>` 流式输入
- 支持 `fade` 模式

### 1.2 实现 Thought Process 打字机效果

**修改文件**：

- `frontend/src/components/ThoughtProcess.tsx`
  - 集成 `useTextStream` Hook 实现打字机效果
  - 确保在流式输出时启用打字机效果
  - 添加完成状态管理

**预期效果**：

- Thought Process 内容逐字显示
- 与 Response 内容打字机效果协调

### 1.3 修复 Thought Process Markdown 渲染

**修改文件**：

- `frontend/src/components/ThoughtProcess.tsx`
  - 使用 `EnhancedMarkdown` 组件替换纯文本显示
  - 支持 Markdown 格式的思考过程内容

### 1.4 删除旧的冗余代码

**目标**：清理 `SophiaChat.tsx` 中的内联实现，避免代码冗余

**需要删除的代码**：

- `frontend/src/pages/SophiaChat.tsx` 中的内联组件：
  - `useTypewriter` Hook（已被 `ResponseStream` 中的 `useTextStream` 替代）
  - `ThoughtProcess` 组件（已被模块化组件替代）
  - `MarkdownContent` 组件（已被 `EnhancedMarkdown` 组件替代）

**执行时机**：

- 在阶段1.1、1.2、1.3 全部完成并测试通过后执行
- 确保新组件正常工作，旧代码不再被引用

**验证步骤**：

1. 确认所有功能正常工作
2. 检查是否有其他地方引用了旧的内联组件
3. 删除内联组件代码
4. 运行测试确保无回归问题

## 阶段2：功能扩展（优先级2）

### 2.1 添加代码高亮支持

**依赖安装**：

- 确认 `react-syntax-highlighter` 已安装（已在 package.json 中）
- 可选：安装 `shiki` 作为替代方案（更现代，但体积更大）

**修改文件**：

- `frontend/src/components/EnhancedMarkdown.tsx`
  - 集成代码高亮功能
  - 支持多种编程语言
  - 添加代码块复制功能

**实现方案**：

```typescript
// 使用 react-syntax-highlighter 或 shiki
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
```

### 2.2 实现暂停/恢复功能

**修改文件**：

- `frontend/src/components/ResponseStream.tsx`
  - 在 `useTextStream` Hook 中添加 `pause()` 和 `resume()` 方法
  - 保存当前状态以便恢复

**UI 修改**：

- `frontend/src/pages/SophiaChat.tsx`
  - 在消息组件中添加暂停/恢复按钮
  - 处理暂停/恢复状态

### 2.3 支持 AsyncIterable 流式输入

**修改文件**：

- `frontend/src/components/ResponseStream.tsx`
  - 确保 `useTextStream` 完全支持 `AsyncIterable<string>`
  - 处理增量更新逻辑

**WebSocket 集成**：

- `frontend/src/pages/SophiaChat.tsx`
  - 修改 WebSocket 消息处理，支持流式 chunk
  - 创建 AsyncIterable 适配器处理 WebSocket 流

## 阶段3：架构优化（优先级3）

### 3.1 模块化组件分离

**目录结构**：

```
frontend/src/
├── components/
│   ├── chat/
│   │   ├── ResponseStream.tsx
│   │   ├── EnhancedMarkdown.tsx
│   │   ├── ThoughtProcess.tsx
│   │   └── ChatMessage.tsx
│   └── ...
├── hooks/
│   ├── useTextStream.ts
│   ├── useWebSocket.ts
│   └── ...
├── types/
│   ├── chat.ts
│   └── websocket.ts
└── pages/
    └── SophiaChat.tsx
```

**文件变更**：

- 提取 `useTextStream` → `hooks/useTextStream.ts`
- 提取 `ChatMessage` → `components/chat/ChatMessage.tsx`
- 提取 WebSocket 逻辑 → `hooks/useWebSocket.ts`
- 重构 `SophiaChat.tsx` 使用模块化组件

### 3.2 TypeScript 转换

**配置文件**：

- 创建/更新 `tsconfig.json`
- 确保 TypeScript 配置正确

**类型定义**：

- `frontend/src/types/chat.ts`
  ```typescript
  interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    thought?: string;
    timestamp?: string;
  }
  ```

- `frontend/src/types/websocket.ts`
  ```typescript
  interface WebSocketMessage {
    type: 'thought' | 'answer' | 'status' | 'complete' | 'error';
    content?: string;
    is_complete?: boolean;
  }
  ```


**文件转换**：

- 将所有 `.jsx` 文件重命名为 `.tsx`
- 添加完整的类型定义
- 修复类型错误

### 3.3 统一组件接口

**修改文件**：

- 所有组件文件
  - 定义统一的 Props 接口
  - 添加 JSDoc 注释
  - 确保类型一致性

## 阶段4：高级功能（优先级4）

### 4.1 Mermaid 图表支持

**依赖安装**：

- `@mermaid-js/mermaid` 或 `mermaid`

**修改文件**：

- `frontend/src/components/chat/EnhancedMarkdown.tsx`
  - 检测 `language-mermaid` 代码块
  - 创建 `MermaidBlock.tsx` 组件
  - 渲染 Mermaid 图表

**实现**：

```typescript
// 检测 mermaid 代码块
if (language === 'mermaid') {
  return <MermaidBlock code={code} />;
}
```

### 4.2 自定义代码渲染器

**修改文件**：

- `frontend/src/components/chat/EnhancedMarkdown.tsx`
  - 定义代码渲染器接口
  - 实现 `component` 语言支持
  - 允许注册自定义渲染器

**接口定义**：

```typescript
type CustomCodeRenderer = (code: string) => React.ReactNode;
interface EnhancedMarkdownProps {
  customCodeRenderers?: Record<string, CustomCodeRenderer>;
}
```

### 4.3 CLTP 协议支持（可选）

**研究阶段**：

- 分析 CLTP 协议规范
- 评估迁移成本

**实现阶段**（如果决定迁移）：

- 创建 CLTP 客户端
- 迁移现有 WebSocket 逻辑
- 更新消息处理流程

## 实施顺序

1. **阶段1**：核心功能增强（必须）
2. **阶段2**：功能扩展（推荐）
3. **阶段3**：架构优化（重要）
4. **阶段4**：高级功能（可选）

## 关键文件清单

### 需要创建的文件

- `frontend/src/components/chat/ResponseStream.tsx`
- `frontend/src/components/chat/EnhancedMarkdown.tsx`
- `frontend/src/components/chat/ThoughtProcess.tsx`
- `frontend/src/components/chat/ChatMessage.tsx`
- `frontend/src/components/chat/MermaidBlock.tsx`
- `frontend/src/hooks/useTextStream.ts`
- `frontend/src/hooks/useWebSocket.ts`
- `frontend/src/types/chat.ts`
- `frontend/src/types/websocket.ts`

### 需要修改的文件

- `frontend/src/pages/SophiaChat.jsx` → `SophiaChat.tsx`
- `frontend/tsconfig.json`（创建或更新）
- `frontend/package.json`（添加依赖）

### 需要删除的代码

- `frontend/src/pages/SophiaChat.tsx` 中的内联实现：
  - `useTypewriter` Hook（第27-60行）
  - `ThoughtProcess` 组件（第66-104行）
  - `MarkdownContent` 组件（第110-163行）

### 参考文件

- `Reference-Sop/frontend/components/ResponseStream.jsx`
- `Reference-Sop/frontend/components/EnhancedMarkdown.jsx`
- `Reference-Sop/frontend/components/ThoughtProcess.jsx`

## 注意事项

1. **向后兼容**：确保优化不影响现有功能
2. **测试**：每个阶段完成后进行充分测试
3. **性能**：监控 `requestAnimationFrame` 优化后的性能提升
4. **类型安全**：TypeScript 转换时确保类型完整性
5. **代码质量**：保持代码风格一致，添加必要的注释

## 预期成果

- ✅ 性能提升：使用 `requestAnimationFrame` 实现 60fps 流畅动画
- ✅ 功能完整：支持代码高亮、Mermaid 图表、暂停/恢复等高级功能
- ✅ 架构优化：模块化组件，易于维护和扩展
- ✅ 类型安全：完整的 TypeScript 类型定义
- ✅ 用户体验：与 Sophia-Pro 一致的用户体验