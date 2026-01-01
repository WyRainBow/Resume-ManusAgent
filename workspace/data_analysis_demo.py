#!/usr/bin/env python3
"""
综合数据分析演示
展示OpenManus的多工具协作能力
"""

import json
import csv
import os
from datetime import datetime
import random

def generate_sample_data(num_records=50):
    """生成示例数据集"""
    data = []
    categories = ['电子产品', '服装', '食品', '书籍', '家居用品']
    
    for i in range(1, num_records + 1):
        record = {
            'id': i,
            'product': f'产品{i:03d}',
            'category': random.choice(categories),
            'price': round(random.uniform(10.0, 500.0), 2),
            'quantity': random.randint(1, 100),
            'sales_date': f'2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}',
            'rating': round(random.uniform(1.0, 5.0), 1)
        }
        record['revenue'] = round(record['price'] * record['quantity'], 2)
        data.append(record)
    
    return data

def save_data_to_files(data):
    """将数据保存到不同格式的文件"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # 保存为JSON
    json_filename = f'sales_data_{timestamp}.json'
    with open(json_filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    
    # 保存为CSV
    csv_filename = f'sales_data_{timestamp}.csv'
    if data:
        fieldnames = data[0].keys()
        with open(csv_filename, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(data)
    
    return json_filename, csv_filename

def analyze_sales_data(data):
    """分析销售数据"""
    if not data:
        return {}
    
    analysis = {
        'summary': {
            'total_records': len(data),
            'date_range': {
                'start': min(record['sales_date'] for record in data),
                'end': max(record['sales_date'] for record in data)
            }
        },
        'financials': {
            'total_revenue': sum(record['revenue'] for record in data),
            'average_price': sum(record['price'] for record in data) / len(data),
            'total_quantity': sum(record['quantity'] for record in data)
        },
        'by_category': {},
        'top_products': []
    }
    
    # 按类别分析
    categories = {}
    for record in data:
        category = record['category']
        if category not in categories:
            categories[category] = {
                'count': 0,
                'total_revenue': 0,
                'total_quantity': 0,
                'avg_rating': 0
            }
        
        categories[category]['count'] += 1
        categories[category]['total_revenue'] += record['revenue']
        categories[category]['total_quantity'] += record['quantity']
        categories[category]['avg_rating'] += record['rating']
    
    for category, stats in categories.items():
        stats['avg_rating'] = stats['avg_rating'] / stats['count']
        analysis['by_category'][category] = stats
    
    # 找出最畅销的产品
    sorted_by_revenue = sorted(data, key=lambda x: x['revenue'], reverse=True)
    analysis['top_products'] = sorted_by_revenue[:5]
    
    # 计算统计指标
    prices = [record['price'] for record in data]
    quantities = [record['quantity'] for record in data]
    revenues = [record['revenue'] for record in data]
    ratings = [record['rating'] for record in data]
    
    analysis['statistics'] = {
        'price_stats': calculate_basic_stats(prices),
        'quantity_stats': calculate_basic_stats(quantities),
        'revenue_stats': calculate_basic_stats(revenues),
        'rating_stats': calculate_basic_stats(ratings)
    }
    
    return analysis

def calculate_basic_stats(numbers):
    """计算基本统计信息"""
    if not numbers:
        return {}
    
    return {
        'count': len(numbers),
        'sum': sum(numbers),
        'mean': sum(numbers) / len(numbers),
        'min': min(numbers),
        'max': max(numbers),
        'range': max(numbers) - min(numbers)
    }

def generate_visualization_code(data, analysis):
    """生成数据可视化代码"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    viz_filename = f'visualization_{timestamp}.py'
    
    viz_code = '''#!/usr/bin/env python3
"""
销售数据可视化脚本
自动生成的图表代码
"""

import matplotlib.pyplot as plt
import numpy as np
import json

# 数据准备
categories = {categories_data}
revenues_by_category = {revenues_data}
top_products = {top_products_data}

# 创建图表
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
fig.suptitle('销售数据分析图表', fontsize=16)

# 1. 按类别收入饼图
ax1 = axes[0, 0]
category_names = list(categories.keys())
category_revenues = [cat['total_revenue'] for cat in categories.values()]
ax1.pie(category_revenues, labels=category_names, autopct='%1.1f%%', startangle=90)
ax1.set_title('按类别收入分布')

# 2. 按类别收入柱状图
ax2 = axes[0, 1]
x_pos = np.arange(len(category_names))
ax2.bar(x_pos, category_revenues)
ax2.set_xticks(x_pos)
ax2.set_xticklabels(category_names, rotation=45)
ax2.set_title('按类别收入对比')
ax2.set_ylabel('收入')

# 3. 价格分布直方图
ax3 = axes[1, 0]
prices = [product['price'] for product in top_products]
product_names = [product['product'] for product in top_products]
ax3.bar(product_names, prices)
ax3.set_title('畅销产品价格')
ax3.set_ylabel('价格')
ax3.tick_params(axis='x', rotation=45)

# 4. 评分分布
ax4 = axes[1, 1]
ratings = [product['rating'] for product in top_products]
ax4.bar(product_names, ratings, color='green')
ax4.set_title('畅销产品评分')
ax4.set_ylabel('评分')
ax4.tick_params(axis='x', rotation=45)

plt.tight_layout()
plt.savefig('sales_analysis_charts.png', dpi=300, bbox_inches='tight')
print("图表已保存为 'sales_analysis_charts.png'")
plt.show()
'''
    
    # 准备数据
    categories_data = {}
    for category, stats in analysis['by_category'].items():
        categories_data[category] = {
            'total_revenue': stats['total_revenue'],
            'count': stats['count']
        }
    
    revenues_data = {}
    for category, stats in analysis['by_category'].items():
        revenues_data[category] = stats['total_revenue']
    
    top_products_data = analysis['top_products']
    
    # 替换模板中的占位符
    viz_code = viz_code.replace('{categories_data}', json.dumps(categories_data, indent=2))
    viz_code = viz_code.replace('{revenues_data}', json.dumps(revenues_data, indent=2))
    viz_code = viz_code.replace('{top_products_data}', json.dumps(top_products_data, indent=2))
    
    with open(viz_filename, 'w', encoding='utf-8') as f:
        f.write(viz_code)
    
    return viz_filename

def main():
    print("=== 综合数据分析演示 ===")
    print(f"开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 步骤1: 生成示例数据
    print("步骤1: 生成示例销售数据...")
    sample_data = generate_sample_data(50)
    print(f"已生成 {len(sample_data)} 条销售记录")
    
    # 步骤2: 保存数据到文件
    print("\n步骤2: 保存数据到文件...")
    json_file, csv_file = save_data_to_files(sample_data)
    print(f"JSON文件: {json_file}")
    print(f"CSV文件: {csv_file}")
    
    # 步骤3: 分析数据
    print("\n步骤3: 分析销售数据...")
    analysis = analyze_sales_data(sample_data)
    
    print(f"总记录数: {analysis['summary']['total_records']}")
    print(f"日期范围: {analysis['summary']['date_range']['start']} 到 {analysis['summary']['date_range']['end']}")
    print(f"总收入: ${analysis['financials']['total_revenue']:,.2f}")
    print(f"总销量: {analysis['financials']['total_quantity']} 件")
    print(f"平均价格: ${analysis['financials']['average_price']:.2f}")
    
    # 步骤4: 按类别显示结果
    print("\n步骤4: 按类别分析:")
    for category, stats in analysis['by_category'].items():
        print(f"  {category}:")
        print(f"    记录数: {stats['count']}")
        print(f"    收入: ${stats['total_revenue']:,.2f}")
        print(f"    销量: {stats['total_quantity']}")
        print(f"    平均评分: {stats['avg_rating']:.1f}/5.0")
    
    # 步骤5: 显示畅销产品
    print("\n步骤5: 最畅销产品:")
    for i, product in enumerate(analysis['top_products'], 1):
        print(f"  {i}. {product['product']} ({product['category']})")
        print(f"     价格: ${product['price']:.2f}, 销量: {product['quantity']}, 收入: ${product['revenue']:.2f}, 评分: {product['rating']}/5.0")
    
    # 步骤6: 生成可视化代码
    print("\n步骤6: 生成可视化代码...")
    viz_file = generate_visualization_code(sample_data, analysis)
    print(f"可视化脚本: {viz_file}")
    
    # 步骤7: 保存分析报告
    print("\n步骤7: 保存完整分析报告...")
    report = {
        'metadata': {
            'generated_at': datetime.now().isoformat(),
            'data_source': 'generated_sample',
            'records_count': len(sample_data)
        },
        'summary': analysis['summary'],
        'financial_summary': analysis['financials'],
        'category_analysis': analysis['by_category'],
        'top_products': analysis['top_products'],
        'statistics': analysis['statistics']
    }
    
    report_filename = f'sales_analysis_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    with open(report_filename, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"分析报告: {report_filename}")
    
    # 步骤8: 显示文件系统状态
    print("\n步骤8: 生成的文件列表:")
    files = os.listdir('.')
    data_files = [f for f in files if f.startswith('sales_') or f.startswith('visualization_')]
    for file in sorted(data_files):
        size = os.path.getsize(file)
        print(f"  {file} ({size:,} bytes)")
    
    print(f"\n总生成文件数: {len(data_files)}")
    print("\n=== 演示完成 ===")
    print("下一步建议:")
    print("1. 运行可视化脚本生成图表: python visualization_*.py")
    print("2. 使用Excel或数据分析工具打开CSV文件")
    print("3. 查看JSON报告获取详细分析结果")

if __name__ == "__main__":
    main()