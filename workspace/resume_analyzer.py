#!/usr/bin/env python3
"""
简历分析工具
分析简历文件，提取关键信息，生成分析报告
"""

import re
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Set, Any

class ResumeAnalyzer:
    """简历分析器"""
    
    def __init__(self, resume_path: str):
        self.resume_path = Path(resume_path)
        self.content = ""
        self.analysis_result = {}
        
        # 技术栈分类
        self.tech_categories = {
            'programming_languages': {'Java', 'Python', 'C++', 'Go', 'JavaScript', 'TypeScript', 'Rust', 'Scala', 'Kotlin'},
            'backend_frameworks': {'Spring Boot', 'Spring Cloud', 'Django', 'Flask', 'Express.js', 'Gin', 'Dubbo', 'gRPC'},
            'databases': {'MySQL', 'PostgreSQL', 'Redis', 'MongoDB', 'Elasticsearch', 'TiDB', 'HBase'},
            'middleware': {'Kafka', 'RabbitMQ', 'RocketMQ', 'Pulsar', 'Nacos', 'Consul'},
            'cloud_platforms': {'AWS', '阿里云', '腾讯云', 'Google Cloud Platform'},
            'container_tools': {'Docker', 'Kubernetes', 'Helm', 'Istio'},
            'monitoring_tools': {'Prometheus', 'Grafana', 'ELK Stack', 'SkyWalking', 'Zipkin', 'Jaeger'},
            'devops_tools': {'Git', 'Maven', 'Gradle', 'Jenkins', 'GitLab CI/CD', 'Jira', 'Confluence'},
            'arch_methods': {'DDD', 'EDA', 'Clean Architecture', 'Hexagonal Architecture', 'CQRS', 'Saga'}
        }
        
    def load_resume(self) -> bool:
        """加载简历文件"""
        try:
            with open(self.resume_path, 'r', encoding='utf-8') as f:
                self.content = f.read()
            return True
        except Exception as e:
            print(f"加载简历文件失败: {e}")
            return False
    
    def extract_sections(self) -> Dict[str, str]:
        """提取简历各部分内容"""
        sections = {}
        
        # 使用正则表达式提取章节
        section_pattern = r'^##\s+(.+?)$\n(.*?)(?=^##|\Z)'
        matches = re.findall(section_pattern, self.content, re.MULTILINE | re.DOTALL)
        
        for title, content in matches:
            sections[title.strip()] = content.strip()
        
        return sections
    
    def extract_basic_info(self) -> Dict[str, str]:
        """提取基本信息"""
        basic_info = {}
        
        # 查找基本信息部分
        basic_pattern = r'##\s+基本信息\s*\n(.*?)(?=^##|\Z)'
        match = re.search(basic_pattern, self.content, re.MULTILINE | re.DOTALL)
        
        if match:
            basic_text = match.group(1)
            # 提取键值对
            lines = basic_text.strip().split('\n')
            for line in lines:
                if '**' in line:
                    # 提取键和值
                    key_match = re.search(r'\*\*(.+?)\*\*', line)
                    if key_match:
                        key = key_match.group(1).strip()
                        # 提取值（去掉键后的部分）
                        value = line.replace(f'**{key}**', '').strip(' ：:')
                        basic_info[key] = value
        
        return basic_info
    
    def extract_skills(self) -> Dict[str, List[str]]:
        """提取技能信息"""
        skills = {category: [] for category in self.tech_categories.keys()}
        skills['other'] = []
        
        # 查找专业技能部分
        skills_pattern = r'##\s+专业技能\s*\n(.*?)(?=^##|\Z)'
        match = re.search(skills_pattern, self.content, re.MULTILINE | re.DOTALL)
        
        if match:
            skills_text = match.group(1)
            
            # 提取所有提到的技术
            all_techs = set()
            for category, tech_set in self.tech_categories.items():
                for tech in tech_set:
                    if tech in skills_text:
                        skills[category].append(tech)
                        all_techs.add(tech)
            
            # 提取其他技术（不在预定义分类中的）
            # 查找技术列表项
            tech_items = re.findall(r'[-*]\s+(.+?)[：:,]', skills_text)
            for item in tech_items:
                # 分割技术项
                item_techs = re.split(r'[、,，]', item)
                for tech in item_techs:
                    tech = tech.strip()
                    if tech and tech not in all_techs:
                        # 检查是否属于某个分类
                        categorized = False
                        for category, tech_set in self.tech_categories.items():
                            if tech in tech_set:
                                skills[category].append(tech)
                                categorized = True
                                break
                        
                        if not categorized and tech not in skills['other']:
                            skills['other'].append(tech)
        
        # 去重
        for category in skills:
            skills[category] = list(set(skills[category]))
        
        return skills
    
    def extract_projects(self) -> List[Dict[str, Any]]:
        """提取项目经验"""
        projects = []
        
        # 查找项目经验部分
        projects_pattern = r'###\s+项目[一二三四五六七八九十\d]+[：:]\s*(.+?)$\n(.*?)(?=^###|\Z)'
        matches = re.findall(projects_pattern, self.content, re.MULTILINE | re.DOTALL)
        
        for project_title, project_content in matches:
            project = {
                'title': project_title.strip(),
                'content': project_content.strip()
            }
            
            # 提取项目详细信息
            # 时间
            time_match = re.search(r'时间[：:]\s*(.+?)$', project_content, re.MULTILINE)
            if time_match:
                project['time'] = time_match.group(1).strip()
            
            # 角色
            role_match = re.search(r'角色[：:]\s*(.+?)$', project_content, re.MULTILINE)
            if role_match:
                project['role'] = role_match.group(1).strip()
            
            # 技术栈
            tech_match = re.search(r'技术栈[：:]\s*(.+?)$', project_content, re.MULTILINE)
            if tech_match:
                project['tech_stack'] = [t.strip() for t in tech_match.group(1).strip().split(',')]
            
            # 提取成果（数字指标）
            achievements = []
            number_pattern = r'(\d+[\d,\.]*)\s*(万?\+?|ms|秒?|%|倍|个)'
            number_matches = re.findall(number_pattern, project_content)
            
            for num, unit in number_matches:
                achievements.append(f"{num}{unit}")
            
            if achievements:
                project['achievements'] = achievements
            
            projects.append(project)
        
        return projects
    
    def analyze_structure(self) -> Dict[str, Any]:
        """分析简历结构"""
        sections = self.extract_sections()
        
        structure_analysis = {
            'total_sections': len(sections),
            'section_names': list(sections.keys()),
            'section_lengths': {name: len(content) for name, content in sections.items()},
            'total_length': len(self.content),
            'line_count': self.content.count('\n') + 1,
            'word_count': len(re.findall(r'\b\w+\b', self.content))
        }
        
        return structure_analysis
    
    def calculate_skill_score(self, skills: Dict[str, List[str]]) -> Dict[str, Any]:
        """计算技能评分"""
        total_skills = sum(len(skill_list) for skill_list in skills.values())
        
        score_analysis = {
            'total_skills': total_skills,
            'category_counts': {category: len(skill_list) for category, skill_list in skills.items()},
            'skill_diversity': len([c for c, s in skills.items() if s]) / len(skills) * 100,
            'programming_languages_count': len(skills.get('programming_languages', [])),
            'backend_frameworks_count': len(skills.get('backend_frameworks', [])),
            'databases_count': len(skills.get('databases', [])),
            'cloud_platforms_count': len(skills.get('cloud_platforms', []))
        }
        
        return score_analysis
    
    def generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """生成改进建议"""
        recommendations = []
        
        # 基于结构分析的建议
        structure = analysis.get('structure', {})
        if structure.get('total_length', 0) < 1000:
            recommendations.append("简历内容较短，建议增加更多详细的工作经验和项目描述")
        
        # 基于技能分析的建议
        skills = analysis.get('skills', {})
        skill_score = analysis.get('skill_score', {})
        
        if skill_score.get('programming_languages_count', 0) < 3:
            recommendations.append("编程语言技能较少，建议学习或展示更多编程语言经验")
        
        if skill_score.get('cloud_platforms_count', 0) < 2:
            recommendations.append("云平台经验较少，建议增加AWS/Azure/GCP等云平台经验")
        
        # 基于项目分析的建议
        projects = analysis.get('projects', [])
        if len(projects) < 2:
            recommendations.append("项目经验较少，建议增加更多有代表性的项目案例")
        
        # 通用建议
        recommendations.extend([
            "确保所有联系信息都已填写完整",
            "量化项目成果，使用具体数字说明贡献",
            "定期更新技术栈，保持与市场需求的同步",
            "考虑添加GitHub项目链接或技术博客链接"
        ])
        
        return recommendations
    
    def analyze(self) -> Dict[str, Any]:
        """执行完整分析"""
        if not self.load_resume():
            return {}
        
        print("开始分析简历...")
        print(f"简历文件: {self.resume_path.name}")
        print()
        
        # 执行各项分析
        basic_info = self.extract_basic_info()
        skills = self.extract_skills()
        projects = self.extract_projects()
        structure = self.analyze_structure()
        skill_score = self.calculate_skill_score(skills)
        
        # 构建分析结果
        self.analysis_result = {
            'analysis_time': datetime.now().isoformat(),
            'resume_file': str(self.resume_path),
            'basic_info': basic_info,
            'skills': skills,
            'projects': projects,
            'structure': structure,
            'skill_score': skill_score
        }
        
        return self.analysis_result
    
    def print_summary(self):
        """打印分析摘要"""
        if not self.analysis_result:
            print("未找到分析结果，请先执行analyze()方法")
            return
        
        print("=" * 60)
        print("简历分析摘要")
        print("=" * 60)
        
        # 基本信息
        basic_info = self.analysis_result.get('basic_info', {})
        if basic_info:
            print("\n📋 基本信息:")
            for key, value in basic_info.items():
                print(f"  {key}: {value}")
        
        # 技能统计
        skill_score = self.analysis_result.get('skill_score', {})
        if skill_score:
            print(f"\n💻 技能统计:")
            print(f"  总技能数: {skill_score.get('total_skills', 0)}")
            print(f"  编程语言: {skill_score.get('programming_languages_count', 0)} 种")
            print(f"  后端框架: {skill_score.get('backend_frameworks_count', 0)} 种")
            print(f"  数据库: {skill_score.get('databases_count', 0)} 种")
            print(f"  云平台: {skill_score.get('cloud_platforms_count', 0)} 种")
        
        # 项目经验
        projects = self.analysis_result.get('projects', [])
        if projects:
            print(f"\n🚀 项目经验: {len(projects)} 个")
            for i, project in enumerate(projects, 1):
                print(f"  {i}. {project.get('title', '未命名项目')}")
                if 'role' in project:
                    print(f"     角色: {project['role']}")
        
        # 结构分析
        structure = self.analysis_result.get('structure', {})
        if structure:
            print(f"\n📊 结构分析:")
            print(f"  总字数: {structure.get('word_count', 0)}")
            print(f"  总行数: {structure.get('line_count', 0)}")
            print(f"  章节数: {structure.get('total_sections', 0)}")
        
        print("\n" + "=" * 60)
    
    def save_report(self, output_path: str = None):
        """保存分析报告"""
        if not self.analysis_result:
            print("未找到分析结果，请先执行analyze()方法")
            return
        
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"resume_analysis_{timestamp}.json"
        
        output_file = Path(output_path)
        
        # 添加改进建议
        recommendations = self.generate_recommendations(self.analysis_result)
        self.analysis_result['recommendations'] = recommendations
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(self.analysis_result, f, indent=2, ensure_ascii=False)
            
            print(f"✅ 分析报告已保存到: {output_file}")
            print(f"   文件大小: {output_file.stat().st_size:,} bytes")
            
            # 打印建议
            if recommendations:
                print("\n💡 改进建议:")
                for i, rec in enumerate(recommendations, 1):
                    print(f"  {i}. {rec}")
            
            return str(output_file)
            
        except Exception as e:
            print(f"保存报告失败: {e}")
            return None

def main():
    """主函数"""
    # 简历文件路径
    resume_file = "朱兆武_简历.md"
    resume_path = Path(__file__).parent / resume_file
    
    if not resume_path.exists():
        print(f"错误: 找不到简历文件: {resume_file}")
        return
    
    print("简历分析工具")
    print("=" * 60)
    
    # 创建分析器
    analyzer = ResumeAnalyzer(resume_path)
    
    # 执行分析
    analysis_result = analyzer.analyze()
    
    if analysis_result:
        # 打印摘要
        analyzer.print_summary()
        
        # 保存报告
        report_file = analyzer.save_report()
        
        if report_file:
            print(f"\n📁 报告文件: {report_file}")
            print("分析完成!")
        else:
            print("分析完成，但保存报告失败")
    else:
        print("简历分析失败")

if __name__ == "__main__":
    main()