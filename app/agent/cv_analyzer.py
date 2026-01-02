"""
CVAnalyzer Agent - 简历深度分析 Agent

使用 STAR 法则深入分析简历内容质量
"""

import json
import re
from typing import Dict, Optional
from pydantic import Field

from app.agent.toolcall import ToolCallAgent
from app.tool import ToolCollection, Terminate, CreateChatCompletion
from app.tool.cv_reader_tool import ReadCVContext


class CVAnalyzer(ToolCallAgent):
    """简历深度分析 Agent

    使用 STAR 法则深入分析简历内容质量，包括：
    - 完整性检查（哪些字段为空）
    - STAR 法则分析（Situation, Task, Action, Result）
    - 技能描述分析
    - 项目描述分析
    """

    name: str = "CVAnalyzer"
    description: str = "An AI assistant that deeply analyzes CV/Resume content using STAR methodology"

    system_prompt: str = """你是一位专业的简历分析师，使用 STAR 法则深入分析简历质量。

【绝对重要 - 永远使用第一人称，绝对不要使用第三人称】

你是在和用户谈论他们自己的简历。

【禁止使用的词 - 绝对不要使用】
- ❌ 候选人
- ❌ 求职者
- ❌ 该用户
- ❌ 候选人的信息
- ❌ 查看候选人的简历
- ❌ 这位候选人

【必须使用的词 - 永远使用】
- ✅ 您 / 你
- ✅ 您的 / 你的
- ✅ 这份简历
- ✅ 您的信息

【工作流程 - 根据问题类型决定分析深度】

**当用户要求"简单分析简历亮点"或"简单介绍一下简历"时：**
1. **只调用一次 read_cv_context 工具**获取完整简历数据
2. **输出简洁的亮点分析**（2-3个主要亮点，1-2句话总结）
3. **必须询问是否需要深入分析**：
   "🤔 需要我为您深入分析简历，找出需要优化的地方吗？回复'帮我分析'或'开始优化'，我们就开始！"
4. 调用 terminate 工具结束

**当用户要求"深入分析"或"帮我分析"时：**

1. **只调用一次 read_cv_context 工具**获取完整简历数据
2. **立即输出完整的分析报告**（不要分步，不要重复调用工具）
3. 调用 terminate 工具结束

【输出格式 - 根据问题类型决定】

**当问题是"简单分析简历亮点"时：**
⚠️⚠️⚠️ 输出简洁的结构化分析数据（让 Manus 来组织最终输出）：

```
【分析数据】
基本信息: {姓名、学校、专业、求职意向}
亮点: [{亮点1}, {亮点2}, {亮点3}]
可优化点: [{问题1}, {问题2}, {问题3}]
最推荐: 【{单一推荐项}】
```
说明：只输出结构化数据，不要输出完整的报告文本。Manus 会用这些数据生成最终的总结。

**当问题是"深度分析简历"时：**
⚠️⚠️⚠️ 必须一次性输出完整的分析报告，严格按照以下结构：

```
好的，我已经读取了您的简历内容。整体来看，您的简历信息比较丰富，特别是腾讯云的实习经历描述非常详细，量化数据和技术细节都体现得很好，这是非常大的亮点！

不过，我也发现了一些可以进一步优化的地方，让您的简历更具竞争力：

个人总结：目前写得不错，但可以更突出您作为"大模型应用开发/后端开发工程师"的核心优势和未来方向，与目标岗位匹配度更高。

工作经历：
• 深言科技：经历描述为空，这会让人觉得信息不完整。即使是短期实习，也建议补充一些核心职责或学到的技能。
• 腾讯云：经历虽然很详细，但可以考虑将其中的项目内容独立出来，放在"项目经历"模块，这样结构会更清晰。

项目经历：
• 腾讯云域名注册业务：描述非常详细，量化数据和技术细节都体现得很好。
• 语鲸 DeepResearch：描述略显冗长，可以提炼核心成果和您的贡献，并补充量化数据。

技能：技能描述比较笼统，例如"熟悉Java编程语言，Golang编程语言等原理"。建议具体说明您在这些技术上的熟练程度（精通、熟练、了解）以及实际应用经验。

荣誉奖项：全国大学生数学建模省一等奖和人工智能比赛省二等奖很有含金量，建议补充获奖时间。

教育经历：建议补充与目标岗位相关的核心课程、GPA（如果优秀）或在校期间参与的社团活动。

总的来说，您的简历基础很好，特别是腾讯云的实习经历是加分项。如果能把其他部分也填充完整并优化，会更有冲击力！

━━━━━━━━━━━━━━━━━━━━━
💡 我最推荐下一步：【{单一推荐项}】！

直接回复"开始优化"，我们马上开始！
```

⚠️ 格式要求：
- 所有文本在一行内，不要随意换行
- 如果需要强调，使用正常文本，不要用 Markdown 符号
- 保持简洁自然

❌ 绝对禁止：
- 使用"候选人"、"求职者"等第三人称
- 分步输出（要一次性输出完整报告）

✅ 必须做到：
- 简单分析时：输出结构化数据（基本信息、亮点、可优化点、最推荐），让 Manus 来组织最终输出
- 深度分析时：输出完整报告，列出所有问题，但最后只给1个最重要的优化建议
- 使用"您"而不是"候选人"

【重要提醒】
- ✅ 调用 read_cv_context 一次后，立即输出完整报告
- ❌ 不要说"让我查看"、"我来分析"这类过渡语
- ❌ 不要分步输出，要一次性输出完整报告
- ❌ 不要重复调用工具
"""

    next_step_prompt: str = """根据用户的问题类型，决定分析深度：

1. 如果问题是"简单分析简历亮点"或"简单介绍一下简历"：
   - 调用 read_cv_context 工具获取简历数据
   - 输出简洁的亮点分析（2-3个主要亮点，每个亮点1-2句话）
   - **必须询问是否需要深入分析**，格式如下：
     "🤔 需要我为您深入分析简历，找出需要优化的地方吗？回复'帮我分析'或'开始优化'，我们就开始！"
   - 调用 terminate 工具结束

2. 如果问题是"深度分析简历"或"帮我分析一下简历"：
   - 调用 read_cv_context 工具获取简历数据
   - 立即输出完整报告（一次性输出，不要分步）
   - 调用 terminate 工具结束

⚠️ 重要：
- 只调用一次 read_cv_context 工具
- 根据问题类型决定输出格式
- 简单分析时，必须询问是否需要深入分析
- 不要说"让我查看"、"我来分析"这类过渡语
"""

    available_tools: ToolCollection = Field(
        default_factory=lambda: ToolCollection(
            ReadCVContext(),
            Terminate(),  # 只保留读取和终止工具，强制直接输出分析
        )
    )

    special_tool_names: list[str] = Field(default_factory=lambda: [Terminate().name])

    max_steps: int = 10

    # 当前加载的简历数据
    _resume_data: Optional[Dict] = None
    _cv_tool: Optional[ReadCVContext] = None

    class Config:
        arbitrary_types_allowed = True

    def load_resume(self, resume_data: Dict) -> str:
        """加载简历数据到 Agent

        Args:
            resume_data: 简历数据字典，格式参考 ResumeData

        Returns:
            简历摘要文本
        """
        self._resume_data = resume_data

        # 获取 ReadCVContext 工具并设置简历数据
        for tool in self.available_tools.tools:
            if isinstance(tool, ReadCVContext):
                tool.set_resume_data(resume_data)
                self._cv_tool = tool
                break

        # 将简历基本信息添加到上下文
        basic = resume_data.get("basic", {})
        context = f"""Current Resume Loaded:

Name: {basic.get('name', 'N/A')}
Target Position: {basic.get('title', 'N/A')}

Use the read_cv_context tool to get detailed information for STAR analysis.
"""
        from app.schema import Message
        self.memory.add_message(Message.system_message(context))
        return context

    async def chat(self, message: str, resume_data: Optional[Dict] = None) -> str:
        """与简历对话

        Args:
            message: 用户消息
            resume_data: 简历数据（如果未加载过）

        Returns:
            AI 回复
        """
        if resume_data:
            self.load_resume(resume_data)
        elif not self._resume_data:
            return "No resume data loaded. Please load a resume first."

        # 添加用户消息
        self.update_memory("user", message)

        # 运行 Agent
        result = await self.run()

        return result

    def _check_completeness(self, resume_data: Dict) -> Dict:
        """检查简历完整性

        Returns:
            {
                "missing_sections": [],
                "empty_fields": []
            }
        """
        missing_sections = []
        empty_fields = []

        basic = resume_data.get("basic", {})
        menu_sections = resume_data.get("menuSections", [])

        # 检查个人总结
        summary = basic.get("summary", "")
        if not summary or summary.strip() == "":
            empty_fields.append("basic.summary")

        # 检查各模块
        for section in menu_sections:
            section_id = section.get("id")
            enabled = section.get("enabled", True)

            if not enabled:
                continue

            if section_id == "experience":
                experience = resume_data.get("experience", [])
                if not experience:
                    missing_sections.append("工作经历")
                else:
                    for i, exp in enumerate(experience):
                        if not exp.get("details") or not exp.get("details").strip():
                            empty_fields.append(f"experience[{i}].details")

            elif section_id == "projects":
                projects = resume_data.get("projects", [])
                if not projects:
                    missing_sections.append("项目经历")
                else:
                    for i, proj in enumerate(projects):
                        if not proj.get("description") or not proj.get("description").strip():
                            empty_fields.append(f"projects[{i}].description")

            elif section_id == "skills":
                skill_content = resume_data.get("skillContent", "")
                if not skill_content or not skill_content.strip():
                    empty_fields.append("skillContent")

            elif section_id == "education":
                education = resume_data.get("education", [])
                if not education:
                    missing_sections.append("教育经历")

            elif section_id == "awards":
                awards = resume_data.get("awards", [])
                if not awards:
                    # 奖项不是必需的，但如果没有可以建议添加
                    pass

        return {
            "missing_sections": missing_sections,
            "empty_fields": empty_fields
        }

    def _analyze_star_for_experience(self, experience: Dict, index: int) -> Dict:
        """使用 STAR 法则分析工作经历"""
        details = experience.get("details", "")
        company = experience.get("company", "公司名")
        position = experience.get("position", "职位")

        # 分析内容
        star_analysis = {
            "situation": {"status": "missing", "suggestion": "补充工作背景和环境描述"},
            "task": {"status": "missing", "suggestion": "明确你的职责和目标"},
            "action": {"status": "missing", "suggestion": "描述具体采取了什么行动"},
            "result": {"status": "missing", "suggestion": "添加量化的成果数据"}
        }

        if details:
            # 检查是否有数字/量化结果
            has_numbers = bool(re.search(r'\d+', details))

            # 检查关键词
            situation_keywords = ["负责", "参与", "在", "期间", "背景", "环境"]
            task_keywords = ["目标", "职责", "任务", "负责"]
            action_keywords = ["开发", "实现", "设计", "优化", "完成", "搭建", "构建"]
            result_keywords = ["提升", "降低", "节省", "获得", "达到", "成功", "%"]

            details_lower = details.lower()

            # 简单的判断逻辑
            if any(kw in details for kw in situation_keywords):
                star_analysis["situation"]["status"] = "weak"
            if any(kw in details for kw in task_keywords):
                star_analysis["task"]["status"] = "weak"
            if any(kw in details for kw in action_keywords):
                star_analysis["action"]["status"] = "good"
                star_analysis["action"]["note"] = "有具体行动描述"
            if any(kw in details for kw in result_keywords) or has_numbers:
                star_analysis["result"]["status"] = "good"
                star_analysis["result"]["note"] = "有成果描述"

        return {
            "id": f"exp-{index}",
            "company": company,
            "position": position,
            "star_analysis": star_analysis
        }

    def _analyze_star_for_project(self, project: Dict, index: int) -> Dict:
        """使用 STAR 法则分析项目经历"""
        description = project.get("description", "")
        name = project.get("name", "项目名")

        star_analysis = {
            "situation": {"status": "missing", "suggestion": "补充项目背景"},
            "task": {"status": "missing", "suggestion": "明确项目目标和你的角色"},
            "action": {"status": "missing", "suggestion": "描述具体技术实现"},
            "result": {"status": "missing", "suggestion": "添加项目成果和影响"}
        }

        if description:
            has_numbers = bool(re.search(r'\d+', description))

            action_keywords = ["使用", "采用", "开发", "实现", "设计", "基于", "运用"]
            result_keywords = ["成功", "完成", "上线", "部署", "用户", "访问", "性能"]

            if "项目" in description or "背景" in description:
                star_analysis["situation"]["status"] = "weak"
            if any(kw in description for kw in action_keywords):
                star_analysis["action"]["status"] = "good"
                star_analysis["action"]["note"] = "有技术实现描述"
            if (any(kw in description for kw in result_keywords) or has_numbers):
                star_analysis["result"]["status"] = "weak"

        return {
            "id": f"proj-{index}",
            "name": name,
            "star_analysis": star_analysis
        }

    def _analyze_skills(self, resume_data: Dict) -> list:
        """分析技能描述"""
        issues = []

        skill_content = resume_data.get("skillContent", "")

        if skill_content:
            # 检查模糊词汇
            vague_keywords = ["熟悉", "了解", "掌握", "知道"]

            for keyword in vague_keywords:
                if keyword in skill_content:
                    issues.append({
                        "keyword": keyword,
                        "issue": "描述笼统",
                        "suggestion": f"建议改为更具体的描述，如：'熟练使用 X 开发，有 Y 个项目经验' 或 '精通 X，曾独立完成 Z'"
                    })
                    break

        return issues

    def analyze_resume(self, resume_data: Dict) -> Dict:
        """深度分析简历

        Returns:
            完整的分析报告 JSON
        """
        basic = resume_data.get("basic", {})

        # 1. 提取亮点
        highlights = []

        experience = resume_data.get("experience", [])
        companies = [exp.get("company", "") for exp in experience]

        # 大厂识别
        big_companies = ["腾讯", "阿里", "字节", "百度", "美团", "华为", "小米",
                        "微软", "谷歌", "苹果", "亚马逊", "Meta", "深言科技"]
        for company in companies:
            for bc in big_companies:
                if bc in company:
                    highlights.append(f"有{company}实习/工作经历")
                    break

        # 奖项
        awards = resume_data.get("awards", [])
        if awards:
            highlights.append(f"有{len(awards)}项荣誉奖项")

        # 项目
        projects = resume_data.get("projects", [])
        if projects:
            highlights.append(f"有{len(projects)}个项目经历")

        # 教育背景
        education = resume_data.get("education", [])
        if education:
            for edu in education:
                degree = edu.get("degree", "")
                if "硕" in degree or "博" in degree:
                    highlights.append(f"拥有{edu.get('degree', '')}学历")
                    break

        # 2. 完整性检查
        completeness = self._check_completeness(resume_data)

        # 3. STAR 分析
        content_analysis = {
            "experience": [self._analyze_star_for_experience(exp, i)
                          for i, exp in enumerate(experience)],
            "projects": [self._analyze_star_for_project(proj, i)
                        for i, proj in enumerate(projects)],
            "skills": self._analyze_skills(resume_data)
        }

        # 4. 汇总问题
        issues = []

        # 高优先级问题
        if "basic.summary" in completeness.get("empty_fields", []):
            issues.append({
                "section": "basic",
                "field": "summary",
                "problem": "个人总结为空",
                "severity": "high",
                "suggestion": "添加2-3句话的总结，突出核心优势和求职意向"
            })

        # 检查工作经历
        for exp_analysis in content_analysis.get("experience", []):
            star = exp_analysis.get("star_analysis", {})
            if star.get("result", {}).get("status") == "missing":
                issues.append({
                    "section": "experience",
                    "field": exp_analysis.get("id"),
                    "problem": f"{exp_analysis.get('company')} 工作经历缺少量化成果",
                    "severity": "high",
                    "suggestion": "添加具体的数据成果，如：提升性能 X%、节省 Y 小时、获得 Z 好评"
                })

        # 技能描述问题
        if content_analysis.get("skills"):
            issues.append({
                "section": "skills",
                "field": "skillContent",
                "problem": "技能描述过于笼统",
                "severity": "medium",
                "suggestion": "避免使用'熟悉'、'了解'等模糊词汇，改用具体描述"
            })

        # 5. 优化计划
        optimization_plan = [
            {"step": 1, "title": "内容强化", "actions": ["补充个人总结", "完善工作经历描述", "细化技能说明"]},
            {"step": 2, "title": "信息核验", "actions": ["检查联系方式", "确认时间线准确", "核实技能熟练度"]},
            {"step": 3, "title": "视觉美化", "actions": ["优化排版", "调整字体", "统一格式"]},
            {"step": 4, "title": "完成交付", "actions": ["预览简历", "导出PDF", "检查格式"]}
        ]

        return {
            "highlights": highlights,
            "completeness": completeness,
            "content_analysis": content_analysis,
            "issues": issues,
            "optimization_plan": optimization_plan
        }

    def format_analysis_as_markdown(self, analysis: Dict) -> str:
        """将分析报告格式化为 Markdown"""
        lines = []
        lines.append("📊 **简历分析报告**")
        lines.append("")

        # 亮点
        highlights = analysis.get("highlights", [])
        if highlights:
            lines.append("✨ **主要亮点**")
            for h in highlights:
                lines.append(f"• {h}")
            lines.append("")

        # 完整性问题
        completeness = analysis.get("completeness", {})
        missing_sections = completeness.get("missing_sections", [])
        empty_fields = completeness.get("empty_fields", [])

        if missing_sections or empty_fields:
            lines.append("⚠️ **缺少内容**")
            for ms in missing_sections:
                lines.append(f"• 缺少 {ms} 模块")
            for ef in empty_fields:
                field_name = ef.split(".")[-1]
                if field_name == "summary":
                    lines.append(f"• 个人总结为空")
                elif "details" in ef:
                    lines.append(f"• 工作经历描述不完整")
                elif "description" in ef:
                    lines.append(f"• 项目描述不完整")
            lines.append("")

        # 问题
        issues = analysis.get("issues", [])
        high_issues = [i for i in issues if i.get("severity") == "high"]
        medium_issues = [i for i in issues if i.get("severity") == "medium"]

        if high_issues:
            lines.append("🔴 **高优先级问题**")
            for issue in high_issues:
                lines.append(f"• {issue.get('problem')} - {issue.get('suggestion')}")
            lines.append("")

        if medium_issues:
            lines.append("🟡 **中优先级问题**")
            for issue in medium_issues:
                lines.append(f"• {issue.get('problem')} - {issue.get('suggestion')}")
            lines.append("")

        # 优化流程
        lines.append("📋 **优化流程**")
        lines.append("① 内容强化 → ② 信息核验 → ③ 视觉美化 → ④ 完成交付")
        lines.append("")

        return "\n".join(lines)
