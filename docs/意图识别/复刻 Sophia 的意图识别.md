# 复刻 Sophia-Pro 的意图识别系统

## 📋 概述

本文档详细分析 OpenManus 和 Sophia-Pro 的意图识别实现，说明已复刻的功能和未复刻的模块，并提供完整的代码示例。

---

## 🔍 当前 OpenManus 的意图识别实现

### 1. 意图类型定义

**位置：** `app/memory/conversation_state.py`

```python
class Intent(str, Enum):
    """用户意图 - 仅保留需要在代码层面特殊处理的意图"""
    GREETING = "greeting"  # 问候 - 直接返回，不走 LLM
    LOAD_RESUME = "load_resume"  # 加载简历 - 需检查重复
    UNKNOWN = "unknown"  # 未知 - 交由 LLM 根据上下文判断
```

**特点：**
- 只有 3 种意图类型
- 意图类型很少，主要用于特殊处理（问候、加载简历）
- 其他所有情况都交给 LLM 处理

### 2. LLM 意图分类

**位置：** `app/memory/conversation_state.py`

```python
async def classify_intent_with_llm(
    self,
    user_input: str,
    conversation_history: List[Any] = None,
    last_ai_message: Optional[str] = None
) -> Dict[str, Any]:
    """
    使用 LLM 进行意图分类
    """
    # 构建意图识别提示词
    prompt = f"""你是一个意图识别助手。根据用户输入判断是否为特殊意图。

## 用户输入
"{user_input}"

## 意图类型
- greeting: 问候语（你好、hi、hello、嘿等）
- load_resume: 加载简历（包含"加载简历"、"导入简历"等，且后面通常跟着文件路径）
- unknown: 其他所有情况（交给 LLM 根据上下文处理）

## 输出格式（JSON）
{{
    "intent": "greeting/load_resume/unknown",
    "confidence": 0.0-1.0,
    "reasoning": "简短理由"
}}

只返回JSON。"""

    response = await self.llm.ask(
        messages=[{"role": "user", "content": prompt}],
        stream=False,
        temperature=0.1
    )
    
    # 解析 JSON 响应
    result = json.loads(response)
    intent_str = result.get("intent", "unknown")
    intent = Intent(intent_str)
    
    return {
        "intent": intent,
        "confidence": result.get("confidence", 0.5),
        "extracted_info": result.get("extracted_info", {}),
        "reasoning": result.get("reasoning", "")
    }
```

**特点：**
- 完全依赖 LLM 进行意图分类
- 没有规则匹配
- 没有关键词匹配
- 没有技能注册表
- 简单的 prompt 让 LLM 判断

### 3. 意图处理流程

**位置：** `app/agent/manus.py`

```python
async def think(self) -> bool:
    """Process current state and decide next actions using LLM intent recognition."""
    
    # 获取最后的用户输入
    user_input = self._get_last_user_input()
    
    # 🧠 使用 LLM 意图识别
    intent_result = await self._conversation_state.process_input(
        user_input=user_input,
        conversation_history=self.memory.messages[-5:],
        last_ai_message=self._get_last_ai_message()
    )
    
    intent = intent_result["intent"]
    tool = intent_result.get("tool")
    tool_args = intent_result.get("tool_args", {})
    
    # 🎯 GREETING 意图：让 LLM 处理（通过 prompt 中的 greeting_exception 规则）
    if intent == Intent.GREETING:
        logger.info("👋 GREETING: 交给 LLM 处理（遵循 greeting_exception 规则）")
        # 继续往下走，让 LLM 处理
    
    # 🎯 LOAD_RESUME 意图：直接调用工具
    if tool and self._conversation_state.should_use_tool_directly(intent):
        if intent == Intent.LOAD_RESUME and self._conversation_state.context.resume_loaded:
            logger.info("✅ 简历已加载，跳过重复加载")
            return False
        return await self._handle_direct_tool_call(tool, tool_args, intent)
    
    # 🎯 其他意图：交给 LLM 自然处理
    self.system_prompt, self.next_step_prompt = await self._generate_dynamic_prompts(user_input, intent)
    # ... 继续 LLM 处理
```

**特点：**
- 简单的意图处理流程
- GREETING 和 LOAD_RESUME 有特殊处理
- 其他意图完全交给 LLM

---

## 🎯 Sophia-Pro 的意图识别实现

### 1. 意图类型定义

**位置：** `sophia-pro/backend/app/services/intent/intent_classifier.py`

```python
class IntentType(Enum):
    """意图类型"""
    SKILL_SPECIFIC = "skill_specific"  # 明确需要某个 skill
    GENERAL_CHAT = "general_chat"  # 普通对话
    TOOL_USE = "tool_use"  # 需要使用工具但不特定
    CLARIFICATION = "clarification"  # 需要澄清
```

**特点：**
- 4 种意图类型，更细粒度
- 区分技能特定、工具使用、澄清等场景

### 2. 两阶段分类策略

**位置：** `sophia-pro/backend/app/services/intent/intent_classifier.py`

```python
class IntentClassifier:
    """
    意图分类器
    
    采用两阶段分类策略：
    1. 基于规则的快速匹配（关键词 + 正则）
    2. LLM 增强分类（当规则匹配置信度不够时）
    """
    
    # 置信度阈值
    HIGH_CONFIDENCE_THRESHOLD = 0.7  # 高置信度，直接使用规则结果
    MIN_CONFIDENCE_THRESHOLD = 0.3  # 最低置信度，低于此值不考虑
    
    async def classify(
        self,
        query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> IntentResult:
        """
        对用户 query 进行意图分类
        """
        # Step 1: 基于规则的快速匹配
        rule_matches = self._rule_based_match(query)
        
        # Step 2: 判断是否需要 LLM 增强
        if rule_matches and rule_matches[0][1] >= self.HIGH_CONFIDENCE_THRESHOLD:
            # 高置信度，直接使用规则结果
            return self._build_result(rule_matches, "high_confidence_rule_match")
        
        # Step 3: 使用 LLM 增强分类（如果启用）
        if self.use_llm and (not rule_matches or rule_matches[0][1] < self.HIGH_CONFIDENCE_THRESHOLD):
            try:
                llm_result = await self._llm_classify(query, rule_matches, context)
                return llm_result
            except Exception as e:
                logger.warning(f"LLM classification failed, falling back to rules: {e}")
        
        # Step 4: 回退到规则结果
        if rule_matches:
            return self._build_result(rule_matches, "rule_match_fallback")
        
        # 无匹配
        return IntentResult(
            intent_type=IntentType.GENERAL_CHAT,
            reasoning="No skill matched",
        )
```

**特点：**
- **两阶段分类**：先规则匹配，再 LLM 增强
- **置信度阈值**：高置信度直接使用规则，低置信度使用 LLM
- **回退机制**：LLM 失败时回退到规则匹配

### 3. 规则匹配（Rule-Based Matching）

**位置：** `sophia-pro/backend/app/services/intent/intent_classifier.py`

```python
def _rule_based_match(self, query: str) -> List[Tuple[str, float]]:
    """
    基于规则的快速匹配
    
    计算每个 skill 的匹配分数：
    - 关键词匹配: 每个匹配 +0.15, 最高 0.45
    - 正则模式匹配: 匹配 +0.35
    - 描述相似度: 每个词 +0.05, 最高 0.2
    """
    query_lower = query.lower()
    matches: List[Tuple[str, float]] = []
    
    for skill_name, skill in self.registry.get_all_skills().items():
        score = 0.0
        
        # 1. 关键词匹配
        for kw in skill.trigger_keywords:
            kw_clean = kw.strip().lower()
            if kw_clean and kw_clean in query_lower:
                if len(kw_clean) >= 6:
                    score += self.weights.keyword_long  # 0.2
                else:
                    score += self.weights.keyword_short  # 0.15
        
        score = min(score, self.weights.keyword_max)  # 最高 0.45
        
        # 2. 正则模式匹配
        for pattern in skill.patterns:
            try:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    score += self.weights.pattern  # 0.35
                    break  # 只计算一次
            except re.error:
                continue
        
        # 3. 描述相似度（简单词匹配）
        desc_words = [w for w in skill.description.lower().split() if len(w) > 3]
        desc_hits = sum(1 for w in desc_words if w in query_lower)
        if desc_hits > 0:
            score += min(self.weights.desc_max, desc_hits * self.weights.desc)
        
        # 4. 应用优先级权重
        score *= skill.priority
        
        # 过滤低分
        if score >= self.MIN_CONFIDENCE_THRESHOLD:
            matches.append((skill_name, min(1.0, score)))
    
    # 按置信度排序
    matches.sort(key=lambda x: x[1], reverse=True)
    
    # 最多返回 3 个
    return matches[:3]
```

**评分权重配置：**

```python
@dataclass
class IntentScoreWeights:
    """评分权重配置"""
    keyword_short: float = 0.15  # 短关键词（<6字符）
    keyword_long: float = 0.2     # 长关键词（>=6字符）
    keyword_max: float = 0.45      # 关键词匹配最高分
    pattern: float = 0.35          # 正则模式匹配
    desc: float = 0.05            # 描述词匹配（每个词）
    desc_max: float = 0.2         # 描述匹配最高分
```

**特点：**
- **多维度评分**：关键词、正则、描述相似度
- **权重系统**：可配置的评分权重
- **优先级支持**：技能可以设置优先级权重
- **性能优化**：快速规则匹配，避免每次都调用 LLM

### 4. Skill Registry（技能注册表）

**位置：** `sophia-pro/backend/app/services/intent/skill_registry.py`

```python
@dataclass
class SkillMetadata:
    """Skill 元数据"""
    name: str
    description: str
    # 触发关键词（从 SKILL.md frontmatter 或配置中获取）
    trigger_keywords: List[str] = field(default_factory=list)
    # 正则匹配模式
    patterns: List[str] = field(default_factory=list)
    # 示例 queries
    example_queries: List[str] = field(default_factory=list)
    # skill 文件路径
    skill_path: str = ""
    # 适用的对话模式
    applicable_modes: List[str] = field(default_factory=lambda: ["general", "workflow", "report"])
    # 优先级权重 (1.0 为默认)
    priority: float = 1.0
    # 是否有显式配置（用于判断是否需要自动生成 keywords）
    has_explicit_config: bool = False


class SkillRegistry:
    """
    Skills 注册中心 - 单例模式
    
    负责：
    1. 从 skills 目录加载所有 SKILL.md 的元数据
    2. 提供 skills 查询接口
    3. 支持基于配置的 patterns 扩展
    """
    
    def _load_skills(self) -> None:
        """加载所有 skills 的元数据"""
        skills_dir = self._get_skills_directory()
        skill_files = sorted(skills_dir.rglob("SKILL.md"))
        
        for skill_md in skill_files:
            metadata = self._parse_skill_md(skill_md)
            if metadata:
                # 尝试加载单独的 INTENT.yaml 文件
                intent_yaml = skill_md.parent / "INTENT.yaml"
                if intent_yaml.exists():
                    self._load_intent_yaml(metadata, intent_yaml)
                self._skills[metadata.name] = metadata
    
    def _parse_skill_md(self, skill_md_path: Path) -> Optional[SkillMetadata]:
        """
        解析 SKILL.md 文件的 YAML frontmatter
        
        SKILL.md frontmatter 支持的 intent 字段：
        ```yaml
        ---
        name: my-skill
        description: "..."
        intent:
          keywords: ["关键词1", "keyword2"]
          patterns: [".*正则模式.*"]
          examples: ["示例查询1", "示例查询2"]
          priority: 1.0
        ---
        ```
        """
        # 解析 YAML frontmatter
        # 优先级 1: 从 SKILL.md frontmatter 中的 intent 字段获取
        # 优先级 2: 自动从 description 中提取关键词
```

**特点：**
- **自动加载**：从 `SKILL.md` 文件自动加载技能元数据
- **YAML 配置**：支持在 frontmatter 中配置意图识别信息
- **独立配置文件**：支持 `INTENT.yaml` 单独配置
- **自动提取关键词**：如果没有显式配置，自动从描述中提取
- **单例模式**：全局统一的技能注册表

### 5. LLM 增强分类

**位置：** `sophia-pro/backend/app/services/intent/intent_classifier.py`

```python
async def _llm_classify(
    self,
    query: str,
    rule_matches: List[Tuple[str, float]],
    context: Optional[Dict[str, Any]] = None,
) -> IntentResult:
    """
    使用 LLM 进行意图分类
    """
    # 构建 skills 描述
    skills_desc = self.registry.get_skills_summary()
    
    # 构建 prompt
    system_prompt = """You are an intent recognition expert. Analyze the user's input and determine if it requires a specific skill.

Output Format (JSON only, no markdown):
{
    "intent_type": "skill_specific" | "general_chat" | "tool_use" | "clarification",
    "matched_skills": [["skill_name", confidence], ...],
    "reasoning": "Your brief reasoning"
}

Respond with ONLY the JSON object, no other text."""

    user_prompt = f"""## Available Skills:
{skills_desc}

## User Input:
{query}

## Rule-based Match Results (for reference):
{rule_matches if rule_matches else "No matches from rules"}

Analyze the user's intent and determine if a specific skill is needed."""

    # 使用 OpenAI 兼容接口直接调用
    client = openai.AsyncOpenAI(api_key=api_key, base_url=base_url)
    response = await client.chat.completions.create(
        model=self.llm_model,  # 默认 gemini-2.5-flash，低延迟
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.1,
        max_tokens=500,
    )
    
    # 解析 LLM 响应
    result = json.loads(response_text)
    return self._build_result_from_llm(result)
```

**特点：**
- **参考规则结果**：LLM 可以看到规则匹配结果作为参考
- **技能摘要**：提供所有技能的摘要描述
- **低延迟模型**：默认使用 `gemini-2.5-flash` 快速模型
- **JSON 格式输出**：结构化输出，便于解析

### 6. Agent Intent Enhancer（意图增强器）

**位置：** `sophia-pro/backend/app/services/intent/intent_enhancer.py`

```python
class AgentIntentEnhancer:
    """
    Agent 意图增强器
    
    功能：
    1. 在 agent 执行前分析用户 query 的意图
    2. 根据意图匹配结果，在 query 前添加 /[skill:xxx] 标记
    3. 提供意图摘要用于日志和前端展示
    """
    
    async def enhance_query(
        self,
        user_query: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> tuple[str, Optional[IntentResult]]:
        """
        增强 user query
        """
        # 检查是否已有显式 skill 标记
        explicit_skill = self._has_explicit_skill_tag(user_query)
        if explicit_skill:
            return user_query, None
        
        # 进行意图识别
        intent_result = await self.classifier.classify(user_query, context)
        
        # 如果识别到特定 skill，在 query 前添加 skill 标记
        if intent_result.intent_type in (IntentType.SKILL_SPECIFIC, IntentType.TOOL_USE):
            if intent_result.matched_skills:
                top_skill = intent_result.matched_skills[0][0]
                enhanced_query = f"{self._build_skill_tag(top_skill)} {user_query}"
                return enhanced_query, intent_result
        
        return user_query, intent_result
    
    def _has_explicit_skill_tag(self, user_query: str) -> Optional[str]:
        """
        检查用户 query 是否已包含显式 skill 标记
        
        格式: /[skill:skill-name]
        """
        match = EXPLICIT_SKILL_PATTERN.search(user_query)
        if match:
            return match.group(1).strip()
        return None
```

**特点：**
- **自动添加技能标记**：识别到技能后自动在 query 前添加 `/[skill:xxx]`
- **显式标记支持**：支持用户手动指定技能 `/[skill:xxx]`
- **意图摘要**：提供意图识别摘要用于日志和前端展示

---

## ❌ 未复刻的模块

### 1. Skill Registry（技能注册表）

**功能：**
- 自动从 `SKILL.md` 文件加载技能元数据
- 支持 YAML frontmatter 配置意图识别信息
- 支持独立的 `INTENT.yaml` 配置文件
- 自动从描述中提取关键词

**为什么重要：**
- 集中管理所有技能的意图识别配置
- 便于维护和扩展
- 支持自动发现新技能

**复刻建议：**
```python
# app/services/intent/skill_registry.py
class ToolRegistry:
    """工具注册中心 - 类似 SkillRegistry"""
    
    def _load_tools(self) -> None:
        """从工具定义中加载元数据"""
        # 扫描所有工具类
        # 从工具描述中提取关键词
        # 支持配置文件覆盖
```

### 2. 规则匹配（Rule-Based Matching）

**功能：**
- 关键词匹配（短/长关键词不同权重）
- 正则模式匹配
- 描述相似度匹配
- 评分权重系统
- 优先级权重

**为什么重要：**
- **性能优化**：快速规则匹配，避免每次都调用 LLM
- **可解释性**：规则匹配结果更可解释
- **成本优化**：减少 LLM 调用次数

**复刻建议：**
```python
# app/services/intent/rule_matcher.py
class RuleMatcher:
    """规则匹配器"""
    
    def match(self, query: str, tools: List[ToolMetadata]) -> List[Tuple[str, float]]:
        """基于规则匹配工具"""
        # 关键词匹配
        # 正则匹配
        # 描述相似度
        # 返回评分排序的结果
```

### 3. 两阶段分类策略

**功能：**
- 先规则匹配，再 LLM 增强
- 置信度阈值判断
- 回退机制

**为什么重要：**
- **平衡性能和准确性**：规则匹配快速，LLM 增强准确
- **成本控制**：高置信度时跳过 LLM 调用
- **可靠性**：LLM 失败时回退到规则

**复刻建议：**
```python
# app/services/intent/intent_classifier.py
class IntentClassifier:
    """两阶段意图分类器"""
    
    async def classify(self, query: str) -> IntentResult:
        # Step 1: 规则匹配
        rule_matches = self.rule_matcher.match(query)
        
        # Step 2: 判断是否需要 LLM
        if rule_matches[0][1] >= HIGH_CONFIDENCE_THRESHOLD:
            return self._build_result(rule_matches)
        
        # Step 3: LLM 增强
        llm_result = await self._llm_classify(query, rule_matches)
        return llm_result
```

### 4. 评分权重系统

**功能：**
- 可配置的评分权重
- 关键词、正则、描述不同权重
- 优先级权重

**为什么重要：**
- **灵活性**：可以根据场景调整权重
- **可调优**：通过调整权重优化匹配效果

**复刻建议：**
```python
# app/services/intent/weights.py
@dataclass
class IntentScoreWeights:
    keyword_short: float = 0.15
    keyword_long: float = 0.2
    keyword_max: float = 0.45
    pattern: float = 0.35
    desc: float = 0.05
    desc_max: float = 0.2
```

### 5. Agent Intent Enhancer（意图增强器）

**功能：**
- 在 agent 执行前增强 query
- 自动添加技能标记
- 支持显式技能标记

**为什么重要：**
- **引导 agent**：通过标记引导 agent 使用特定工具
- **用户体验**：支持用户手动指定工具

**复刻建议：**
```python
# app/services/intent/intent_enhancer.py
class AgentIntentEnhancer:
    """意图增强器"""
    
    async def enhance_query(self, query: str) -> str:
        """增强 query，添加工具标记"""
        intent_result = await self.classifier.classify(query)
        if intent_result.matched_tools:
            return f"/[tool:{intent_result.matched_tools[0]}] {query}"
        return query
```

### 6. 显式技能标记支持

**功能：**
- 支持用户手动指定技能：`/[skill:xxx]`
- 检测到显式标记时跳过意图识别

**为什么重要：**
- **用户控制**：允许用户明确指定要使用的工具
- **性能优化**：跳过意图识别，直接使用指定工具

**复刻建议：**
```python
# 在 AgentIntentEnhancer 中
EXPLICIT_TOOL_PATTERN = re.compile(r"/\[tool:([^\]]+)\]", re.IGNORECASE)

def _has_explicit_tool_tag(self, query: str) -> Optional[str]:
    """检查是否有显式工具标记"""
    match = EXPLICIT_TOOL_PATTERN.search(query)
    return match.group(1) if match else None
```

---

## 📊 对比总结

| 功能 | OpenManus | Sophia-Pro | 状态 |
|------|-----------|------------|------|
| **意图类型** | 3 种（GREETING, LOAD_RESUME, UNKNOWN） | 4 种（SKILL_SPECIFIC, GENERAL_CHAT, TOOL_USE, CLARIFICATION） | ❌ 未复刻 |
| **规则匹配** | ❌ 无 | ✅ 关键词、正则、描述相似度 | ❌ 未复刻 |
| **LLM 分类** | ✅ 简单 prompt | ✅ 两阶段分类（规则+LLM） | ⚠️ 部分复刻 |
| **技能注册表** | ❌ 无 | ✅ SkillRegistry 自动加载 | ❌ 未复刻 |
| **评分权重** | ❌ 无 | ✅ 可配置权重系统 | ❌ 未复刻 |
| **置信度阈值** | ❌ 无 | ✅ 高/低置信度阈值 | ❌ 未复刻 |
| **意图增强器** | ❌ 无 | ✅ AgentIntentEnhancer | ❌ 未复刻 |
| **显式标记** | ❌ 无 | ✅ `/[skill:xxx]` 支持 | ❌ 未复刻 |
| **问候处理** | ✅ Prompt 规则（greeting_exception） | ✅ Prompt 规则 | ✅ 已复刻 |

---

## 🎯 复刻优先级建议

### 高优先级（核心功能）

1. **规则匹配（Rule-Based Matching）**
   - 性能优化：减少 LLM 调用
   - 成本控制：高置信度时跳过 LLM
   - 实现难度：中等

2. **两阶段分类策略**
   - 平衡性能和准确性
   - 实现难度：中等

3. **工具注册表（Tool Registry）**
   - 集中管理工具元数据
   - 支持自动发现和配置
   - 实现难度：较高

### 中优先级（增强功能）

4. **评分权重系统**
   - 可调优的匹配算法
   - 实现难度：低

5. **置信度阈值**
   - 控制何时使用 LLM
   - 实现难度：低

### 低优先级（可选功能）

6. **意图增强器**
   - 引导 agent 使用特定工具
   - 实现难度：中等

7. **显式工具标记**
   - 用户手动指定工具
   - 实现难度：低

---

## 💡 复刻实现示例

### 示例 1：工具注册表

```python
# app/services/intent/tool_registry.py
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from pathlib import Path
import yaml

@dataclass
class ToolMetadata:
    """工具元数据"""
    name: str
    description: str
    trigger_keywords: List[str] = field(default_factory=list)
    patterns: List[str] = field(default_factory=list)
    priority: float = 1.0

class ToolRegistry:
    """工具注册中心"""
    
    _instance: Optional["ToolRegistry"] = None
    _tools: Dict[str, ToolMetadata] = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not hasattr(self, '_initialized'):
            self._load_tools()
            self._initialized = True
    
    def _load_tools(self):
        """从工具定义中加载元数据"""
        # 扫描 app/tool/ 目录
        # 从工具类的 description 中提取关键词
        # 支持配置文件覆盖
        
        # 示例：从工具类加载
        from app.tool import ToolCollection
        
        # 遍历所有工具
        for tool in ToolCollection.get_all_tools():
            metadata = ToolMetadata(
                name=tool.name,
                description=tool.description,
                trigger_keywords=self._extract_keywords(tool.description),
            )
            self._tools[tool.name] = metadata
    
    def _extract_keywords(self, description: str) -> List[str]:
        """从描述中提取关键词"""
        # 简单的关键词提取逻辑
        words = description.lower().split()
        keywords = [w for w in words if len(w) > 3]
        return keywords[:10]  # 最多 10 个
    
    def get_all_tools(self) -> Dict[str, ToolMetadata]:
        """获取所有工具"""
        return self._tools.copy()
```

### 示例 2：规则匹配器

```python
# app/services/intent/rule_matcher.py
import re
from typing import List, Tuple
from app.services.intent.tool_registry import ToolRegistry, ToolMetadata

class RuleMatcher:
    """规则匹配器"""
    
    def __init__(self, registry: ToolRegistry = None):
        self.registry = registry or ToolRegistry()
        # 评分权重
        self.weights = {
            'keyword_short': 0.15,
            'keyword_long': 0.2,
            'keyword_max': 0.45,
            'pattern': 0.35,
            'desc': 0.05,
            'desc_max': 0.2,
        }
        self.min_confidence = 0.3
    
    def match(self, query: str) -> List[Tuple[str, float]]:
        """基于规则匹配工具"""
        query_lower = query.lower()
        matches: List[Tuple[str, float]] = []
        
        for tool_name, tool in self.registry.get_all_tools().items():
            score = 0.0
            
            # 1. 关键词匹配
            for kw in tool.trigger_keywords:
                kw_clean = kw.strip().lower()
                if kw_clean and kw_clean in query_lower:
                    if len(kw_clean) >= 6:
                        score += self.weights['keyword_long']
                    else:
                        score += self.weights['keyword_short']
            
            score = min(score, self.weights['keyword_max'])
            
            # 2. 正则模式匹配
            for pattern in tool.patterns:
                try:
                    if re.search(pattern, query_lower, re.IGNORECASE):
                        score += self.weights['pattern']
                        break
                except re.error:
                    continue
            
            # 3. 描述相似度
            desc_words = [w for w in tool.description.lower().split() if len(w) > 3]
            desc_hits = sum(1 for w in desc_words if w in query_lower)
            if desc_hits > 0:
                score += min(
                    self.weights['desc_max'],
                    desc_hits * self.weights['desc']
                )
            
            # 4. 应用优先级
            score *= tool.priority
            
            # 过滤低分
            if score >= self.min_confidence:
                matches.append((tool_name, min(1.0, score)))
        
        # 按置信度排序
        matches.sort(key=lambda x: x[1], reverse=True)
        return matches[:3]  # 最多返回 3 个
```

### 示例 3：两阶段意图分类器

```python
# app/services/intent/intent_classifier.py
from typing import Optional, Dict, Any
from app.services.intent.rule_matcher import RuleMatcher
from app.services.intent.tool_registry import ToolRegistry

class IntentResult:
    """意图识别结果"""
    def __init__(self, intent_type: str, matched_tools: List[Tuple[str, float]], reasoning: str):
        self.intent_type = intent_type
        self.matched_tools = matched_tools
        self.reasoning = reasoning

class IntentClassifier:
    """两阶段意图分类器"""
    
    HIGH_CONFIDENCE_THRESHOLD = 0.7
    MIN_CONFIDENCE_THRESHOLD = 0.3
    
    def __init__(self, use_llm: bool = True, llm_model: str = "google/gemini-2.5-flash"):
        self.rule_matcher = RuleMatcher()
        self.use_llm = use_llm
        self.llm_model = llm_model
    
    async def classify(self, query: str, context: Optional[Dict[str, Any]] = None) -> IntentResult:
        """两阶段分类"""
        # Step 1: 规则匹配
        rule_matches = self.rule_matcher.match(query)
        
        # Step 2: 判断是否需要 LLM
        if rule_matches and rule_matches[0][1] >= self.HIGH_CONFIDENCE_THRESHOLD:
            return IntentResult(
                intent_type="tool_specific",
                matched_tools=rule_matches,
                reasoning="high_confidence_rule_match"
            )
        
        # Step 3: LLM 增强（如果启用）
        if self.use_llm:
            try:
                llm_result = await self._llm_classify(query, rule_matches, context)
                return llm_result
            except Exception as e:
                logger.warning(f"LLM classification failed: {e}")
        
        # Step 4: 回退到规则结果
        if rule_matches:
            return IntentResult(
                intent_type="tool_use",
                matched_tools=rule_matches,
                reasoning="rule_match_fallback"
            )
        
        # 无匹配
        return IntentResult(
            intent_type="general_chat",
            matched_tools=[],
            reasoning="No tool matched"
        )
    
    async def _llm_classify(self, query: str, rule_matches: List[Tuple[str, float]], context: Optional[Dict[str, Any]]) -> IntentResult:
        """LLM 增强分类"""
        # 构建 prompt
        tools_desc = self.rule_matcher.registry.get_tools_summary()
        
        prompt = f"""分析用户输入的意图，判断是否需要特定工具。

可用工具：
{tools_desc}

用户输入：{query}

规则匹配结果（参考）：{rule_matches if rule_matches else "无匹配"}

返回 JSON：
{{
    "intent_type": "tool_specific" | "general_chat" | "tool_use",
    "matched_tools": [["tool_name", confidence], ...],
    "reasoning": "理由"
}}"""
        
        # 调用 LLM
        response = await self.llm.ask(messages=[{"role": "user", "content": prompt}])
        result = json.loads(response)
        
        return IntentResult(
            intent_type=result.get("intent_type", "general_chat"),
            matched_tools=result.get("matched_tools", []),
            reasoning=f"LLM: {result.get('reasoning', '')}"
        )
```

---

## 🔧 集成到 OpenManus

### 1. 修改 `conversation_state.py`

```python
# app/memory/conversation_state.py
from app.services.intent.intent_classifier import IntentClassifier

class ConversationStateManager:
    def __init__(self, llm=None):
        self.context = ConversationContext()
        self.llm = llm
        # 添加意图分类器
        self.intent_classifier = IntentClassifier(use_llm=True)
    
    async def detect_intent(self, user_input: str, ...) -> Tuple[Intent, Dict[str, Any]]:
        """使用两阶段分类器检测意图"""
        # 先使用规则匹配
        intent_result = await self.intent_classifier.classify(user_input)
        
        # 映射到 OpenManus 的 Intent 类型
        if intent_result.intent_type == "tool_specific":
            if "cv_reader_agent" in [t[0] for t in intent_result.matched_tools]:
                return Intent.LOAD_RESUME, {}
            # 其他工具映射...
        
        # 检查是否是问候
        if any(kw in user_input.lower() for kw in ["你好", "hello", "hi"]):
            return Intent.GREETING, {}
        
        return Intent.UNKNOWN, {}
```

### 2. 修改 `manus.py`

```python
# app/agent/manus.py
async def think(self) -> bool:
    """使用两阶段意图分类"""
    user_input = self._get_last_user_input()
    
    # 使用两阶段分类器
    intent_result = await self._conversation_state.intent_classifier.classify(user_input)
    
    # 根据匹配的工具决定下一步
    if intent_result.matched_tools:
        top_tool = intent_result.matched_tools[0][0]
        # 直接调用工具或引导 LLM 使用工具
        ...
```

---

## 📝 总结

### 已复刻的功能

1. ✅ **问候处理**：通过 `greeting_exception` prompt 规则
2. ✅ **LLM 意图分类**：基本的 LLM 分类功能

### 未复刻的核心模块

1. ❌ **Skill/Tool Registry**：技能/工具注册表
2. ❌ **规则匹配**：关键词、正则、描述相似度匹配
3. ❌ **两阶段分类**：规则匹配 + LLM 增强
4. ❌ **评分权重系统**：可配置的评分权重
5. ❌ **置信度阈值**：高/低置信度判断
6. ❌ **意图增强器**：自动添加工具标记
7. ❌ **显式标记支持**：`/[tool:xxx]` 格式

### 复刻建议

1. **优先复刻规则匹配**：性能优化，减少 LLM 调用
2. **实现两阶段分类**：平衡性能和准确性
3. **创建工具注册表**：集中管理工具元数据
4. **添加评分权重**：可调优的匹配算法

这些模块的复刻将显著提升 OpenManus 的意图识别能力和性能。
