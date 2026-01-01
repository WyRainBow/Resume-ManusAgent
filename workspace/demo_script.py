#!/usr/bin/env python3
"""
演示OpenManus能力的Python脚本
增强版：添加了数据可视化和文件操作功能
"""

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
    
    return stats

def fibonacci_sequence(n):
    """生成斐波那契数列"""
    sequence = []
    a, b = 0, 1
    for _ in range(n):
        sequence.append(a)
        a, b = b, a + b
    return sequence

def save_results_to_file(results, filename="results.txt"):
    """将结果保存到文件"""
    try:
        with open(filename, 'w') as f:
            f.write("=== 分析结果 ===\n\n")
            for key, value in results.items():
                if isinstance(value, (int, float)):
                    f.write(f"{key}: {value:.4f}\n")
                else:
                    f.write(f"{key}: {value}\n")
        print(f"结果已保存到文件: {filename}")
        return True
    except Exception as e:
        print(f"保存文件时出错: {e}")
        return False

def generate_data_visualization(data, title="数据分布"):
    """生成简单的文本可视化"""
    if not data:
        print("数据为空，无法生成可视化")
        return
    
    print(f"\n=== {title} ===")
    print("数据值: ", data)
    
    # 简单的文本直方图
    max_val = max(data)
    min_val = min(data)
    range_val = max_val - min_val
    
    if range_val > 0:
        print("\n文本直方图:")
        for value in data:
            bar_length = int((value - min_val) / range_val * 40)
            print(f"{value:4d}: {'█' * bar_length}")
    
    # 统计摘要
    stats = calculate_statistics(data)
    if stats:
        print("\n统计摘要:")
        for key, value in stats.items():
            print(f"  {key}: {value:.2f}")

def main():
    print("=== OpenManus增强版演示脚本 ===")
    print()
    
    # 演示统计计算
    sample_data = [23, 45, 67, 89, 12, 34, 56, 78, 90, 11]
    print(f"样本数据: {sample_data}")
    
    stats = calculate_statistics(sample_data)
    if stats:
        print("\n统计结果:")
        for key, value in stats.items():
            print(f"  {key}: {value:.2f}")
    
    print()
    
    # 演示斐波那契数列
    fib_count = 10
    fib_seq = fibonacci_sequence(fib_count)
    print(f"前{fib_count}个斐波那契数: {fib_seq}")
    
    print()
    
    # 演示新功能：数据可视化
    print("=== 数据可视化演示 ===")
    generate_data_visualization(sample_data, "样本数据可视化")
    
    print()
    
    # 演示新功能：文件保存
    print("=== 文件操作演示 ===")
    if stats:
        save_results_to_file(stats, "analysis_results.txt")
    
    print()
    
    # 演示文件系统信息
    import os
    current_dir = os.getcwd()
    print(f"当前工作目录: {current_dir}")
    
    # 列出当前目录文件
    files = os.listdir('.')
    print(f"目录中的文件: {files}")
    
    print("\n=== 演示完成 ===")

if __name__ == "__main__":
    main()