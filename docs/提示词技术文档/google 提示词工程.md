# Google 提示词工程 (Prompt Engineering) v7

> 基于 Google 官方《Introduction to Large Language Models》和《Prompt Engineering Best Practices》整理

---

## 概述

Google Prompt Engineering v7 是 Google 官方发布的提示词工程最佳实践指南，旨在帮助开发者更有效地与大语言模型（LLM）交互。这些实践经过 Google 内部大量实验验证，适用于各类 LLM 应用场景。

### 核心设计原则

| 原则 | 说明 |
|------|------|
| **简洁性** | 提示词应简明扼要，删除无关内容 |
| **正面表述** | 告诉模型"做什么"而非"不做什么" |
| **结构清晰** | 使用明确的步骤和格式 |
| **提供示例** | 通过示例展示期望行为 |

---

## 一、12 条最佳实践

### 1. 提供示例 (Provide Examples)

**核心思想**：通过具体示例展示期望的输入和输出模式。

```python
# ❌ 不好的做法
prompt = "判断情感：我很开心"

# ✅ 好的做法
prompt = """判断文本的情感类别（正面/负面/中性）

示例：
输入：今天天气真好！  输出：正面
输入：这个产品质量太差了。  输出：负面
输入：明天会议在3点。  输出：中性

输入：我很开心  输出："""
```

**应用场景**：
- 文本分类
- 格式转换
- 数据提取

---

### 2. 简洁设计 (Keep It Simple)

**核心思想**：删除任何对任务无关的内容，避免冗余表述。

```python
# ❌ 冗长表述
prompt = """
作为一名拥有多年经验的专业自然语言处理助手，我需要你帮我完成以下任务。
请仔细分析下面的文本，并按照要求给出答案...
"""

# ✅ 简洁表述
prompt = """分析以下文本并提取关键信息：

{content}

输出格式：JSON
"""
```

**关键要点**：
- 避免"作为..."、"请仔细..."等客套话
- 直接说明任务和要求
- 每句话都有实际作用

---

### 3. 清晰输出 (Be Clear About Output)

**核心思想**：明确指定输出格式和结构。

```python
# ❌ 模糊要求
prompt = "分析这段简历"

# ✅ 明确格式
prompt = """分析简历并输出以下格式的 JSON：

{
  "name": "姓名",
  "education": ["学校1", "学校2"],
  "strengths": ["亮点1", "亮点2"],
  "suggestions": ["建议1", "建议2"]
}

简历内容：{resume}
"""
```

**推荐格式**：
- JSON：结构化数据
- Markdown：文档输出
- 表格：对比类内容

---

### 4. 使用指令而非约束 (Use Instructions, Not Constraints)

**核心思想**：正面引导比负面约束更有效。

```python
# ❌ 负面约束
prompt = """
不要生成过长的回答
不要使用技术术语
不要提到竞争对手
"""

# ✅ 正面指令
prompt = """
保持回答在100字以内
使用通俗易懂的语言
聚焦于产品核心功能
"""
```

**原因**：LLM 对正面指令的理解更准确，负面约束可能被忽略。

---

### 5. 控制 Token 长度 (Control Token Length)

**核心思想**：删除不必要的上下文，减少 Token 消耗。

```python
# ❌ 冗余上下文
prompt = """
以下是公司历史背景信息...
（500字公司介绍）
...

现在请回答：我们的客服电话是多少？
"""

# ✅ 精简上下文
prompt = """客服电话：400-123-4567

根据以上信息回答用户问题。
"""
```

**优化策略**：
- 只包含任务相关的上下文
- 使用引用而非全文
- 动态加载必要信息

---

### 6. 使用变量 (Use Variables)

**核心思想**：使用占位符实现模板复用。

```python
# 模板定义
template = """你好 {name}，欢迎来到 {place}！

当前有 {count} 个任务待处理。"""

# 使用时填充
result = template.format(
    name="张三",
    place="OpenManus",
    count=5
)
```

**本项目实现**：`app/prompt/base.py` 中的 `PromptTemplate` 类

```python
from app.prompt.base import PromptTemplate

# 定义模板
SYSTEM_PROMPT = PromptTemplate.from_template("""
你是 OpenManus，当前目录：{directory}
当前状态：{context}
""")

# 预填充常用值
BASE_PROMPT = SYSTEM_PROMPT.partial(directory="/workspace")

# 使用时只需传动态变量
result = BASE_PROMPT.format(context="ready")
```

---

### 7. 尝试不同格式 (Experiment with Formats)

**核心思想**：同一内容用不同格式表达，效果可能不同。

```python
# 格式1：列表
prompt = """
分析要点：
1. 检查语法
2. 检查逻辑
3. 检查格式
"""

# 格式2：表格
prompt = """
| 检查项 | 说明 |
|--------|------|
| 语法 | 检查拼写和语法 |
| 逻辑 | 检查逻辑连贯性 |
| 格式 | 检查排版格式 |
"""

# 格式3：JSON
prompt = """
{"checks": ["语法", "逻辑", "格式"]}
"""
```

**建议**：针对不同任务尝试不同格式，选择效果最好的。

---

### 8. 混合类别 (Mix Categories in Few-Shot)

**核心思想**：在 few-shot 示例中混合不同类别，避免模型产生偏差。

```python
# ❌ 顺序分组（可能产生偏差）
prompt = """
正面示例：
1. 这个产品很棒！
2. 我非常喜欢这个服务。

负面示例：
1. 质量太差了。
2. 完全不推荐。
"""

# ✅ 混合排列
prompt = """
示例：
1. 这个产品很棒！ → 正面
2. 质量太差了。 → 负面
3. 服务态度很好。 → 正面
4. 完全不推荐。 → 负面
"""
```

---

### 9. 适应模型更新 (Adapt to Model Updates)

**核心思想**：模型会定期更新，提示词也需要相应调整。

**建议**：
- 定期评估提示词效果
- 关注模型更新日志
- 建立 A/B 测试机制
- 保留多个版本进行对比

---

### 10. 使用结构化输出 (Use Structured Output)

**核心思想**：JSON 等结构化格式可以减少幻觉。

```python
# ✅ JSON 格式输出
prompt = """请以以下 JSON 格式输出简历分析结果：

{
  "overall_score": 85,
  "strengths": ["亮点1", "亮点2"],
  "weaknesses": ["不足1", "不足2"],
  "suggestions": ["建议1", "建议2"]
}
"""
```

**本项目应用**：模块分析器使用 JSON 输出

```python
# app/prompt/star_framework.py
ANALYZE_PROMPT = """
输出 JSON 格式分析结果：
{
  "situation": "背景",
  "task": "任务",
  "action": "行动",
  "result": "结果"
}
"""
```

---

### 11. Chain-of-Thought 最佳实践

**核心思想**：复杂推理任务需要展示思考过程。

**关键配置**：
- **Temperature = 0**：确保推理的确定性
- **明确步骤**：告诉模型先分析再得出结论

```python
# CoT 模板
prompt = """
请按以下步骤分析简历：

步骤1：识别候选人的教育背景和工作年限
步骤2：分析项目经历的技术深度
步骤3：评估技能与岗位的匹配度
步骤4：给出综合评分和建议

简历内容：{resume}

分析过程："""
```

**配置建议**：

| 任务类型 | Temperature | 说明 |
|---------|-------------|------|
| CoT 推理 | 0 | 确定性思维链 |
| 内容生成 | 0.7-1.0 | 创造性和多样性 |
| 分类/提取 | 0-0.3 | 高准确性 |

---

### 12. 记录尝试 (Keep Track of Attempts)

**核心思想**：系统化地记录和比较不同提示词版本。

**建议格式**：

```python
"""
版本：v1.2
日期：2025-01-06
任务：简历情感分析

提示词：
[具体的提示词内容]

测试结果：
- 准确率：85%
- 样本数：100
- 失败案例：[列举]

改进方向：
- 增加更多示例
- 简化输出格式
"""
```

---

## 二、核心技术

### 1. Zero-Shot Prompting

不提供示例，直接描述任务。

```python
prompt = """将以下文本翻译成中文：

Hello, how are you today?
"""
```

**适用场景**：
- 简单任务
- 常见操作（翻译、摘要）
- 模型已有充分知识的领域

---

### 2. Few-Shot Prompting

提供 1-5 个示例，展示期望行为。

```python
prompt = """将以下文本转换为 JSON 格式：

示例：
输入：张三，男，30岁，工程师
输出：{"name": "张三", "gender": "男", "age": 30, "job": "工程师"}

输入：李四，女，25岁，设计师
输出：{"name": "李四", "gender": "女", "age": 25, "job": "设计师"}

输入：王五，男，35岁，产品经理
输出："""
```

**最佳实践**：
- 示例数量：3-5 个效果最佳
- 混合不同类别
- 使用真实数据作为示例

---

### 3. Chain-of-Thought (CoT)

引导模型展示推理过程。

```python
# 标准 CoT
prompt = """
小明有5个苹果，他给了小红2个，又买了3个。
请问小明现在有几个苹果？

让我们一步步计算：
1. 小明原有：5个
2. 给小红后：5 - 2 = 3个
3. 买新的后：3 + 3 = 6个
4. 最终答案：6个
"""
```

**本项目应用**：STAR 框架分析

```python
# app/prompt/star_framework.py
STEP_BY_STEP_GUIDANCE = """
分析步骤：
1. 阅读经历描述，提取关键信息
2. 识别情境（Situation）- 背景和环境
3. 识别任务（Task）- 面临的挑战
4. 识别行动（Action）- 采取的具体措施
5. 识别结果（Result）- 取得的成果
6. 按照 STAR 格式重组内容
"""
```

---

### 4. ReAct (Reasoning + Acting)

结合推理和行动，适合 Agent 应用。

```python
prompt = """
工具：
- search: 搜索信息
- calculate: 计算数值

问题：北京今天天气如何？

思考：我需要获取北京今天的天气信息
行动：search("北京今天天气")

观察：晴天，气温15-25度

思考：信息已获取，可以回答
回答：北京今天是晴天，气温15-25度。
"""
```

**本项目应用**：Manus Agent

```python
# app/prompt/manus.py
NEXT_STEP_PROMPT = """
根据用户需求选择合适的工具。

工具选择：
1. 具体修改 → cv_editor_agent
2. 模块分析 → education_analyzer
3. 整体分析 → cv_analyzer_agent

使用工具后解释结果，并提出下一步建议。
"""
```

---

### 5. System/Role/Context Prompts

三层提示词结构。

| 层级 | 作用 | 示例 |
|------|------|------|
| **System** | 定义角色、行为模式 | "你是简历分析专家..." |
| **Role** | 具体任务角色 | "作为教育背景分析员..." |
| **Context** | 当前上下文 | "当前分析对象：计算机专业应届生" |

```python
# OpenManus 双提示词结构
SYSTEM_PROMPT = """你是 OpenManus，专注于简历优化和求职指导。

核心能力：
1. 简历分析
2. 简历优化
3. 内容增强
...
"""

NEXT_STEP_PROMPT = """根据用户需求选择合适的工具。
当前状态：{context}
可用工具：{tools}
"""
```

---

## 三、配置参数指南

### Temperature

控制输出的随机性和创造性。

| 值 | 范围 | 适用场景 |
|----|------|----------|
| **0** | 确定性 | CoT 推理、数据提取、代码生成 |
| **0.1-0.3** | 低变化 | 事实性问答、翻译 |
| **0.4-0.7** | 中等变化 | 内容创作、对话 |
| **0.7-1.0** | 高变化 | 头脑风暴、创意写作 |

**配置示例**：

```python
# CoT 推理：使用 temperature=0
response = llm.complete(
    prompt=reasoning_prompt,
    temperature=0  # 确保推理稳定
)

# 创意生成：使用 temperature=0.8
response = llm.complete(
    prompt=creative_prompt,
    temperature=0.8  # 鼓励多样性
)
```

---

### Top-K 和 Top-P

控制输出的多样性。

| 参数 | 说明 | 推荐值 |
|------|------|--------|
| **Top-K** | 只考虑概率最高的 K 个 token | 40 |
| **Top-P** | 核采样，累积概率达到 P 时停止 | 0.95 |

**一般使用**：保持默认值即可，除非有特殊需求。

---

### Max Tokens

控制输出长度。

```python
# 短回答：摘要、分类
max_tokens = 100

# 中等长度：解释、分析
max_tokens = 500

# 长输出：文章生成、详细分析
max_tokens = 2000
```

---

## 四、与本项目对比

### 当前实现状态

| Google 最佳实践 | 本项目状态 | 说明 |
|----------------|-----------|------|
| 正面简洁表述 | ✅ 已实现 | MCP Agent 风格，`mcp.py`、`manus.py` |
| JSON 结构化输出 | ✅ 已实现 | 模块分析器使用 JSON 格式 |
| 双提示词结构 | ✅ 已实现 | System + NextStep |
| 输入验证 | ✅ 已实现 | `PromptTemplate.format()` 验证 |
| 部分填充 | ✅ 已实现 | `PromptTemplate.partial()` |
| 模板组合 | ✅ 已实现 | `+` 操作符 |
| Temperature=0 for CoT | ⚠️ 待明确 | 需要在配置中明确 |
| Few-shot 示例 | ⚠️ 可增强 | 可在提示词中增加示例 |
| 变量使用 | ✅ 已实现 | `{directory}`, `{context}` 等 |

---

### 优化建议

#### 1. 增加 Few-shot 示例

```python
# app/prompt/cv_analyzer.py
SIMPLE_ANALYSIS_PROMPT = PromptTemplate.from_template("""
分析简历并输出关键信息。

示例分析：
输入：计算机专业本科，3年后端开发经验，精通 Java/Python
输出：{{"background": "计算机科班", "experience": "中级开发", "skills": ["Java", "Python"]}}

当前简历：
{resume}

输出：""")
```

#### 2. 明确 Temperature 配置

```python
# app/agent/cv_analyzer.py
# CoT 分析任务使用 temperature=0
response = await self.llm.ask_tool(
    messages=messages,
    temperature=0,  # 确保推理稳定性
    tools=tools
)
```

#### 3. 统一表述风格

参考 `mcp.py` 的简洁风格，优化其他提示词：

```python
# 优化前（负面表述）
"不要生成过长的回答"
"不要使用 markdown 格式"

# 优化后（正面表述）
"保持回答简洁"
"使用纯文本格式"
```

---

## 五、实战示例

### 示例 1：简历分析

```python
# app/prompt/cv_analyzer.py
ANALYSIS_PROMPT = """分析以下简历并输出 JSON 格式结果。

分析维度：
1. 教育背景：学校、专业、学历
2. 工作经验：年限、公司、职位
3. 核心技能：技术栈、熟练度
4. 项目经历：项目数量、技术深度
5. 亮点总结：3-5 个核心优势

输出格式：
{
  "education": {"school": "", "major": "", "degree": ""},
  "experience": {"years": 0, "companies": [""]},
  "skills": [{"name": "", "level": ""}],
  "projects": [{"name": "", "tech": [""]}],
  "highlights": [""]
}

简历内容：
{resume}
"""
```

---

### 示例 2：内容优化

```python
# app/prompt/cv_editor.py
OPTIMIZATION_PROMPT = """优化简历经历描述，使其更专业、更有说服力。

优化原则：
1. 使用 STAR 结构（情境-任务-行动-结果）
2. 量化成果（数字、百分比）
3. 使用行为动词开头
4. 突出个人贡献

示例：
原文：负责项目开发
优化：主导核心模块开发，用户响应时间从500ms降至80ms，性能提升84%

待优化内容：
{content}

优化结果："""
```

---

### 示例 3：引导性对话

```python
# app/prompt/manus.py
GUIDED_CONVERSATION = """你是 OpenManus，专注于简历优化。

开场白：
"您好！我是 OpenManus，专注于简历优化和求职指导。

我可以帮您：
1. 分析简历结构和内容
2. 优化经历描述
3. 提供求职建议

您想从哪里开始？"

后续引导：
- 分析完成后："我发现了3个可改进的地方，需要我详细说明吗？"
- 优化完成后："接下来是否需要优化其他模块？"

当前状态：{state}
用户目标：{goal}
"""
```

---

## 六、检查清单

使用以下清单检查提示词质量：

### 基础检查

- [ ] 是否使用正面表述？
- [ ] 是否删除了冗余内容？
- [ ] 是否明确指定了输出格式？
- [ ] 是否使用了变量/占位符？
- [ ] 是否提供了示例（如适用）？

### 高级检查

- [ ] Temperature 设置是否合理？
- [ ] 是否考虑了 Token 长度？
- [ ] Few-shot 示例是否混合了不同类别？
- [ ] CoT 任务是否设置了 temperature=0？
- [ ] 是否记录了版本和测试结果？

---

## 七、参考资源

**官方文档**
- [Google - Introduction to LLMs](https://cloud.google.com/ai-platform/training/docs/introduction-llms)
- [Google - Prompt Engineering Best Practices](https://cloud.google.com/ai-platform/prediction/docs/ai-platform-prompt-engineering)

**相关资源**
- [OpenAI Prompt Engineering Guide](https://platform.openai.com/docs/guides/prompt-engineering)
- [Anthropic Prompt Library](https://docs.anthropic.com/claude/prompt-library)

**本项目相关**
- [提示词系统优化](../提示词系统优化.md)
- [上下文恢复机制设计](../上下文恢复机制设计.md)
- [模块分析工具总结](../模块分析工具_总结_分析文档.md)
