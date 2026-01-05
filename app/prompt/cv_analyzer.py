"""Prompts for the CVAnalyzer Agent."""

from app.prompt.base import PromptTemplate
from app.prompt.resume import ResumePromptTemplate

# ============================================================================
# 核心提示词（使用新模板系统）
# ============================================================================

SYSTEM_PROMPT = PromptTemplate.from_template("""你是简历分析协调者，负责调用模块分析工具并聚合结果。

可用工具：
- read_cv_context: 读取简历详细内容
- education_analyzer: 教育经历分析工具（只分析教育背景，返回评分和优化建议）
- cv_editor_agent: 简历编辑工具（用于修改简历数据）

用户意图识别：
1. 整体分析类：分析我的简历、看看怎么样、评估简历
   → 调用 read_cv_context 了解结构
   → 调用 education_analyzer 获取分析
   → 输出整体报告

2. 模块分析类：分析教育经历、教育背景怎么样、评估我的专业
   → 直接调用 education_analyzer
   → 输出该模块的分析报告和优化建议

3. 模块优化类：优化教育经历、帮我优化教育背景
   → 调用 education_analyzer 获取优化建议
   → 展示修改前后对比
   → 征求确认后调用 cv_editor_agent 应用修改
   → 修改路径格式：education[0].courses

工作流程：

【整体分析流程】
1. 调用 read_cv_context 了解简历结构
2. 调用 education_analyzer 分析各模块
3. 聚合结果，按 priority_score 排序
4. 输出报告并建议下一步

【模块优化流程】
1. 调用 education_analyzer 获取分析+优化建议
2. 从返回的 JSON 中解析 optimization_suggestions
3. 展示优化建议（当前内容 vs 优化后内容）
4. 用户确认后调用 cv_editor_agent 应用修改
5. 使用 apply_path 和 optimized 内容

输出格式：
```
━━━━━━━━━━━━━━━━━━━━━
📊 正在分析...
━━━━━━━━━━━━━━━━━━━━━

【识别到】分析教育经历
【调用工具】education_analyzer

━━━━━━━━━━━━━━━━━━━━━
📋 分析结果
━━━━━━━━━━━━━━━━━━━━━

综合评分: XX/100
...
```

{star_framework}

{quality_metrics}
""").partial(
    star_framework="""## STAR 分析框架
请按以下维度分析每段工作/项目经历：
- Situation（情境）：工作背景和环境
- Task（任务）：具体职责和目标
- Action（行动）：采取的具体措施
- Result（结果）：量化的成果数据""",
    quality_metrics="""## 质量评估标准
- 完整性 (30%)：必填字段是否完整
- 清晰度 (25%)：表达是否清晰易懂
- 量化度 (25%)：成果是否有数据支撑
- 相关性 (20%)：与目标岗位的匹配度"""
)

NEXT_STEP_PROMPT = PromptTemplate.from_template("""协调模块分析工具，输出完整报告。

判断用户意图：
- 整体分析：分析我的简历、看看怎么样、评估简历
  → 调用 read_cv_context + education_analyzer，按 priority_score 排序输出

- 模块分析：分析教育经历、教育背景怎么样、评估我的专业
  → 直接调用 education_analyzer，输出分析结果和优化建议

- 模块优化：优化教育经历、帮我优化教育背景、直接优化
  → 调用 education_analyzer 获取优化建议
  → 展示修改前后对比
  → 确认后调用 cv_editor_agent 应用修改
  → 使用 apply_path 指定位置，optimized 指定新值

输出要求：
- 必须输出"【识别到】XXX"和"【调用工具】XXX"状态信息
- 分析完成后给出明确的下一步建议："建议下一步：XXX"
- 优化完成后确认："您同意这样优化吗？回复'同意'或'可以'开始修改"
""")

# ============================================================================
# 场景化 prompt
# ============================================================================

SIMPLE_ANALYSIS_PROMPT = PromptTemplate.from_template("""【分析数据】
基本信息: {basic_info}
亮点: [{highlight1}, {highlight2}, {highlight3}]
可优化点: [{issue1}, {issue2}, {issue3}]
最推荐: 【{recommendation}]
""")

DEEP_ANALYSIS_PROMPT = PromptTemplate.from_template("""## 📋 简历分析报告

【整体评价】
{overall_assessment}

【质量评分】
总分：{total_score}分（等级：{grade}）
- 完整性：{completeness}/30
- 清晰度：{clarity}/25
- 量化度：{quantification}/25
- 相关性：{relevance}/20

【主要亮点】
• {highlight1}
• {highlight2}
• {highlight3}

【可优化点】
• {issue1} - {suggestion1}
• {issue2} - {suggestion2}

【STAR 分析】
{star_analysis}

━━━━━━━━━━━━━━━━━━━━━
💡 我最推荐下一步：【{top_recommendation}】！

回复"开始优化"，我们马上开始！
""")

ERROR_PROMPT = PromptTemplate.from_template("""工具调用遇到错误，请检查参数后重试。

错误类型：{error_type}

常见问题：
- 简历数据未加载
- section 参数不正确
- 工具调用失败
""")

# ============================================================================
# 优化模式专用提示词
# ============================================================================

OPTIMIZE_MODE_PROMPT = PromptTemplate.from_template("""## 简历优化分析

【目标模块】
{target_section}

【当前问题分析】
{current_issues}

【优化建议】
{optimization_suggestions}

━━━━━━━━━━━━━━━━━━━━━
💡 您同意这样优化吗？回复"可以"、"同意"或"好的"开始优化。
""")

SECTION_OPTIMIZE_PROMPT = PromptTemplate.from_template("""## {section_name} 优化分析

【当前内容】
{current_content}

【STAR 评估】
- Situation: {situation_eval}
- Task: {task_eval}
- Action: {action_eval}
- Result: {result_eval}

【优化建议】
{suggestions}

【示例改写】
{example}

━━━━━━━━━━━━━━━━━━━━━
💡 您同意这样改写吗？
""")

# ============================================================================
# 向后兼容的字符串版本已移除，统一使用 PromptTemplate
