# CV Agent 提示词优化调研报告

## 一、调研背景

当前 OpenManus 项目中的 CV Agent（简历分析/优化相关 Agent）提示词存在较多问题，影响用户体验和系统稳定性。本报告通过研究优质开源项目及项目内部优秀 Agent 的实践，分析问题并提出优化方案。

## 二、项目内优秀 Agent 的提示词实践

### 2.1 MCP Agent - 极简设计典范

**文件位置：** `app/agent/mcp.py`、`app/prompt/mcp.py`

#### 提示词特点

| 特点 | 实践方式 |
|------|----------|
| **极简系统提示词** | 仅 20 行，定义角色 + 工具使用指南 |
| **分离式设计** | system_prompt（角色）与 next_step_prompt（引导）分离 |
| **动态工具列表** | 运行时注入可用工具信息 |
| **场景化提示** | 错误、多媒体响应等场景有独立的 prompt 模板 |

#### 提示词结构

**system_prompt（20 行）：**
- 角色定义（1 句话）
- 工具使用指南（4 条）
- 行为准则（6 条）

**next_step_prompt（3 行）：**
- 引导下一步思考
- 不包含具体流程

**场景化 prompt（独立文件）：**
- `TOOL_ERROR_PROMPT` - 工具错误处理
- `MULTIMEDIA_RESPONSE_PROMPT` - 多媒体响应处理

### 2.2 DataAnalysis Agent - 清晰的任务型设计

**文件位置：** `app/agent/data_analysis.py`、`app/prompt/visualization.py`

#### 提示词特点

| 特点 | 实践方式 |
|------|----------|
| **任务聚焦** | 明确"数据分析/可视化"这一特定任务 |
| **变量化配置** | 使用 `{directory}` 等变量动态注入 |
| **分步引导** | next_step_prompt 清晰定义 3 步执行逻辑 |
| **简洁输出** | 仅 10 行左右的核心指令 |

#### 提示词结构

**system_prompt（5 行）：**
- 角色定义（1 句话）
- 工作目录（变量注入）
- 输出要求（1 条）

**next_step_prompt（5 行）：**
- 问题分解引导
- 工具选择原则
- 错误处理指导

### 2.3 ToolCallAgent - 基类提示词

**文件位置：** `app/agent/toolcall.py`、`app/prompt/toolcall.py`

#### 提示词特点

- **极致简洁**：system_prompt 仅 1 行
- **最小化引导**：next_step_prompt 仅 2 行
- **依赖工具描述**：通过工具的 description 参数传递能力

### 2.4 项目内最佳实践总结

| 设计原则 | 说明 |
|----------|------|
| **提示词分离** | system_prompt（角色）与 next_step_prompt（引导）分离 |
| **极简主义** | 系统提示词通常不超过 20 行 |
| **变量化配置** | 使用 `{directory}` 等变量动态注入上下文 |
| **场景化 prompt** | 错误、特殊情况使用独立的 prompt 模板 |
| **工具即文档** | 工具的 description 就是能力说明，不重复在提示词中描述 |
| **流程在代码** | 复杂流程由代码逻辑控制，不写在提示词中 |
| **正面引导** | 使用"做什么"而非"不做什么" |

### 2.5 CV Agent 与优秀 Agent 的对比

| 对比维度 | CV Agent | 优秀 Agent（MCP/DataAnalysis） |
|----------|----------|-------------------------------|
| 系统提示词长度 | 100-140 行 | 5-20 行 |
| 提示词文件 | 硬编码在 Agent 类中 | 独立的 prompt 文件 |
| 变量化配置 | 无 | 有（如 {directory}） |
| 场景化 prompt | 无 | 有（错误、多媒体等） |
| 流程控制 | 写在提示词中 | 由代码逻辑控制 |
| 约束描述 | 大量"禁止"、"绝对不要" | 正面引导"使用"、"做" |
| 输出格式 | 大量示例和格式要求 | 简洁描述或使用 schema |

## 三、当前 CV Agent 提示词问题分析

### 3.1 CVAnalyzer 提示词问题

**文件位置：** `app/agent/cv_analyzer.py`

| 问题类别 | 具体表现 | 影响 |
|----------|----------|------|
| 提示词过长 | system_prompt 约 140 行 | LLM 难以完全遵循 |
| 硬编码 | 直接写在 Agent 类中 | 无法灵活配置 |
| 重复性内容 | 多次强调禁止/正确词汇 | 浪费 token |
| 硬编码示例 | 输出格式示例写在提示词中 | 与实际简历不匹配 |
| 复杂条件逻辑 | "当问题是...时"、"当用户要求...时" | LLM 判断困难 |
| 负面约束 | 大量"绝对不要"、"禁止" | 比正面引导更难遵循 |

### 3.2 CVOptimizer 提示词问题

**文件位置：** `app/agent/cv_optimizer.py`

| 问题类别 | 具体表现 | 影响 |
|----------|----------|------|
| 提示词过长 | system_prompt 约 100 行 | 维护困难 |
| 角色与流程混杂 | 既定义角色又定义四步工作流程 | 流程变更需改核心部分 |
| 硬编码问题模板 | 问题模板写在 Python 代码中 | 修改需要改代码 |
| 职责边界模糊 | 说"不直接修改"但又包含生成逻辑 | 实际行为与声明不一致 |

### 3.3 CVReader 提示词问题

**文件位置：** `app/agent/cv_reader.py`

| 问题类别 | 具体表现 | 影响 |
|----------|----------|------|
| 负面约束过多 | 大量"绝对不要"、"禁止" | LLM 难以遵循 |
| 输出示例固定 | 示例格式完全固定 | 无法适应不同场景 |
| 动作指令冗余 | "立即调用"、"给出完整回答后立即调用" | 增加 token 消耗 |

### 3.4 CVEditor 提示词问题

**文件位置：** `app/agent/cv_editor.py`

| 问题类别 | 具体表现 | 影响 |
|----------|----------|------|
| 提示词过于简单 | 仅描述能力，缺少约束 | 行为不稳定 |
| 缺少错误处理指导 | 没有定义错误情况的处理方式 | 失败时体验差 |

### 3.5 共性问题总结

1. **提示词硬编码**：写在 Agent 类中，无法灵活配置
2. **提示词过长**：100+ 行，远超项目内优秀 Agent 的 5-20 行
3. **负面约束过多**：大量"禁止"、"绝对不要"，比正面引导更难遵循
4. **缺少场景化 prompt**：错误、特殊情况没有独立的 prompt 模板
5. **流程写在提示词中**：复杂流程应由代码逻辑控制
6. **输出格式冗长**：大量示例和格式要求占用 token

## 四、优化方案设计

### 4.1 设计原则（参考项目内优秀 Agent）

#### 原则 1：提示词分离

| 文件 | 内容 | 参考 |
|------|------|------|
| `app/prompt/cv_analyzer.py` | CVAnalyzer 提示词 | `app/prompt/mcp.py` |
| `app/prompt/cv_optimizer.py` | CVOptimizer 提示词 | `app/prompt/visualization.py` |
| `app/prompt/cv_reader.py` | CVReader 提示词 | - |
| `app/prompt/cv_editor.py` | CVEditor 提示词 | - |

每个文件包含：
- `SYSTEM_PROMPT` - 系统提示词（角色定义）
- `NEXT_STEP_PROMPT` - 下一步引导
- `ERROR_PROMPT` - 错误处理（可选）
- `OUTPUT_FORMAT_PROMPT` - 输出格式（可选）

#### 原则 2：极简主义

**系统提示词结构（参考 MCP Agent）：**

| 结构 | 内容 | 目标长度 |
|------|------|----------|
| 角色定义 | 1-2 句话 | 2 行 |
| 核心职责 | 3-5 条正面引导 | 10 行 |
| 输出要求 | 1-2 条 | 3 行 |
| **总计** | | **15 行左右** |

**对比当前 100+ 行，减少 85%**

**关键改进：**
- 移除所有冗长的示例
- 移除重复的约束说明
- 将"禁止 X"改为"使用 Y"

#### 原则 3：变量化配置

**使用变量动态注入上下文（参考 DataAnalysis Agent）：**

```
示例：
SYSTEM_PROMPT = """你是专业的简历分析师。
工作目录：{directory}
当前简历：{resume_name}
分析深度：{analysis_level}
"""
```

#### 原则 4：场景化 Prompt

**为不同场景准备独立的 prompt 模板（参考 MCP Agent）：**

| 场景 | Prompt 变量 |
|------|-------------|
| 简单分析 | `SIMPLE_ANALYSIS_PROMPT` |
| 深度分析 | `DEEP_ANALYSIS_PROMPT` |
| 工具错误 | `TOOL_ERROR_PROMPT` |
| 格式错误 | `FORMAT_ERROR_PROMPT` |

#### 原则 5：流程在代码

**当前问题：** 多步骤流程写在提示词中

**优化方案：**
- 流程由 Agent 类的方法控制
- 提示词只定义"当前步骤"的行为
- 使用状态机管理流程（如已有 ConversationManager）

### 4.2 配置文件结构设计

```
app/
├── prompt/
│   ├── cv_analyzer.py      # CVAnalyzer 提示词（新增）
│   ├── cv_optimizer.py     # CVOptimizer 提示词（新增）
│   ├── cv_reader.py        # CVReader 提示词（新增）
│   ├── cv_editor.py        # CVEditor 提示词（新增）
│   ├── mcp.py              # MCP 提示词（已有，参考）
│   ├── visualization.py    # DataAnalysis 提示词（已有，参考）
│   └── manus.py            # Manus 提示词（已有）
│
├── agent/
│   ├── cv_analyzer.py      # 修改：从 prompt 文件导入
│   ├── cv_optimizer.py     # 修改：从 prompt 文件导入
│   ├── cv_reader.py        # 修改：从 prompt 文件导入
│   └── cv_editor.py        # 修改：从 prompt 文件导入
```

### 4.3 提示词模板结构

#### CVAnalyzer 提示词结构（参考 MCP Agent）

**文件：app/prompt/cv_analyzer.py**

```
SYSTEM_PROMPT
├── 角色定义（2 行）
├── 核心职责（10 条正面引导）
└── 输出要求（3 条）

NEXT_STEP_PROMPT（3 行）
└── 调用工具 + 一次性输出

场景化 Prompt
├── SIMPLE_ANALYSIS_PROMPT
└── DEEP_ANALYSIS_PROMPT
```

#### CVOptimizer 提示词结构（参考 DataAnalysis Agent）

**文件：app/prompt/cv_optimizer.py**

```
SYSTEM_PROMPT
├── 角色定义（2 行）
├── 核心职责（8 条）
└── 输出要求（2 行）

NEXT_STEP_PROMPT
├── 获取简历状态
└── 针对当前模块提问
```

### 4.4 输出格式管理

**当前问题：** 输出格式占用大量提示词空间

**优化方案：**
1. 使用 Pydantic 模型定义输出格式（已有 schema.py）
2. 提示词中只引用格式名称
3. 格式示例放到独立文档或测试文件

### 4.5 状态管理优化

**当前问题：** 多步流程状态依赖提示词描述

**优化方案：**
- 使用已有的 ConversationManager 管理状态
- 流程步骤由代码逻辑控制
- 提示词根据当前状态动态生成

```
示例：根据状态选择 prompt
if state == "simple_analysis":
    return SIMPLE_ANALYSIS_PROMPT
elif state == "deep_analysis":
    return DEEP_ANALYSIS_PROMPT
```

## 五、具体优化建议

### 5.1 CVAnalyzer 优化

| 当前 | 优化后 |
|------|--------|
| 140 行系统提示词 | 20 行左右 |
| 硬编码在类中 | 独立 `app/prompt/cv_analyzer.py` |
| 包含大量示例 | 移除示例，使用简洁描述 |
| "当问题是...时"条件逻辑 | 由代码判断，注入对应 prompt |
| "禁止使用候选人" | "使用您/你的称呼用户" |

### 5.2 CVOptimizer 优化

| 当前 | 优化后 |
|------|--------|
| 100 行系统提示词 | 15 行左右 |
| 四步流程写在提示词中 | 流程由代码控制 |
| 问题模板在代码中 | 移到配置或独立文件 |
| "不直接修改" | 明确角色：建议者 vs 执行者 |

### 5.3 CVReader 优化

| 当前 | 优化后 |
|------|--------|
| 大量"绝对不要"、"禁止" | 正面引导 |
| 固定输出示例 | 简洁格式描述 |
| "立即调用"等冗余指令 | 移除冗余描述 |

### 5.4 CVEditor 优化

| 当前 | 优化后 |
|------|--------|
| 仅描述能力 | 添加行为约束 |
| 无错误处理指导 | 添加错误处理 prompt |

## 六、实施计划

### 阶段一：提示词文件分离（1 周）

**任务：**
1. 创建 `app/prompt/cv_analyzer.py`
2. 创建 `app/prompt/cv_optimizer.py`
3. 创建 `app/prompt/cv_reader.py`
4. 创建 `app/prompt/cv_editor.py`
5. 修改各 Agent 类，从 prompt 文件导入

**预期成果：**
- 提示词与代码分离
- 参考项目内优秀 Agent 的结构

### 阶段二：提示词内容优化（1 周）

**任务：**
1. 缩短系统提示词到 20 行以内
2. 移除负面约束，改为正面引导
3. 提取示例到独立文档
4. 添加场景化 prompt

**预期成果：**
- 提示词长度显著减少
- 风格与项目内优秀 Agent 一致

### 阶段三：流程代码化（1 周）

**任务：**
1. 将流程逻辑从提示词移到代码
2. 利用已有的 ConversationManager
3. 实现状态判断和 prompt 动态选择

**预期成果：**
- 提示词更加简洁
- 流程控制更加可靠

### 阶段四：测试与验证（持续）

**任务：**
1. 测试各 Agent 的输出质量
2. 测试错误场景的处理
3. A/B 对比优化前后的效果

## 七、风险评估

| 风险 | 可能性 | 影响 | 缓解措施 |
|------|--------|------|----------|
| 输出质量下降 | 中 | 高 | 充分测试，保留优化前的版本 |
| 状态管理复杂化 | 中 | 中 | 利用已有的 ConversationManager |
| 迁移工作量 | 低 | 中 | 渐进式迁移，一次一个 Agent |

## 八、参考资料

### 项目内参考

1. `app/agent/mcp.py` - MCP Agent 极简设计
2. `app/prompt/mcp.py` - MCP Agent 提示词结构
3. `app/agent/data_analysis.py` - DataAnalysis Agent
4. `app/prompt/visualization.py` - DataAnalysis 提示词结构
5. `app/agent/toolcall.py` - ToolCallAgent 基类
6. `app/prompt/toolcall.py` - 基类提示词

### 外部参考

7. [LangChain GitHub Repository](https://github.com/langchain-ai/langchain)
8. [CrewAI Documentation - Customizing Prompts](https://docs.crewai.com/en/guides/advanced/customizing-prompts)
9. [OpenAI Swarm GitHub Repository](https://github.com/openai/swarm)
10. [Top AI Agent Frameworks in 2025](https://medium.com/@elisowski/top-ai-agent-frameworks-in-2025-9bcedab2e239)

---

**文档版本：** v3.0
**创建日期：** 2025-01-03
**更新日期：** 2025-01-03
**作者：** Claude (OpenManus 项目)
