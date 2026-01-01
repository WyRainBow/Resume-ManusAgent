#!/usr/bin/env python3
"""
综合演示工作流
展示OpenManus工具组合使用的工作流程
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

def print_header(title):
    """打印标题"""
    print("\n" + "=" * 60)
    print(f" {title}")
    print("=" * 60)

def step1_workspace_analysis():
    """步骤1：工作空间分析"""
    print_header("步骤1: 工作空间分析")
    
    workspace_path = Path(__file__).parent
    
    print(f"📁 分析工作空间: {workspace_path}")
    print()
    
    # 获取文件列表
    files = []
    directories = []
    
    for item in workspace_path.iterdir():
        if item.is_file():
            size = item.stat().st_size
            files.append({
                'name': item.name,
                'size': size,
                'size_kb': size / 1024,
                'type': 'file'
            })
        else:
            directories.append({
                'name': item.name,
                'type': 'directory'
            })
    
    # 显示结果
    print(f"发现 {len(files)} 个文件, {len(directories)} 个目录")
    print()
    
    print("📄 文件列表:")
    for file in sorted(files, key=lambda x: x['name'].lower()):
        print(f"  • {file['name']} ({file['size_kb']:.1f} KB)")
    
    print()
    
    # 按类型分组
    file_types = {}
    for file in files:
        ext = Path(file['name']).suffix.lower()
        file_types[ext] = file_types.get(ext, 0) + 1
    
    print("📊 文件类型分布:")
    for ext, count in sorted(file_types.items()):
        if ext:
            print(f"  {ext}: {count} 个")
    
    total_size = sum(f['size'] for f in files)
    print(f"\n💾 总大小: {total_size:,} bytes ({total_size/1024/1024:.2f} MB)")
    
    return {
        'files': files,
        'directories': directories,
        'file_types': file_types,
        'total_size': total_size
    }

def step2_resume_analysis():
    """步骤2：简历分析"""
    print_header("步骤2: 简历分析")
    
    resume_file = "朱兆武_简历.md"
    resume_path = Path(__file__).parent / resume_file
    
    if not resume_path.exists():
        print(f"❌ 找不到简历文件: {resume_file}")
        return None
    
    print(f"📄 分析简历文件: {resume_file}")
    print()
    
    # 简单分析简历内容
    try:
        with open(resume_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 基本统计
        lines = content.split('\n')
        words = content.split()
        
        # 提取关键部分
        sections = []
        current_section = None
        
        for line in lines:
            if line.startswith('## '):
                if current_section:
                    sections.append(current_section)
                current_section = {
                    'title': line[3:].strip(),
                    'content': [],
                    'line_count': 0
                }
            elif current_section and line.strip():
                current_section['content'].append(line)
                current_section['line_count'] += 1
        
        if current_section:
            sections.append(current_section)
        
        # 显示结果
        print(f"📝 简历统计:")
        print(f"  • 总行数: {len(lines)}")
        print(f"  • 总字数: {len(words)}")
        print(f"  • 总字符数: {len(content)}")
        print(f"  • 章节数: {len(sections)}")
        print()
        
        print("📑 章节概览:")
        for section in sections:
            print(f"  • {section['title']} ({section['line_count']} 行)")
        
        # 提取技术关键词
        tech_keywords = [
            'Java', 'Python', 'Spring', 'MySQL', 'Redis', 'Docker', 
            'Kubernetes', 'AWS', '微服务', '架构', '优化'
        ]
        
        found_tech = []
        for keyword in tech_keywords:
            if keyword in content:
                found_tech.append(keyword)
        
        print(f"\n💻 发现的技术关键词: {len(found_tech)} 个")
        if found_tech:
            print("  " + ", ".join(found_tech))
        
        return {
            'file': resume_file,
            'lines': len(lines),
            'words': len(words),
            'chars': len(content),
            'sections': len(sections),
            'tech_keywords': found_tech,
            'section_titles': [s['title'] for s in sections]
        }
        
    except Exception as e:
        print(f"❌ 分析简历时出错: {e}")
        return None

def step3_script_analysis():
    """步骤3：脚本分析"""
    print_header("步骤3: Python脚本分析")
    
    workspace_path = Path(__file__).parent
    python_files = list(workspace_path.glob("*.py"))
    
    print(f"🔍 发现 {len(python_files)} 个Python脚本:")
    
    script_analysis = []
    
    for py_file in sorted(python_files, key=lambda x: x.name.lower()):
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 基本统计
            lines = content.split('\n')
            code_lines = [l for l in lines if l.strip() and not l.strip().startswith('#')]
            comment_lines = [l for l in lines if l.strip().startswith('#')]
            
            # 提取函数定义
            functions = []
            for line in lines:
                if line.strip().startswith('def '):
                    func_name = line.strip()[4:].split('(')[0]
                    functions.append(func_name)
            
            # 提取导入
            imports = []
            for line in lines:
                if line.strip().startswith('import ') or line.strip().startswith('from '):
                    imports.append(line.strip())
            
            analysis = {
                'file': py_file.name,
                'total_lines': len(lines),
                'code_lines': len(code_lines),
                'comment_lines': len(comment_lines),
                'comment_ratio': len(comment_lines) / len(lines) * 100 if lines else 0,
                'functions': len(functions),
                'imports': len(imports),
                'size': py_file.stat().st_size
            }
            
            script_analysis.append(analysis)
            
            print(f"\n📜 {py_file.name}:")
            print(f"  • 总行数: {analysis['total_lines']}")
            print(f"  • 代码行: {analysis['code_lines']}")
            print(f"  • 注释行: {analysis['comment_lines']} ({analysis['comment_ratio']:.1f}%)")
            print(f"  • 函数数: {analysis['functions']}")
            print(f"  • 导入数: {analysis['imports']}")
            print(f"  • 文件大小: {analysis['size']:,} bytes")
            
            if functions:
                print(f"  • 函数列表: {', '.join(functions[:5])}" + ("..." if len(functions) > 5 else ""))
            
        except Exception as e:
            print(f"❌ 分析 {py_file.name} 时出错: {e}")
    
    return script_analysis

def step4_generate_report(workspace_data, resume_data, scripts_data):
    """步骤4：生成综合报告"""
    print_header("步骤4: 生成综合报告")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_file = f"comprehensive_analysis_{timestamp}.json"
    
    report = {
        'generated_at': datetime.now().isoformat(),
        'workflow': 'OpenManus综合演示工作流',
        'workspace_analysis': workspace_data,
        'resume_analysis': resume_data,
        'script_analysis': scripts_data,
        'summary': {
            'total_files': len(workspace_data.get('files', [])),
            'total_python_scripts': len(scripts_data),
            'resume_sections': resume_data.get('sections', 0) if resume_data else 0,
            'total_script_lines': sum(s.get('total_lines', 0) for s in scripts_data),
            'total_script_functions': sum(s.get('functions', 0) for s in scripts_data)
        },
        'insights': []
    }
    
    # 生成洞察
    insights = []
    
    # 工作空间洞察
    if workspace_data:
        total_size_mb = workspace_data.get('total_size', 0) / 1024 / 1024
        insights.append(f"工作空间包含 {len(workspace_data.get('files', []))} 个文件，总大小 {total_size_mb:.2f} MB")
    
    # 简历洞察
    if resume_data:
        insights.append(f"简历包含 {resume_data.get('sections', 0)} 个章节，{resume_data.get('words', 0)} 个字")
        insights.append(f"简历中提到 {len(resume_data.get('tech_keywords', []))} 个关键技术")
    
    # 脚本洞察
    if scripts_data:
        total_functions = sum(s.get('functions', 0) for s in scripts_data)
        avg_comment_ratio = sum(s.get('comment_ratio', 0) for s in scripts_data) / len(scripts_data)
        insights.append(f"共有 {len(scripts_data)} 个Python脚本，包含 {total_functions} 个函数")
        insights.append(f"平均注释比例: {avg_comment_ratio:.1f}%")
    
    report['insights'] = insights
    
    # 保存报告
    try:
        report_path = Path(__file__).parent / report_file
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 综合报告已生成:")
        print(f"   文件: {report_file}")
        print(f"   大小: {report_path.stat().st_size:,} bytes")
        print()
        
        print("📋 报告摘要:")
        print(f"  • 生成时间: {report['generated_at']}")
        print(f"  • 工作流: {report['workflow']}")
        print()
        
        print("🔍 关键洞察:")
        for i, insight in enumerate(insights, 1):
            print(f"  {i}. {insight}")
        
        return report_file
        
    except Exception as e:
        print(f"❌ 生成报告时出错: {e}")
        return None

def step5_create_readme():
    """步骤5：创建README文档"""
    print_header("步骤5: 创建README文档")
    
    readme_content = """# OpenManus 工作空间分析报告

## 概述
本报告由OpenManus综合演示工作流自动生成，展示了工作空间分析、简历分析和脚本分析的能力。

## 生成的文件

### 1. 分析脚本
- `analyze_workspace.py` - 工作空间分析工具
- `resume_analyzer.py` - 简历分析工具  
- `demo_workflow.py` - 综合演示工作流脚本

### 2. 演示脚本
- `demo_script.py` - 基础演示脚本
- `enhanced_script.py` - 增强版演示脚本

### 3. 数据文件
- `朱兆武_简历.md` - 示例简历文件
- `example.txt` - 示例文本文件

## 工具能力展示

### 文件处理能力
- 文件查看和编辑
- 文件内容分析
- 文件系统扫描
- 报告生成

### 数据分析能力
- 文本内容分析
- 结构分析
- 统计计算
- 可视化输出

### 自动化能力
- 批量文件处理
- 数据提取和转换
- 报告自动生成
- 工作流自动化

## 使用说明

### 运行工作空间分析
```bash
python analyze_workspace.py
```

### 运行简历分析
```bash
python resume_analyzer.py
```

### 运行综合演示
```bash
python demo_workflow.py
```

## 技术栈
- Python 3.x
- 标准库: os, json, re, datetime, pathlib
- 正则表达式处理
- 文件系统操作

## 生成时间
{timestamp}

---

*本报告由OpenManus AI助手自动生成*
"""
    
    # 替换时间戳
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    readme_content = readme_content.replace("{timestamp}", timestamp)
    
    # 保存README文件
    readme_file = "README_ANALYSIS.md"
    readme_path = Path(__file__).parent / readme_file
    
    try:
        with open(readme_path, 'w', encoding='utf-8') as f:
            f.write(readme_content)
        
        print(f"✅ README文档已创建:")
        print(f"   文件: {readme_file}")
        print(f"   大小: {readme_path.stat().st_size:,} bytes")
        print()
        
        print("📖 文档内容预览:")
        print("-" * 40)
        lines = readme_content.split('\n')[:15]
        for line in lines:
            print(line)
        print("...")
        print("-" * 40)
        
        return readme_file
        
    except Exception as e:
        print(f"❌ 创建README时出错: {e}")
        return None

def main():
    """主工作流"""
    print("🚀 OpenManus 综合演示工作流")
    print("=" * 60)
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 执行所有步骤
    print("📊 开始执行分析工作流...")
    print()
    
    # 步骤1: 工作空间分析
    workspace_data = step1_workspace_analysis()
    
    # 步骤2: 简历分析
    resume_data = step2_resume_analysis()
    
    # 步骤3: 脚本分析
    scripts_data = step3_script_analysis()
    
    # 步骤4: 生成综合报告
    if workspace_data or resume_data or scripts_data:
        report_file = step4_generate_report(workspace_data, resume_data, scripts_data)
    else:
        print("⚠️ 没有足够的数据生成报告")
        report_file = None
    
    # 步骤5: 创建README
    readme_file = step5_create_readme()
    
    # 完成总结
    print_header("工作流完成")
    
    print("🎉 所有步骤已完成!")
    print()
    
    print("📁 生成的文件:")
    if report_file:
        print(f"  • 综合报告: {report_file}")
    if readme_file:
        print(f"  • 文档文件: {readme_file}")
    
    print()
    print("🛠️ 使用的工具:")
    print("  • 文件查看和编辑工具")
    print("  • Python执行环境")
    print("  • 数据分析算法")
    print("  • 报告生成系统")
    
    print()
    print(f"⏱️ 完成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

if __name__ == "__main__":
    main()