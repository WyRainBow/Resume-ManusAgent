# OpenManus - 简历优化 AI Agent

<p align="center">
  <img src="assets/logo.jpg" width="200"/>
</p>

基于 [OpenManus](https://github.com/FoundationAgents/OpenManus) 框架构建的智能简历优化 Agent，提供专业的简历分析、优化建议和对话式交互体验。

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)

## ✨ 核心功能

### 🤖 智能简历分析
- **模块化分析系统**：教育经历、工作经历、实习经历、项目经历、技能等独立分析模块
- **深度内容分析**：自动识别简历中的问题点，提供针对性的优化建议
- **优先级评分**：智能评估各模块的优化优先级，帮助用户聚焦关键问题

### 💬 引导性对话
- **意图识别**：智能识别用户意图（问候、简单对话、任务导向等）
- **主动引导**：AI 主动提出优化建议，引导用户完成简历优化
- **上下文记忆**：基于 LangChain 的 Memory 系统，支持多轮对话和上下文保持

### 🎨 现代化交互体验
- **流式输出**：实时流式响应，提供流畅的交互体验
- **Thought Process**：展示 AI 的思考过程，增强用户信任
- **Markdown 渲染**：支持完整的 Markdown 语法，优雅展示分析结果
- **打字机效果**：优雅的动画效果，提升用户体验

### 📊 数据管理
- **简历数据存储**：统一的简历数据管理（ResumeDataStore）
- **版本控制**：支持简历优化的版本回溯（Checkpoint）
- **对话历史**：完整的对话历史记录和管理

## 🏗️ 技术架构

### 后端技术栈
- **框架**：FastAPI + WebSocket
- **AI 框架**：基于 OpenManus 的 Agent 系统
- **LLM 支持**：OpenAI、Azure OpenAI、Anthropic、Google 等
- **记忆系统**：LangChain Memory（ChatHistoryManager、ConversationStateManager）
- **工具系统**：MCP (Model Context Protocol) 支持

### 前端技术栈
- **框架**：React 18 + Vite
- **样式**：Tailwind CSS
- **Markdown**：react-markdown + rehype-highlight
- **图标**：lucide-react

## 📦 安装指南

### 环境要求
- Python 3.12+
- Node.js 18+
- Conda（推荐）或 uv

### 后端安装

1. **创建 conda 环境**：
```bash
conda create -n openmanus python=3.12
conda activate openmanus
```

2. **克隆仓库**：
```bash
git clone https://github.com/WyRainBow/Resume-ManusAgent.git
cd Resume-ManusAgent
```

3. **安装依赖**：
```bash
pip install -r requirements.txt
```

4. **安装浏览器自动化工具**（可选）：
```bash
playwright install
```

### 前端安装

```bash
cd frontend
npm install
```

## ⚙️ 配置说明

### 1. 创建配置文件

复制示例配置文件：
```bash
cp config/config.example.toml config/config.toml
```

### 2. 配置 LLM API

编辑 `config/config.toml`，添加您的 API 密钥：

```toml
[llm]
model = "gpt-4o"
base_url = "https://api.openai.com/v1"
api_key = "sk-..."  # 替换为您的 API 密钥
max_tokens = 4096
temperature = 0.3
api_type = "Openai"
api_version = ""
```

支持的 API 类型：
- `Openai`：OpenAI API
- `AzureOpenai`：Azure OpenAI
- `Anthropic`：Anthropic Claude
- `Ollama`：本地 Ollama 模型
- 其他：参考 `config/config.example-*.toml`

### 3. 可选配置

- **浏览器配置**：`[browser]` 部分
- **搜索配置**：`[search]` 部分
- **沙箱配置**：`[sandbox]` 部分
- **MCP 配置**：`config/mcp.json`

## 🚀 快速启动

### 启动后端服务

使用 conda 环境启动（推荐）：
```bash
bash -c "eval \"\$(conda shell.bash hook)\" && conda activate openmanus && python -m uvicorn app.web.server:app --host 0.0.0.0 --port 8000 --reload"
```

或使用启动脚本：
```bash
bash start_web.sh
```

后端服务将在 `http://localhost:8000` 启动。

### 启动前端服务

```bash
cd frontend
npm run dev
```

前端服务将在 `http://localhost:5173` 启动。

### 访问应用

打开浏览器访问：`http://localhost:5173`
