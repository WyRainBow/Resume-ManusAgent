# Reference-Sop - 意图识别、Thought Process、流式输出和 Markdown 渲染演示

本项目复刻了 sophia-pro 项目的核心聊天功能，包括：

1. **意图识别** - 识别用户输入的意图类型（问候、简单对话、任务导向等）
2. **Thought Process** - 显示 AI 的思考过程
3. **流式输出** - 实时流式输出 AI 响应
4. **打字机效果** - 优雅的打字机动画效果
5. **Markdown 渲染** - 增强的 Markdown 内容渲染

## 项目结构

```
Reference-Sop/
├── backend/              # 后端代码
│   ├── intent_classifier.py    # 意图分类器
│   └── intent_handler.py       # 意图处理集成
├── frontend/             # 前端代码
│   ├── components/       # React 组件
│   │   ├── ResponseStream.jsx      # 流式输出和打字机效果
│   │   ├── ThoughtProcess.jsx      # 思考过程显示
│   │   └── EnhancedMarkdown.jsx    # 增强的 Markdown 渲染
│   └── pages/            # 页面
│       └── ChatDemo.jsx           # 演示页面
└── README.md             # 本文档
```

## 功能说明

### 1. 意图识别

意图分类器可以识别以下类型的用户输入：

- **问候 (GREETING)**: "你好", "hello", "介绍一下自己" 等
- **简单对话 (CASUAL_CHAT)**: "谢谢", "再见", "怎么样" 等
- **任务导向 (TASK_ORIENTED)**: "帮我", "分析", "生成" 等
- **普通对话 (GENERAL_CHAT)**: 其他类型

### 2. Thought Process

显示 AI 的思考过程，包括：
- 意图识别结果
- 推理过程
- 处理策略

### 3. 流式输出和打字机效果

支持两种显示模式：
- **typewriter**: 打字机效果，逐字符显示
- **fade**: 淡入效果，逐词显示

### 4. Markdown 渲染

支持完整的 Markdown 语法：
- 标题、段落、列表
- 代码块和行内代码
- 表格、链接、引用
- 粗体、斜体等格式

## 使用方法

### 后端集成

1. 在 WebSocket 消息处理中集成意图识别：

```python
from Reference_Sop.backend.intent_handler import handle_intent_recognition

# 在处理用户消息时
intent_result = await handle_intent_recognition(
    user_message=user_input,
    client_id=client_id,
    connection_manager=connection_manager,
)
```

2. 根据意图结果决定响应方式：

```python
from Reference_Sop.backend.intent_handler import should_use_casual_response

if should_use_casual_response(intent_result):
    # 使用简单对话响应方式
    # 不需要 ask_human、需求澄清等
    pass
```

### 前端使用

1. 在 `frontend/src/App.jsx` 中导入并使用 `ChatDemo` 组件：

```jsx
import ChatDemo from './Reference-Sop/frontend/pages/ChatDemo';

// 在路由中使用
<Route path="/chat-demo" element={<ChatDemo />} />
```

或者直接替换现有的 `App.jsx` 内容。

2. 确保安装了必要的依赖：

```bash
cd frontend
npm install react-markdown remark-gfm remark-breaks lucide-react
```

## 演示

启动项目后，在聊天界面输入 **"你好"**，你将看到：

1. **意图识别结果** - 显示识别为"问候"类型，并显示推理过程
2. **Thought Process** - 展开显示 AI 的思考过程
3. **流式输出** - AI 的回答以打字机效果逐字显示
4. **Markdown 渲染** - 如果回答包含 Markdown 格式，会正确渲染

## 技术细节

### 意图识别算法

- 使用关键词匹配进行快速识别
- 支持中英文关键词
- 返回置信度和推理过程

### 流式输出实现

- 使用 `requestAnimationFrame` 实现平滑动画
- 支持字符串和异步迭代器两种输入方式
- 可配置速度和显示模式

### Markdown 渲染

- 基于 `react-markdown` 库
- 使用 `remark-gfm` 支持 GitHub Flavored Markdown
- 使用 `remark-breaks` 支持换行
- 自定义样式类名，符合 Tailwind CSS 设计

## 注意事项

1. 确保后端 WebSocket 服务正常运行（默认端口 8080）
2. 前端需要连接到正确的 WebSocket 地址
3. 意图识别结果会通过 WebSocket 发送到前端
4. Thought Process 内容需要后端在适当的时候发送 `thought` 类型消息

## 扩展

你可以根据需要扩展以下功能：

1. **更复杂的意图识别** - 集成 LLM 进行更准确的意图识别
2. **更多显示模式** - 添加更多流式输出的显示效果
3. **自定义 Markdown 组件** - 添加代码高亮、图表等高级功能
4. **多语言支持** - 扩展意图识别支持更多语言

## 参考

本实现参考了以下项目：
- sophia-pro 项目的意图识别系统
- sophia-pro 项目的流式输出组件
- sophia-pro 项目的 Markdown 渲染组件





