#!/usr/bin/env python3
"""
增强版OpenManus演示脚本
添加了更多功能和数据分析能力
"""

import math
import json
from datetime import datetime

def calculate_statistics(numbers):
    """计算基本统计信息"""
    if not numbers:
        return None
    
    stats = {
        'count': len(numbers),
        'sum': sum(numbers),
        'mean': sum(numbers) / len(numbers),
        'min': min(numbers),
        'max': max(numbers)
    }
    
    # 计算标准差
    mean = stats['mean']
    variance = sum((x - mean) ** 2 for x in numbers) / len(numbers)
    stats['std_dev'] = variance ** 0.5
    
    # 计算中位数
    sorted_numbers = sorted(numbers)
    n = len(sorted_numbers)
    if n % 2 == 0:
        stats['median'] = (sorted_numbers[n//2 - 1] + sorted_numbers[n//2]) / 2
    else:
        stats['median'] = sorted_numbers[n//2]
    
    return stats

def fibonacci_sequence(n):
    """生成斐波那契数列"""
    sequence = []
    a, b = 0, 1
    for _ in range(n):
        sequence.append(a)
        a, b = b, a + b
    return sequence

def analyze_file_system():
    """分析文件系统信息"""
    import os
    
    current_dir = os.getcwd()
    files = os.listdir('.')
    
    file_info = []
    for file in files:
        file_path = os.path.join(current_dir, file)
        if os.path.isfile(file_path):
            size = os.path.getsize(file_path)
            file_info.append({
                'name': file,
                'size_bytes': size,
                'size_kb': size / 1024,
                'type': 'file'
            })
        elif os.path.isdir(file_path):
            file_info.append({
                'name': file,
                'type': 'directory'
            })
    
    return {
        'current_directory': current_dir,
        'total_items': len(files),
        'items': file_info
    }

def generate_report(data, analysis_type="statistical"):
    """生成分析报告"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = {
        'report_type': analysis_type,
        'generated_at': timestamp,
        'data_summary': {
            'data_points': len(data) if isinstance(data, list) else 1,
            'data_type': type(data).__name__
        },
        'analysis_results': {}
    }
    
    if analysis_type == "statistical" and isinstance(data, list):
        stats = calculate_statistics(data)
        report['analysis_results']['statistics'] = stats
    
    return report

def main():
    print("=== 增强版OpenManus演示脚本 ===")
    print(f"执行时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 演示统计计算
    sample_data = [23, 45, 67, 89, 12, 34, 56, 78, 90, 11, 55, 33, 77, 22, 44]
    print(f"样本数据 ({len(sample_data)}个点): {sample_data}")
    
    stats = calculate_statistics(sample_data)
    if stats:
        print("\n详细统计结果:")
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"  {key}: {value:.4f}")
            else:
                print(f"  {key}: {value}")
    
    print()
    
    # 演示斐波那契数列
    fib_count = 15
    fib_seq = fibonacci_sequence(fib_count)
    print(f"前{fib_count}个斐波那契数: {fib_seq}")
    
    # 计算斐波那契数列的黄金比例近似
    if len(fib_seq) >= 3:
        ratios = []
        for i in range(2, len(fib_seq)):
            if fib_seq[i-1] != 0:
                ratio = fib_seq[i] / fib_seq[i-1]
                ratios.append(ratio)
        
        if ratios:
            avg_ratio = sum(ratios) / len(ratios)
            print(f"斐波那契相邻项比例平均值: {avg_ratio:.6f}")
            print(f"黄金比例(φ): {(1 + math.sqrt(5)) / 2:.6f}")
            print(f"与黄金比例的差异: {abs(avg_ratio - (1 + math.sqrt(5)) / 2):.6f}")
    
    print()
    
    # 演示文件系统分析
    print("=== 文件系统分析 ===")
    fs_info = analyze_file_system()
    print(f"当前目录: {fs_info['current_directory']}")
    print(f"总项目数: {fs_info['total_items']}")
    
    print("\n文件和目录列表:")
    for item in fs_info['items']:
        if item['type'] == 'file':
            print(f"  📄 {item['name']} ({item['size_kb']:.2f} KB)")
        else:
            print(f"  📁 {item['name']}")
    
    print()
    
    # 生成JSON报告
    report = generate_report(sample_data, "statistical")
    print("=== 生成的报告摘要 ===")
    print(f"报告类型: {report['report_type']}")
    print(f"生成时间: {report['generated_at']}")
    print(f"数据点: {report['data_summary']['data_points']}")
    
    # 保存报告到文件
    report_filename = f"analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_filename, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"\n详细报告已保存到: {report_filename}")
    print("\n=== 演示完成 ===")

if __name__ == "__main__":
    main()