#!/usr/bin/env python3
"""
工作空间分析脚本
分析当前目录中的文件并生成报告
"""

import os
import json
import sys
from datetime import datetime
from pathlib import Path

def get_file_info(filepath):
    """获取文件详细信息"""
    path = Path(filepath)
    stat = path.stat()
    
    info = {
        'name': path.name,
        'path': str(path),
        'type': 'file' if path.is_file() else 'directory',
        'size_bytes': stat.st_size if path.is_file() else 0,
        'created': datetime.fromtimestamp(stat.st_ctime).isoformat(),
        'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
    }
    
    if path.is_file():
        info['size_kb'] = info['size_bytes'] / 1024
        info['size_mb'] = info['size_kb'] / 1024
        info['extension'] = path.suffix.lower()
        
        # 根据扩展名判断文件类型
        ext = info['extension']
        if ext in ['.py', '.txt', '.md', '.json', '.csv', '.xml', '.html', '.css', '.js']:
            info['content_type'] = 'text'
        elif ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']:
            info['content_type'] = 'image'
        elif ext in ['.pdf', '.doc', '.docx']:
            info['content_type'] = 'document'
        else:
            info['content_type'] = 'other'
    
    return info

def analyze_workspace(workspace_path):
    """分析工作空间"""
    print("=" * 60)
    print("工作空间分析报告")
    print("=" * 60)
    
    path = Path(workspace_path)
    if not path.exists():
        print(f"错误: 路径不存在: {workspace_path}")
        return None
    
    print(f"分析时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"工作空间: {workspace_path}")
    print()
    
    # 收集所有文件和目录
    all_items = []
    for item in path.iterdir():
        all_items.append(get_file_info(item))
    
    # 排序：先目录后文件，按名称排序
    all_items.sort(key=lambda x: (0 if x['type'] == 'directory' else 1, x['name'].lower()))
    
    # 显示文件列表
    print("📁 文件和目录列表:")
    print("-" * 60)
    
    for item in all_items:
        if item['type'] == 'directory':
            print(f"  📁 {item['name']}/")
        else:
            size_str = f"{item['size_kb']:.1f} KB" if item['size_kb'] < 1024 else f"{item['size_mb']:.2f} MB"
            print(f"  📄 {item['name']} ({size_str})")
    
    print("-" * 60)
    
    # 统计信息
    files = [item for item in all_items if item['type'] == 'file']
    directories = [item for item in all_items if item['type'] == 'directory']
    
    total_size = sum(f['size_bytes'] for f in files)
    total_size_kb = total_size / 1024
    total_size_mb = total_size_kb / 1024
    
    # 按扩展名分组
    extensions = {}
    for f in files:
        ext = f.get('extension', '无扩展名')
        extensions[ext] = extensions.get(ext, 0) + 1
    
    # 按内容类型分组
    content_types = {}
    for f in files:
        ctype = f.get('content_type', 'unknown')
        content_types[ctype] = content_types.get(ctype, 0) + 1
    
    print("\n📊 统计摘要:")
    print(f"  • 文件总数: {len(files)}")
    print(f"  • 目录总数: {len(directories)}")
    print(f"  • 总大小: {total_size:,} bytes ({total_size_kb:.1f} KB, {total_size_mb:.2f} MB)")
    
    if extensions:
        print(f"\n  • 文件类型分布:")
        for ext, count in sorted(extensions.items()):
            print(f"      {ext}: {count} 个")
    
    if content_types:
        print(f"\n  • 内容类型分布:")
        for ctype, count in sorted(content_types.items()):
            print(f"      {ctype}: {count} 个")
    
    # 构建分析报告
    report = {
        'analysis_time': datetime.now().isoformat(),
        'workspace_path': str(path),
        'summary': {
            'total_files': len(files),
            'total_directories': len(directories),
            'total_size_bytes': total_size,
            'total_size_kb': total_size_kb,
            'total_size_mb': total_size_mb,
        },
        'file_types': extensions,
        'content_types': content_types,
        'items': all_items
    }
    
    return report

def save_report(report, filename=None):
    """保存分析报告"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"workspace_analysis_{timestamp}.json"
    
    report_path = Path(filename)
    
    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ 分析报告已保存到: {report_path}")
    print(f"   文件大小: {report_path.stat().st_size:,} bytes")
    
    return str(report_path)

def main():
    """主函数"""
    # 使用当前脚本所在目录作为工作空间
    workspace_path = Path(__file__).parent
    
    print("开始分析工作空间...")
    print(f"工作空间路径: {workspace_path}")
    print()
    
    # 执行分析
    report = analyze_workspace(workspace_path)
    
    if report:
        # 保存报告
        report_file = save_report(report)
        
        print("\n" + "=" * 60)
        print("分析完成!")
        print("=" * 60)
        
        # 显示报告摘要
        print(f"\n报告摘要:")
        print(f"  • 分析时间: {report['analysis_time']}")
        print(f"  • 分析项目: {report['summary']['total_files']} 个文件, {report['summary']['total_directories']} 个目录")
        print(f"  • 总大小: {report['summary']['total_size_mb']:.2f} MB")
        
        # 显示最大的3个文件
        files = [item for item in report['items'] if item['type'] == 'file']
        if files:
            largest_files = sorted(files, key=lambda x: x['size_bytes'], reverse=True)[:3]
            print(f"\n  • 最大的3个文件:")
            for i, f in enumerate(largest_files, 1):
                size_mb = f['size_bytes'] / 1024 / 1024
                print(f"      {i}. {f['name']} ({size_mb:.2f} MB)")

if __name__ == "__main__":
    main()