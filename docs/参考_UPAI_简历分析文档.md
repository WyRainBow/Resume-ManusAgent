# 参考 UPAI 简历分析文档

## 参考对话分析

### 用户输入
```
介绍一下我目前的简历
```

### AI 回复结构

#### 1. 开场白
- "好的，没问题！"
- "为了更好地了解您的简历，我需要先读取一下您的简历内容。"
- 主动调用工具读取简历

#### 2. 简历亮点总结
AI 读取简历后，首先总结**做得好的地方**：
- "有大厂实习经历和项目经验"
- "有数学建模和人工智能比赛的奖项"

#### 3. 指出需要优化的地方（结构化分析）
AI 以 HR 的视角，**逐个模块**指出问题：

| 模块 | 问题 | 具体描述 |
|------|------|----------|
| 个人总结 Summary | 内容是空的/占位符 | HR无法快速了解核心优势和求职意向 |
| 工作经历 Experience | summary部分是空的 | 没有具体描述做了什么、取得了什么成果 |
| 技能 Skills | "熟悉"、"了解"不够具体 | HR很难判断实际熟练程度；keywords可更精炼 |
| 项目经历 Projects | 描述详细但有冗余 | 腾讯云项目写得很好，但"语鲸"项目太长 |

#### 4. 给出结构化的优化流程
AI 提出 **4 步优化计划**：
```
1. 内容强化：补充个人总结和工作经历
2. 信息核验：检查细节，确保没有遗漏
3. 视觉美化：调整排版和样式
4. 完成交付：导出完美简历
```

#### 5. 引导用户行动
- "您看我们先从哪个部分开始优化呢？"
- "我建议我们先从个人总结开始"

---

## 我们当前系统 vs 目标系统

### 当前系统（OpenManus）

| 功能 | 状态 | 说明 |
|------|------|------|
| 加载简历模板 | ✅ | LoadResumeData 工具 |
| 读取简历内容 | ✅ | CVReaderAgentTool |
| 编辑简历字段 | ✅ | CVEditorAgentTool |
| 查看简历结构 | ✅ | GetResumeStructure |
| **主动分析简历** | ❌ | 缺少 |
| **指出优化点** | ❌ | 缺少 |
| **结构化建议** | ❌ | 缺少 |
| **引导优化流程** | ❌ | 缺少 |

### 需要补充的功能

#### 1. 简历分析功能 (AnalyzeResume)
- 输入：简历数据
- 输出：结构化的分析报告
  - 亮点总结
  - 问题点分析（按模块分类）
  - 优化建议

#### 2. CVReader 增强模式
当用户问"介绍一下我的简历"时，CVReader 应该：
1. 读取简历内容
2. 分析简历优缺点
3. 输出结构化建议

#### 3. 优化流程引导
- 步骤1：内容强化 → 引导用户补充缺失信息
- 步骤2：信息核验 → 确认信息准确性
- 步骤3：视觉美化 → 建议排版调整
- 步骤4：完成交付 → 导出/预览

---

## 数据结构设计

### 简历分析报告结构

```json
{
  "highlights": [
    "有大厂实习经历（腾讯云、深言科技、美的集团）",
    "有数学建模和人工智能比赛奖项",
    "项目经历描述详细，有量化数据"
  ],
  "issues": [
    {
      "section": "basic",
      "field": "summary",
      "problem": "个人总结为空",
      "severity": "high",
      "suggestion": "添加2-3句话的总结，突出核心优势和求职意向"
    },
    {
      "section": "experience",
      "field": "summary",
      "problem": "工作经历描述不完整",
      "severity": "high",
      "suggestion": "补充每个工作的主要职责和成果"
    }
  ],
  "optimization_plan": [
    {
      "step": 1,
      "title": "内容强化",
      "actions": ["补充个人总结", "完善工作经历描述", "细化技能说明"]
    },
    {
      "step": 2,
      "title": "信息核验",
      "actions": ["检查联系方式", "确认时间线准确", "核实技能熟练度"]
    },
    {
      "step": 3,
      "title": "视觉美化",
      "actions": ["优化排版", "调整字体", "统一格式"]
    },
    {
      "step": 4,
      "title": "完成交付",
      "actions": ["预览简历", "导出PDF", "检查格式"]
    }
  ]
}
```

---

## 实现方案

### 方案 A：增强 CVReader Agent

修改 `CVReader` 的 `system_prompt`，让它：
1. 当用户问"介绍简历"时，主动分析优缺点
2. 输出结构化的建议

**优点**：改动小，复用现有代码
**缺点**：提示词可能不够稳定

### 方案 B：新增 AnalyzeResume 工具

创建专门的 `AnalyzeResumeTool`：
- 调用 LLM 进行深度分析
- 返回结构化的分析报告
- 前端以漂亮的卡片展示

**优点**：功能独立，易于维护
**缺点**：新增代码较多

### 方案 C：混合方案

1. 增强提示词，让 CVReader 在"介绍"场景下主动分析
2. 前端识别分析类型的内容，用特殊卡片展示

**优点**：平衡
**缺点**：需要前后端配合

---

## 前端展示设计

### 分析报告卡片

```jsx
<div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-200 rounded-xl p-6">
  <h3 className="text-lg font-bold text-blue-800 mb-4">📊 简历分析报告</h3>

  {/* 亮点 */}
  <div className="mb-4">
    <h4 className="font-semibold text-green-700 mb-2">✨ 亮点</h4>
    <ul className="list-disc list-inside text-sm text-gray-700">
      <li>有大厂实习经历（腾讯云、深言科技、美的集团）</li>
      <li>有数学建模和人工智能比赛奖项</li>
    </ul>
  </div>

  {/* 需要优化 */}
  <div className="mb-4">
    <h4 className="font-semibold text-orange-700 mb-2">🔧 需要优化</h4>
    <div className="space-y-2">
      <div className="bg-white rounded-lg p-3">
        <div className="flex items-center gap-2 mb-1">
          <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded">高优先级</span>
          <span className="font-medium text-sm">个人总结</span>
        </div>
        <p className="text-xs text-gray-600">内容为空，需要添加2-3句话突出核心优势</p>
      </div>
    </div>
  </div>

  {/* 优化流程 */}
  <div>
    <h4 className="font-semibold text-blue-700 mb-2">📋 优化流程</h4>
    <div className="flex gap-2">
      <div className="flex-1 bg-white rounded-lg p-3 text-center">
        <div className="text-2xl mb-1">1</div>
        <div className="text-xs font-medium">内容强化</div>
      </div>
      <div className="flex-1 bg-white rounded-lg p-3 text-center">
        <div className="text-2xl mb-1">2</div>
        <div className="text-xs font-medium">信息核验</div>
      </div>
      <div className="flex-1 bg-white rounded-lg p-3 text-center">
        <div className="text-2xl mb-1">3</div>
        <div className="text-xs font-medium">视觉美化</div>
      </div>
      <div className="flex-1 bg-white rounded-lg p-3 text-center">
        <div className="text-2xl mb-1">4</div>
        <div className="text-xs font-medium">完成交付</div>
      </div>
    </div>
  </div>
</div>
```

---

## 待确认问题

1. **分析触发时机**
   - 用户明确说"分析我的简历"？
   - 用户说"介绍一下我的简历"时自动触发分析？
   - 还是两者都触发？

2. **分析深度**
   - 只做模块级别的检查（是否为空）？
   - 还是做内容级别的分析（描述是否详细、是否有量化成果）？

3. **输出格式**
   - 纯文本格式？
   - 结构化 JSON 给前端渲染？
   - 还是 Markdown 格式？

4. **与现有工具的关系**
   - 分析功能是否作为独立工具？
   - 还是集成到 CVReaderAgentTool 中？

---

## 下一步

等待用户确认：
1. 是否需要实现这个分析功能？
2. 采用哪种方案（A/B/C）？
3. 分析的深度和输出格式？

确认后开始编码实现。
思路分析
1. 整体流程

用户: "介绍一下我的简历"
   ↓
Manus: 调用 CVReaderAgentTool
   ↓
CVReader: 读取简历 → 总结亮点 → **询问是否需要深入分析**
   ↓
用户: "好的，帮我分析一下"
   ↓
Manus: 调用新的分析 Agent
   ↓
新Agent: STAR法则分析 → 给出优化建议
2. 两阶段设计
阶段 1：快速介绍（CVReader）
读取简历内容
总结亮点（大厂经历、奖项等）
询问是否需要深入分析
阶段 2：深入分析（新 Agent）
用 STAR 法则分析经历
指出具体问题
给出优化建议
3. 新 Agent 命名建议
候选名称	说明
CVAnalyzer	简历分析 Agent
ResumeCoach	简历教练 Agent
CareerAdvisor	职业顾问 Agent
CVReviewer	简历评审 Agent
4. STAR 法则分析内容
对每个工作经历/项目经历，分析：
Situation: 背景/环境
Task: 任务/目标
Action: 行动/做了什么
Result: 结果/成果（量化数据）
5. 我的理解和补充
关于 CVReader 的修改
当前 CVReader 是被动回答问题，需要改成：
先总结亮点
然后主动询问："需要我为您深入分析简历，找出需要优化的地方吗？"
关于新 Agent 的职责

CVAnalyzer (新 Agent) 职责：
├── 检查简历完整性（哪些字段为空）
├── STAR 法则分析每个经历
│   ├── Situation 是否清晰
│   ├── Task 是否明确
│   ├── Action 是否具体
│   └── Result 是否量化
├── 检查技能描述（是否过于笼统）
├── 检查项目描述（是否过于冗长/简短）
└── 输出结构化建议
交互流程示例

用户: 介绍一下我的简历

AI: 我已经阅读了您的简历，整体来看非常不错！

✨ 主要亮点：
• 有腾讯云、深言科技等大厂实习经历
• 有数学建模和人工智能比赛奖项
• 项目经历丰富，技术栈全面

━━━━━━━━━━━━━━━━━━━━━

🤔 需要我为您深入分析简历，找出需要优化的地方吗？

---

用户: 好的，帮我分析一下

AI: 正在使用专业方法为您分析简历...

[调用 CVAnalyzer Agent]

📊 简历分析报告

🔴 高优先级问题：
• 个人总结为空 - 需要添加2-3句话突出核心优势
• 工作经历描述缺少 STAR 结构 - 建议补充具体行动和成果

🟡 中优先级问题：
• 技能描述过于笼统 - "熟悉"、"了解"不够具体
• 项目描述可以更精炼 - 突出核心技术亮点

💡 优化建议：
1. 添加个人总结，突出求职意向
2. 用 STAR 法则重写工作经历
...

━━━━━━━━━━━━━━━━━━━━━

我们可以按照以下流程优化：
① 内容强化 → ② 信息核验 → ③ 视觉美化 → ④ 完成交付

从哪里开始呢？
待确认的问题
新 Agent 的名字：你更喜欢哪个？
CVAnalyzer
ResumeCoach
CVReviewer
其他
分析深度：
只检查完整性（是否为空）？
还是深入分析内容质量（STAR 法则）？
输出格式：
结构化 JSON 让前端渲染成卡片？
还是 Markdown 文本格式？
触发方式：
用户说"介绍"时只做快速总结 + 询问
用户说"分析"时才调用深度分析
你确认一下这些点，我再开始实现。

---

## ✅ 最终确认需求（2025-01-01）

### 1. Agent 命名
**确定为：`CVAnalyzer`**

### 2. 职责划分

#### CVReader（快速介绍 + 完整性检查）
当用户说"介绍"、"介绍一下我的简历"时：
- 快速总结简历亮点（大厂经历、奖项、核心技能）
- 检查完整性（哪些模块/字段为空）
- 提示用户缺少的内容
- **询问是否需要深入分析**

示例输出：
```
✨ 主要亮点：
• 有腾讯云、深言科技等大厂实习经历
• 有数学建模和人工智能比赛奖项
• 项目经历丰富，技术栈全面

⚠️ 缺少内容：
• 个人总结为空
• 工作经历描述不完整

━━━━━━━━━━━━━━━━━━━━━
🤔 需要我为您深入分析简历，找出需要优化的地方吗？
```

#### CVAnalyzer（深度分析 + STAR 法则）
当用户说"分析"、"帮我分析一下"时：
- **完整性检查**：哪些字段为空
- **内容质量分析（STAR 法则）**：
  - Situation: 背景/环境是否清晰
  - Task: 任务/目标是否明确
  - Action: 行动/做了什么是否具体
  - Result: 结果/成果是否量化
- 检查技能描述（是否过于笼统，如"熟悉"、"了解"）
- 检查项目描述（是否过于冗长/简短）
- 输出结构化建议

### 3. 分析深度
**两种都要**：
1. 完整性检查（是否为空）- CVReader 做
2. 深入分析内容质量（STAR 法则）- CVAnalyzer 做

### 4. 输出格式
**两种格式都支持**：
- **JSON 格式**：用于前端渲染成漂亮的卡片
- **Markdown 格式**：用于直接文本展示

### 5. 触发方式
| 用户输入 | 响应 |
|---------|------|
| "介绍"、"介绍一下我的简历" | CVReader：快速总结 + 完整性检查 + 询问 |
| "分析"、"帮我分析一下" | CVAnalyzer：深度分析 + STAR 法则 |

### 6. 交互流程示例

```
用户: 介绍一下我的简历

AI: 我已经阅读了您的简历，整体来看非常不错！

✨ 主要亮点：
• 有腾讯云、深言科技等大厂实习经历
• 有数学建模和人工智能比赛奖项
• 项目经历丰富，技术栈全面

⚠️ 缺少内容：
• 个人总结为空
• 工作经历描述不完整

━━━━━━━━━━━━━━━━━━━━━
🤔 需要我为您深入分析简历，找出需要优化的地方吗？

---

用户: 好的，帮我分析一下

AI: 正在使用专业方法为您分析简历...

📊 简历分析报告

🔴 高优先级问题：
• 个人总结为空 - 需要添加2-3句话突出核心优势
• 工作经历描述缺少 STAR 结构 - 建议补充具体行动和成果

🟡 中优先级问题：
• 技能描述过于笼统 - "熟悉"、"了解"不够具体
• 项目描述可以更精炼 - 突出核心技术亮点

💡 优化建议：
1. 添加个人总结，突出求职意向
2. 用 STAR 法则重写工作经历
...

━━━━━━━━━━━━━━━━━━━━━
我们可以按照以下流程优化：
① 内容强化 → ② 信息核验 → ③ 视觉美化 → ④ 完成交付
```

### 7. 实现文件结构

```
app/
├── agent/
│   ├── cv_reader.py          # 修改：增强 system_prompt
│   └── cv_analyzer.py        # 新增：深度分析 Agent
├── tool/
│   ├── cv_reader_agent_tool.py       # 修改：调整描述
│   ├── cv_analyzer_agent_tool.py     # 新增：CVAnalyzer 工具包装
│   └── base.py                # 可能需要添加 JSON 输出支持
```

### 8. 数据结构（增强版）

```json
{
  "highlights": [
    "有大厂实习经历（腾讯云、深言科技、美的集团）",
    "有数学建模和人工智能比赛奖项",
    "项目经历描述详细，有量化数据"
  ],
  "completeness": {
    "missing_sections": ["summary"],
    "empty_fields": ["basic.summary", "experience[0].summary"]
  },
  "content_analysis": {
    "experience": [
      {
        "id": "exp-1",
        "company": "腾讯云",
        "star_analysis": {
          "situation": {"status": "missing", "suggestion": "补充项目背景"},
          "task": {"status": "weak", "suggestion": "明确你的职责和目标"},
          "action": {"status": "good", "note": "行动描述具体"},
          "result": {"status": "missing", "suggestion": "添加量化成果"}
        }
      }
    ],
    "skills": [
      {
        "skill": "Python",
        "issue": "描述笼统",
        "suggestion": "改为 '熟练使用 Python 开发，有 X 个项目经验'"
      }
    ]
  },
  "issues": [
    {
      "section": "basic",
      "field": "summary",
      "problem": "个人总结为空",
      "severity": "high",
      "suggestion": "添加2-3句话的总结，突出核心优势和求职意向"
    }
  ],
  "optimization_plan": [
    {"step": 1, "title": "内容强化", "actions": ["补充个人总结", "完善工作经历描述"]},
    {"step": 2, "title": "信息核验", "actions": ["检查联系方式", "确认时间线准确"]},
    {"step": 3, "title": "视觉美化", "actions": ["优化排版", "调整字体"]},
    {"step": 4, "title": "完成交付", "actions": ["预览简历", "导出PDF"]}
  ]
}
```

### 9. 前端展示（JSON 格式时）

前端识别到返回的是分析报告 JSON 时，渲染成卡片：
- 📊 分析报告标题
- ✨ 亮点（绿色）
- ⚠️ 缺少内容（黄色）
- 🔴 高优先级问题（红色）
- 🟡 中优先级问题（黄色）
- 💡 优化建议（蓝色）
- 📋 优化流程步骤（4 步）

---

## 下一步行动

1. 创建 `CVAnalyzer` Agent
2. 创建 `CVAnalyzerAgentTool` 工具包装
3. 修改 `CVReader` 的 system_prompt
4. 实现输出格式转换（JSON + Markdown）
5. 测试完整流程

---

## UPAI 交互式优化对话分析（续）

### 完整的优化引导流程

#### 第一阶段：引导用户选择优化起点

```
AI: 您看我们先从哪个部分开始优化呢？
   我建议我们先从个人总结开始，让HR对您有一个初步的深刻印象。

用户: 可以
```

**关键点**：
- AI 主动提出建议（"我建议..."）
- 给出理由（"让HR对您有一个初步的深刻印象"）
- 用户只需简单确认（"可以"）

#### 第二阶段：收集信息，生成内容

```
AI: 好的，那我们先来优化您的【个人总结】部分。
   为了更好地撰写个人总结，我需要了解几个关键信息：

   1. 您的目标岗位是？
   2. 您最擅长的技术/技能是？（请列举2-3个核心技能）
   3. 您最满意的成就是？（1-2个亮点）

   请您提供这些信息，我将为您生成一份有针对性的个人总结。

用户: 目标岗位是大模型应用，我最擅长Java和Go，Python方面熟悉AI后端开发等，
      最满意的成就是有腾讯的实际经历，在腾讯里做了很多架构的工作
```

**关键点**：
- AI 主动提出**结构化的问题**
- 问题数量适中（3个）
- 每个问题都有示例，降低用户回答门槛
- 用户可以自由回答，不需要严格按格式

#### 第三阶段：生成草稿，请求确认

```
AI: 好的，根据您提供的信息，您的目标岗位是大模型应用开发，
   擅长Java、Go，熟悉Python AI后端开发，并且在腾讯有架构优化的实际经验。

   我为您草拟了一份个人总结，请您审阅：

   ────────────────────────────────────────
   大模型应用开发工程师，具备扎实的Java与Go语言开发功底，
   熟悉Python AI后端开发，对大模型应用有深入理解与实践经验。
   在腾讯云实习期间，主导并参与多项核心架构优化工作，
   有效提升系统性能与稳定性。具备优秀的系统设计、问题解决
   和团队协作能力，致力于将前沿AI技术应用于实际业务场景，
   推动产品创新与效率提升。
   ────────────────────────────────────────

   您觉得这份总结怎么样？是否需要调整或补充其他内容？

用户: 可以
```

**关键点**：
- AI 先**复述/总结**用户提供的信息，确认理解正确
- 生成完整的草稿内容（不是让用户自己写）
- 明确请求用户确认（"请您审阅"、"是否需要调整"）
- 用户只需简单确认（"可以"）

#### 第四阶段：执行修改，反馈结果

```
AI: 好的，既然您觉得这份个人总结可以，那我就将它更新到您的简历中。

   [调用编辑工具]

   ✅ 个人总结已成功更新！请查看右侧简历预览，确认效果是否符合预期。

   接下来，我们来优化【工作经历】部分。您有三段非常宝贵的实习经历：

   • 腾讯云：高级后端开发实习生 (2025.06 - 2025.10)
   • 深言科技：AI应用开发实习生 (Go/Python) (2025.02 - 2025.06)
   • 美的集团：后端开发实习生 (Java) (2024.12 - 2025.01)

   目前这三段经历的 summary 部分都是空的，这会让HR无法了解您
   在这些实习中具体做了什么、学到了什么以及取得了哪些成果。

   我们先从腾讯云的高级后端开发实习生经历开始优化吧。
   请您详细描述一下，您在腾讯云主要负责哪些工作？具体参与了
   哪些项目？取得了哪些成果？尽量多提供一些量化的数据和具体的细节。
```

**关键点**：
- 执行修改后给出**明确的成功反馈**（✅ + "已成功更新"）
- 引导用户查看预览确认效果
- **立即进入下一个优化点**，保持优化流程的连贯性
- 列出具体内容，让用户有清晰的认知
- 指出当前问题（"summary部分都是空的"）并说明影响
- 主动选择优先级最高的部分（腾讯云）开始优化
- 引导用户提供细节（"量化数据"、"具体细节"）

---

### 交互模式总结

| 阶段 | AI 动作 | 用户动作 | 关键词 |
|------|---------|---------|--------|
| 1. 引导选择 | 建议优化起点 + 理由 | 简单确认 | "我建议..." |
| 2. 收集信息 | 结构化提问 + 示例 | 自由回答 | "我需要了解..." |
| 3. 生成草稿 | 复述确认 + 生成内容 | 确认/调整 | "请您审阅" |
| 4. 执行反馈 | 执行修改 + 成功确认 | 查看预览 | "✅ 已成功更新" |
| 5. 继续引导 | 指出下一问题 + 引导行动 | 提供信息 | "接下来，我们来..." |

### 关键设计原则

#### 1. AI 主导流程
- AI 不是被动等待指令，而是**主动引导**整个优化流程
- 每一步都有明确的目标和下一步计划

#### 2. 降低用户负担
- 用户只需回答简单问题，不需要自己写内容
- AI 负责生成、修改、优化具体文字

#### 3. 保持反馈闭环
- 每次修改都有明确的成功反馈
- 引导用户查看预览确认效果

#### 4. 连贯的优化流程
- 完成一个优化后立即进入下一个
- 按优先级顺序（个人总结 → 工作经历 → ...）

#### 5. 复述确认机制
- 生成内容前先复述用户信息，确保理解正确

---

### 对我们系统的启发

#### CVAnalyzer 需要增加的能力

**1. 交互式优化引导**

```python
class CVAnalyzer(ToolCallAgent):
    # 新增：优化引导模式

    def suggest_next_step(self, resume_data: Dict) -> str:
        """分析当前状态，建议下一步优化重点"""
        issues = self.analyze_resume(resume_data)

        # 优先级排序
        if issues.get("completeness", {}).get("empty_fields"):
            return "个人总结"

        if any(exp.get("star_analysis", {}).get("result", {}).get("status") == "missing"
               for exp in issues.get("content_analysis", {}).get("experience", [])):
            return "工作经历"

        return "技能描述"

    def generate_summary(self, resume_data: Dict, user_input: Dict) -> str:
        """根据用户提供的信息生成个人总结"""
        target_position = user_input.get("target_position")
        core_skills = user_input.get("core_skills")
        proud_achievement = user_input.get("proud_achievement")

        # 调用 LLM 生成
        prompt = f"""
        请为求职者生成个人总结：
        - 目标岗位：{target_position}
        - 核心技能：{core_skills}
        - 最满意的成就：{proud_achievement}

        要求：2-3句话，突出核心优势，吸引HR注意。
        """
        ...
```

**2. 信息收集模式**

```
AI: 为了帮您优化【个人总结】，我需要了解几个信息：

1️⃣ 您的目标岗位是？
   （例如：高级后端开发工程师、大模型应用工程师等）

2️⃣ 您最擅长的技能是？
   （请列举2-3个核心技能）

3️⃣ 您最满意的成就是？
   （1-2个亮点，可以是工作/项目经历中提炼的）

请提供这些信息，我将为您生成有针对性的个人总结。
```

**3. 草稿确认模式**

```
AI: 根据您提供的信息，我为您草拟了一份个人总结：

═══════════════════════════════════════
[生成的总结内容]
═══════════════════════════════════════

您觉得这份总结怎么样？
- 回复 "可以" 或 "好的"，我将更新到简历
- 或者告诉我需要如何调整
```

**4. 成功反馈模式**

```
AI: ✅ 个人总结已成功更新！请查看右侧简历预览。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📋 接下来优化【工作经历】部分

您有以下实习经历：
• 腾讯云：高级后端开发实习生 (2025.06 - 2025.10)
• 深言科技：AI应用开发实习生 (2025.02 - 2025.06)

⚠️ 目前这些经历的描述部分为空，
   HR无法了解您具体做了什么、取得了什么成果。

我们先从腾讯云的经历开始优化吧。
请描述一下：您主要负责哪些工作？参与了哪些项目？
取得了哪些成果？（尽量提供量化数据）
```

---

### 工具设计建议

#### 新增工具：OptimizeResumeSection

```python
class OptimizeResumeSection(BaseTool):
    """简历模块优化工具

    与 CVAnalyzer 配合，实现交互式优化流程
    """

    name = "optimize_resume_section"

    parameters = {
        "type": "object",
        "properties": {
            "section": {
                "type": "string",
                "enum": ["summary", "experience", "skills", "projects"]
            },
            "mode": {
                "type": "string",
                "enum": ["suggest", "collect_info", "generate", "update"],
                "description": "优化阶段：建议/收集信息/生成草稿/更新"
            },
            "user_input": {
                "type": "object",
                "description": "用户提供的信息（collect_info 阶段使用）"
            },
            "generated_content": {
                "type": "string",
                "description": "生成的内容（update 阶段使用）"
            }
        }
    }
```

---

### 状态机设计

```
                    ┌─────────────────┐
                    │   分析完成      │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ 建议优化起点    │ ──→ "我建议先从个人总结开始"
                    └────────┬────────┘
                             │
                             ▼ 用户确认
                    ┌─────────────────┐
                    │  收集信息      │ ──→ "您的目标岗位是？"
                    └────────┬────────┘
                             │
                             ▼ 用户回答
                    ┌─────────────────┐
                    │  生成草稿      │ ──→ "我为您草拟了..."
                    └────────┬────────┘
                             │
                             ▼ 用户确认
                    ┌─────────────────┐
                    │  更新简历      │ ──→ "✅ 已成功更新"
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  建议下一步    │ ──→ "接下来优化工作经历"
                    └─────────────────┘
```

---

### ✅ 最终确认设计决策

#### 1. 优化流程的入口 → **混合模式**

- 用户明确说"开始优化"时启动优化流程
- 分析完成后**可以**询问"需要我帮您优化吗？"但不强制进入

```
用户: 帮我分析一下简历

AI: [分析报告输出]

━━━━━━━━━━━━━━━━━━━━━
🤔 需要我帮您开始优化简历吗？

用户: 好的 / 开始优化

AI: [进入优化流程]
```

#### 2. 信息收集的方式 → **逐个问题提问（UPAI 模式）**

- 一次问一个问题，降低用户认知负担
- 但允许用户一次性回答多个问题

```
AI: 为了帮您优化【个人总结】，我需要了解几个信息：

1️⃣ 您的目标岗位是？
   （例如：高级后端开发工程师、大模型应用工程师等）

用户: 大模型应用工程师

AI: 2️⃣ 您最擅长的技能是？
   （请列举2-3个核心技能）

用户: Java、Go，熟悉Python AI后端开发

AI: 3️⃣ 您最满意的成就是？
   （1-2个亮点）
```

#### 3. 草稿生成的时机 → **用户确认后再生成**

```
AI: 根据您提供的信息：
- 目标岗位：大模型应用工程师
- 核心技能：Java、Go、Python
- 成就：腾讯架构优化经验

我将为您生成个人总结，确认吗？

用户: 确认

AI: [生成草稿]
```

#### 4. 与 CVEditor 的关系 → **Manus 调用 CVEditor（推荐）**

**设计原则：CVOptimizer 只管建议，不直接修改数据**

```
❌ 不推荐：CVOptimizer 调用 CVEditor
用户 → Manus → CVOptimizerAgentTool → CVOptimizer → CVEditorAgentTool → CVEditor
                     └─────────────────────────────────────────┘
                           工具套工具，链路太长

✅ 推荐：Manus 直接调用 CVEditor
用户 → Manus → CVOptimizerAgentTool → CVOptimizer（只建议）
                    ↓                    ↓
              CVEditorAgentTool ←──── Manus 决定后调用
                    ↓
              CVEditor
```

**两种方案对比：**

| 对比项 | CVOptimizer 调用 | Manus 调用 |
|-------|-----------------|------------|
| 职责清晰度 | ❌ 又引导又修改 | ✅ 只管引导和建议 |
| 工具链路 | ❌ 工具套工具 | ✅ Manus 作为协调者 |
| 灵活性 | ❌ 用户想跳过较复杂 | ✅ 用户可随时打断 |
| 状态管理 | ❌ 两个 Agent 维护状态 | ✅ Manus 统一管理 |

---

### Agent 架构设计（更新版）

#### 1. CVOptimizer Agent（新增）

```
CVOptimizer Agent - 简历优化建议助手

职责：
- 引导用户选择优化起点
- 收集用户信息（逐个提问）
- 生成优化建议/草稿
- **只负责建议，不直接修改数据**

工具：
- ReadCVContext（读取简历）
- CreateChatCompletion（生成内容）
- Terminate（结束）

注意：不包含 CVEditorAgentTool
```

#### 2. Agent 交互关系（更新）

```
用户输入
    ↓
┌─────────────┐
│   Manus     │ ←── 协调者，根据用户反馈决定是否执行修改
└──────┬──────┘
       │
       ├──→ "介绍/查看简历" ──→ CVReaderAgentTool ──→ CVReader Agent
       │
       ├──→ "分析简历" ──→ CVAnalyzerAgentTool ──→ CVAnalyzer Agent
       │
       ├──→ "开始优化" ──→ CVOptimizerAgentTool ──→ CVOptimizer Agent
       │                                                  │
       │                                                  └──→ 只生成建议/草稿
       │
       └──→ 用户确认后 ──→ CVEditorAgentTool ──→ CVEditor Agent
                              │
                              └──→ 执行实际修改
```

#### 3. 完整交互流程示例

```
用户: 开始优化

Manus: [调用 CVOptimizerAgentTool]

CVOptimizer: 我建议先从【个人总结】开始优化，让HR对您有深刻印象。
           可以吗？

用户: 可以

CVOptimizer: 1️⃣ 您的目标岗位是？

用户: 大模型应用工程师

CVOptimizer: 2️⃣ 您最擅长的技能是？

用户: Java、Go、Python

CVOptimizer: 3️⃣ 您最满意的成就是？

用户: 腾讯架构优化经验

CVOptimizer: 根据您提供的信息，我为您草拟了一份个人总结：
           ═══════════════════════
           [草稿内容]
           ═══════════════════════
           您觉得这份总结怎么样？

用户: 可以，更新一下

Manus: [识别到用户确认，调用 CVEditorAgentTool]
     path='basic.summary', action='update', value='[草稿内容]'

CVEditor: ✅ 已成功更新 basic.summary

Manus: ✅ 个人总结已成功更新！请查看右侧简历预览。

       CVOptimizer 建议下一步优化【工作经历】，
       需要继续吗？

用户: 需要

[循环继续...]
```

---

### 4. 工具设计（更新）

**CVOptimizerAgentTool**

```python
class CVOptimizerAgentTool(BaseTool):
    """简历优化建议助手工具

    注意：此工具只负责引导和生成建议，不直接修改数据
    实际修改由 Manus 调用 CVEditorAgentTool 完成
    """

    name = "cv_optimizer_agent"

    description = """Guide users through interactive resume optimization process.

Use this tool when the user wants to:
- Start optimizing their resume (开始优化)
- Improve a specific section (优化个人总结/工作经历/技能)
- Get help writing resume content

The CVOptimizer will:
1. Suggest which section to optimize first
2. Collect information through questions (one at a time)
3. Generate optimized content suggestions
4. Wait for user confirmation (Manus will handle the actual update)

此工具用于引导求职者逐步优化简历内容。"""

    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["start", "suggest_next", "collect_info", "generate"],
                "description": "优化动作：start=开始优化, suggest_next=建议下一步, collect_info=收集信息, generate=生成内容"
            },
            "section": {
                "type": "string",
                "description": "要优化的模块（如：个人总结、工作经历）"
            },
            "user_input": {
                "type": "string",
                "description": "用户提供的信息"
            }
        }
    }
```

#### 5. CVOptimizer Agent 实现（更新）

```python
class CVOptimizer(ToolCallAgent):
    """简历优化建议助手 Agent

    引导用户通过交互式流程优化简历
    注意：只负责建议，不直接修改数据
    """

    name = "CVOptimizer"
    description = "An AI assistant that guides users through resume optimization"

    system_prompt = """You are a professional resume optimization coach. You guide users through improving their resumes step by step.

**Your workflow:**

1. **Suggest Starting Point** (when user says "start optimization")
   - Analyze current resume state
   - Suggest the most impactful section to optimize first
   - Explain why this section is important

2. **Collect Information** (one question at a time)
   - Ask structured questions with examples
   - Wait for user response before asking the next
   - Be encouraging and supportive

3. **Generate Content** (after confirmation)
   - Summarize what you learned from the user
   - Ask for confirmation before generating
   - Generate polished, professional content

4. **Important: Do NOT directly modify the resume**
   - Present the generated content to the user
   - Ask if they want to apply it
   - Let Manus handle the actual update via cv_editor_agent

**Output Style:**
- Use emojis for visual clarity (✨📋⚠️✅)
- Keep messages concise and actionable
- Always explain the "why" behind suggestions

**Language:**
Respond in Chinese (Simplified) for Chinese users.
"""

    available_tools = ToolCollection(
        ReadCVContext(),           # 读取简历
        CreateChatCompletion(),    # 生成内容
        Terminate(),               # 结束
        # 注意：不包含 CVEditorAgentTool
    )

    def suggest_next_section(self, resume_data: Dict) -> Dict:
        """建议下一个优化模块"""
        # 检查优先级
        if not resume_data.get("basic", {}).get("summary"):
            return {
                "section": "个人总结",
                "reason": "让HR对您有一个初步的深刻印象",
                "priority": "high"
            }

        experience = resume_data.get("experience", [])
        if experience and not experience[0].get("details"):
            return {
                "section": "工作经历",
                "reason": "HR最关注的部分，需要详细描述",
                "priority": "high"
            }

        return {
            "section": "技能描述",
            "reason": "突出核心竞争力",
            "priority": "medium"
        }

    def get_questions_for_section(self, section: str) -> list:
        """获取指定模块的问题列表"""
        questions = {
            "个人总结": [
                {
                    "key": "target_position",
                    "question": "您的目标岗位是？",
                    "example": "例如：大模型应用工程师、高级后端开发工程师"
                },
                {
                    "key": "core_skills",
                    "question": "您最擅长的技能是？",
                    "example": "请列举2-3个核心技能"
                },
                {
                    "key": "proud_achievement",
                    "question": "您最满意的成就是？",
                    "example": "1-2个亮点，可以是工作/项目经历中提炼的"
                }
            ],
            "工作经历": [
                {
                    "key": "company_role",
                    "question": "您在{company}担任什么职位？",
                    "example": "具体职位名称"
                },
                {
                    "key": "responsibilities",
                    "question": "您主要负责哪些工作？",
                    "example": "具体职责和任务"
                },
                {
                    "key": "achievements",
                    "question": "您取得了哪些成果？",
                    "example": "尽量提供量化数据，如提升性能X%、节省Y小时"
                }
            ]
        }
        return questions.get(section, [])
```

#### 5. 优化流程状态机（更新版）

```
                    ┌─────────────────┐
                    │ 用户说"开始优化" │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ CVOptimizer     │
                    │ 分析简历状态    │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ 建议优化起点    │
                    │ "我建议先从..." │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │    用户确认     │
                    │   "可以/好的"   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  逐个收集信息   │
                    │  Q1 → Q2 → Q3  │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   复述确认      │
                    │ "根据您提供..." │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │   用户确认生成  │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │  生成优化内容   │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ 调用CVEditor    │
                    │ 执行修改        │
                    └────────┬────────┘
                             │
                             ▼
                    ┌─────────────────┐
                    │ ✅ 成功反馈     │
                    │ 建议下一步优化  │
                    └─────────────────┘
```

---

### 实现文件结构（更新）

```
app/
├── agent/
│   ├── cv_reader.py          # 快速介绍
│   ├── cv_analyzer.py        # 深度分析 (STAR)
│   └── cv_optimizer.py       # 交互式优化 (新增)
├── tool/
│   ├── cv_reader_agent_tool.py
│   ├── cv_analyzer_agent_tool.py  # 新增
│   └── cv_optimizer_agent_tool.py # 新增
```


用户: 开始优化

Manus: [调用 CVOptimizerAgentTool]

CVOptimizer: 我建议先从【个人总结】开始优化，让HR对您有深刻印象。
           请问可以吗？

用户: 可以

CVOptimizer: 为了帮您优化【个人总结】，我需要了解几个信息：
           1️⃣ 您的目标岗位是？
           ...

[收集完信息后]

CVOptimizer: 根据您提供的信息，我为您草拟了一份个人总结：
           ═══════════════════════
           [草稿内容]
           ═══════════════════════

           您觉得这份总结怎么样？

用户: 可以，更新一下

Manus: [识别到用户确认，调用 CVEditorAgentTool 执行修改]

CVEditor: ✅ 已成功更新 basic.summary

Manus: ✅ 个人总结已成功更新！请查看右侧简历预览。

       CVOptimizer 建议下一步优化【工作经历】，
       需要继续吗？
