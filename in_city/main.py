
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
主控脚本
按顺序执行整个数据处理和可视化流程：
1. XLS/XLSX to CSV: 将原始数据从Excel格式转换为CSV格式。
2. CSV Classification: 对CSV数据进行分类和标准化处理。
3. City to Mesh: 为每个城市生成H3网格。
4. POI to Hex Allocation: 将POI数据分配到对应的H3网格中。
5. Mart Hex Aggregation: 分析包含商场的Hex及其邻近区域。
6. Visualization: 生成POI密度图和商场Hex分析图。
"""

import os
import glob
import sys

# 将当前目录添加到系统路径，以便导入其他模块
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 导入各个处理模块
try:
    import xlsx_to_csv
    import csv_converter
    import city_to_mesh
    import poi_hex
    import mart_mesh
    import json_visualization
    import mart_hex_visualize
except ImportError as e:
    print(f"错误：无法导入必要的模块: {e}")
    print("请确保所有必需的 .py 文件 (xlsx_to_csv.py, csv_converter.py, etc.) 都存在于脚本目录中。")
    sys.exit(1)

def main():
    """主函数，按顺序执行所有处理步骤"""
    print("🚀 开始执行数据处理与可视化流程...\n")
    
    # 定义项目根目录和关键子目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    xlsx_dir = os.path.join(base_dir, 'xlsx')
    # csv_unclassified_dir 在 csv_converter.py 中硬编码，这里不需定义
    # csv_classified_dir 在多个模块中硬编码，这里不需定义
    json_dir = os.path.join(base_dir, 'json')
    mart_analysis_dir = os.path.join(base_dir, 'mart_hex_analysis')
    html_dir = os.path.join(base_dir, 'html')

    # --- 步骤 1: 执行数据转换 (XLS -> CSV) ---
    print("--- 步骤 1 of 6: XLS/XLSX to CSV 数据转换 ---")
    # 注意: xlsx_to_csv.py 的函数 process_all_xlsx() 内部硬编码了路径
    xlsx_to_csv.process_all_xlsx()
    print("✅ 步骤 1 完成\n")

    # --- 步骤 2: 进行数据分类 ---
    print("--- 步骤 2 of 6: CSV 数据分类 ---")
    # 注意: csv_converter.py 的函数 process_unclassified_csv() 内部硬编码了路径
    csv_converter.process_unclassified_csv()
    print("✅ 步骤 2 完成\n")

    # --- 步骤 3: 城市网格划分 ---
    print("--- 步骤 3 of 6: 城市网格划分 (City to Mesh) ---")
    # 注意: city_to_mesh.py 的函数 process_cities() 内部硬编码了路径
    city_to_mesh.process_cities()
    print("✅ 步骤 3 完成\n")

    # --- 步骤 4: POI数据分配 ---
    print("--- 步骤 4 of 6: POI 数据分配 (POI to Hex) ---")
    # 注意: poi_hex.py 的函数 process_all_cities() 内部硬编码了路径
    poi_hex.process_all_cities()
    print("✅ 步骤 4 完成\n")

    # --- 步骤 5: Mart Hex 信息聚合 ---
    print("--- 步骤 5 of 6: 商场 Hex 信息聚合 (Mart Mesh) ---")
    mart_mesh.process_cities(json_dir, mart_analysis_dir)
    print("✅ 步骤 5 完成\n")

    # --- 步骤 6: 可视化 ---
    print("--- 步骤 6 of 6: 生成可视化图表 ---")
    
    # 6.1 城市POI密度可视化
    print("  -> 6.1: 生成POI密度分布图...")
    json_visualization.visualize_all_cities(json_dir, html_dir)
    
    # 6.2 城市商场Hex可视化
    print("  -> 6.2: 生成商场Hex分析图...")
    mart_analysis_files = glob.glob(os.path.join(mart_analysis_dir, '*_mart_hex_analysis.json'))
    if not mart_analysis_files:
        print("    - 未找到商场Hex分析文件，跳过可视化。")
    else:
        for json_path in mart_analysis_files:
            city_name = os.path.basename(json_path).replace('_mart_hex_analysis.json', '')
            print(f"    - 正在处理城市: {city_name}")
            mart_hex_visualize.visualize_mart_hex_analysis(json_path, base_dir)
            
    print("✅ 步骤 6 完成\n")
    
    print("🎉🎉🎉 所有流程执行完毕！ 🎉🎉🎉")

if __name__ == "__main__":
    main()
