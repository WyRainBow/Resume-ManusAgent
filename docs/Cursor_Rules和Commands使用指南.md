# Cursor Rules 和 Commands 使用指南

## 概述

Cursor 编辑器提供了 **Rules（规则）** 和 **Commands（命令）** 两种功能，用于定制 AI 助手的行为和提高开发效率。

---

## 1. Rules（规则）

### 1.1 什么是 Rules

Rules 允许您为 AI 助手设置系统级指令，指导其在代码生成、编辑和解释时的行为。通过定义规则，您可以确保 AI 的输出符合项目的编码风格和需求。

### 1.2 Rules 的类型

#### 项目规则（Project Rules）

- **位置**：项目根目录的 `.cursor/rules` 文件夹
- **格式**：`.mdc` 文件（Markdown with frontmatter）
- **作用域**：仅适用于当前项目

#### 全局规则（Global Rules）

- **位置**：Cursor 设置中配置
- **设置路径**：`设置` > `通用` > `AI 规则`
- **作用域**：适用于所有项目

### 1.3 创建项目规则

#### 步骤

1. 在项目根目录创建 `.cursor` 文件夹（如果不存在）
2. 在 `.cursor` 文件夹内创建 `rules` 子目录
3. 在 `rules` 目录中创建规则文件（`.mdc` 格式）

#### 规则文件格式

```markdown
---
description: 规则描述
globs: ["**/*.js", "**/*.ts"]  # 可选：指定适用的文件类型
alwaysApply: true  # 可选：是否总是应用
---

## 规则内容

这里是具体的规则说明...
```

#### 示例：编码风格规则

创建 `.cursor/rules/coding-style.mdc`：

```markdown
---
description: JavaScript/TypeScript 编码风格
globs: ["**/*.js", "**/*.ts"]
alwaysApply: true
---

## 编码风格指南

- 使用 2 个空格进行缩进
- 每行代码不超过 80 个字符
- 使用分号结束语句
- 使用单引号而非双引号
- 函数和方法应该包含 JSDoc 风格注释
- 优先使用 const，其次 let，避免 var
```

#### 示例：项目特定规则

创建 `.cursor/rules/openmanus.mdc`：

```markdown
---
description: OpenManus 项目开发规则
alwaysApply: true
---

## 核心原则

1. **提示词设计**：系统提示词可稍长，场景化提示词保持简洁
2. **引导性对话**：原则而非脚本，主动引导、方案提案、逐项确认、流程预告、具体化
3. **交互规范**：使用中文时设置 working language 为 Chinese，使用"您/您的"，分析后给出下一步建议
```

### 1.4 规则文件配置选项

| 选项 | 类型 | 说明 | 示例 |
|------|------|------|------|
| `description` | string | 规则的简短描述 | `"编码风格指南"` |
| `globs` | array | 文件匹配模式，指定规则适用的文件 | `["**/*.js", "**/*.ts"]` |
| `alwaysApply` | boolean | 是否总是应用此规则 | `true` / `false` |

### 1.5 规则最佳实践

1. **保持简洁**：规则应该简洁明了，只包含关键信息
2. **分类管理**：不同类型的规则创建不同的文件
3. **使用描述**：为每个规则文件添加清晰的描述
4. **合理使用 globs**：只在需要时指定文件类型，避免过度限制

---

## 2. Commands（命令）

### 2.1 什么是 Commands

Commands 是 Cursor 提供的快捷键和指令，帮助您快速执行各种操作，提高开发效率。

### 2.2 常用快捷键命令

#### 核心命令

| 快捷键 | 功能 | 说明 |
|--------|------|------|
| `Ctrl/⌘ + K` | 内联编辑 | 打开内联编辑器，根据描述生成或修改代码 |
| `Ctrl/⌘ + L` | 聊天界面 | 打开聊天界面，与 AI 进行对话 |
| `Ctrl/⌘ + I` | Composer | 打开 Composer，生成新的代码片段或文件 |
| `Ctrl/⌘ + ↵` | 应用更改 | 在 Cmd K 模式下应用 AI 生成的更改 |
| `Ctrl/⌘ + ⌫` | 取消更改 | 在 Cmd K 模式下取消或删除更改 |

#### @ 符号引用

在聊天或命令中使用 `@` 符号可以引用特定的上下文：

| 用法 | 功能 | 示例 |
|------|------|------|
| `@filename` | 引用文件 | `@App.jsx` |
| `@functionName` | 引用函数 | `@handleSubmit` |
| `@variableName` | 引用变量 | `@userData` |
| `@codebase query` | 搜索代码库 | `@codebase 如何实现用户认证` |
| `@web query` | 搜索网络 | `@web React hooks 最佳实践` |

### 2.3 使用示例

#### 示例 1：代码生成（Cmd K）

1. 按下 `Ctrl/⌘ + K` 打开内联编辑器
2. 输入描述：`创建一个用户登录函数，使用 JWT 认证`
3. AI 生成代码
4. 按下 `Ctrl/⌘ + ↵` 应用更改

#### 示例 2：代码优化（Cmd K）

1. 选中需要优化的代码段
2. 按下 `Ctrl/⌘ + K`
3. 输入：`优化这段代码，提高性能`
4. AI 提供优化建议
5. 选择应用或取消

#### 示例 3：聊天对话（Cmd L）

1. 按下 `Ctrl/⌘ + L` 打开聊天界面
2. 输入问题：`@App.jsx 这段代码有什么问题？`
3. AI 分析代码并提供建议

#### 示例 4：使用 Composer（Cmd I）

1. 按下 `Ctrl/⌘ + I` 打开 Composer
2. 描述需求：`创建一个用户管理模块，包含增删改查功能`
3. AI 生成完整的代码文件

---

## 3. 自定义 Commands

### 3.1 创建自定义命令

Cursor 支持在 `.cursor/commands` 目录中创建自定义命令。

#### 步骤

1. 在项目根目录创建 `.cursor/commands` 文件夹
2. 创建命令文件（`.mdc` 格式）

#### 命令文件格式

```markdown
---
name: 命令名称
description: 命令描述
prompt: 执行的提示词
---

## 命令说明

这里是命令的详细说明...
```

#### 示例：创建测试命令

创建 `.cursor/commands/create-test.mdc`：

```markdown
---
name: 创建单元测试
description: 为当前文件创建单元测试
prompt: 为当前文件创建一个完整的单元测试文件，使用 pytest 框架
---

## 说明

此命令会为当前打开的文件自动生成单元测试。
```

### 3.2 使用自定义命令

1. 打开命令面板：`Ctrl/⌘ + Shift + P`
2. 输入命令名称
3. 选择并执行

---

## 4. 最佳实践

### 4.1 Rules 最佳实践

1. **分层管理**：
   - 全局规则：适用于所有项目的通用规则
   - 项目规则：项目特定的编码风格和约定

2. **保持更新**：
   - 定期审查和更新规则
   - 删除不再需要的规则

3. **文档化**：
   - 为每个规则添加清晰的描述
   - 在团队中共享规则文件

### 4.2 Commands 最佳实践

1. **合理使用快捷键**：
   - 熟悉常用快捷键，提高效率
   - 根据工作流自定义快捷键

2. **善用 @ 引用**：
   - 使用 `@filename` 提供上下文
   - 使用 `@codebase` 搜索相关代码

3. **创建常用命令**：
   - 为重复性任务创建自定义命令
   - 命令名称要清晰易懂

---

## 5. 参考资料

### 官方文档

- [Cursor AI 规则文档](https://docs.cursor.com/zh/context/rules-for-ai)
- [Cursor 官方文档](https://docs.cursor.com/)

### 社区资源

- [Cursor Rules 配置指南](https://cursor.zone/faq/cursor-rules-configuration-guide.html)
- [Cursor AI 快捷键完全指南](https://learn-cursor.com/blog/posts/cursor-shortcuts)
- [Cursor Rules 平台](https://www.cursorrules.pro/)

### 视频教程

- [Cursor 使用教程](https://www.youtube.com/watch?v=lypPoT8lZ2M)

---

## 6. 常见问题

### Q: Rules 文件应该放在哪里？

A: 项目规则放在 `.cursor/rules/` 目录，全局规则在 Cursor 设置中配置。

### Q: 如何让规则只适用于特定文件类型？

A: 使用 `globs` 选项指定文件匹配模式，例如：`globs: ["**/*.js", "**/*.ts"]`

### Q: 可以创建多个规则文件吗？

A: 可以，建议按功能分类创建不同的规则文件，例如：`coding-style.mdc`、`testing.mdc`、`documentation.mdc`

### Q: 自定义命令如何执行？

A: 通过命令面板（`Ctrl/⌘ + Shift + P`）搜索并执行自定义命令。

### Q: Rules 和 Commands 有什么区别？

A:
- **Rules**：指导 AI 的行为和输出风格，是"如何做"
- **Commands**：执行特定操作的快捷方式，是"做什么"

---

## 7. 总结

通过合理配置 Rules 和熟练使用 Commands，您可以：

- ✅ 定制 AI 助手的行为，使其更符合项目需求
- ✅ 提高代码生成的质量和一致性
- ✅ 显著提升开发效率
- ✅ 保持团队编码风格统一

建议从简单的规则开始，逐步完善和优化，找到最适合您和团队的工作方式。

