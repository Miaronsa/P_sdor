import pandas as pd
import json
import os
import re

def clean_city_name(city_name):
    """清理城市名称，去除多余字符"""
    if pd.isna(city_name) or city_name == '':
        return None
    
    # 去除前导空格和特殊标记
    city_name = str(city_name).strip()
    if city_name.startswith('  '):
        city_name = city_name.strip()
    
    # 提取城市名称（去除英文名称部分）
    city_match = re.match(r'^([^,]+)', city_name)
    if city_match:
        city_name = city_match.group(1).strip()
    
    # 过滤掉省份名称等不需要的行
    if any(keyword in city_name for keyword in ['省', 'Province', '自治区', '直辖市', '特别行政区']):
        return None
    
    return city_name

def extract_numeric_value(value):
    """提取数值，处理空值和非数值情况"""
    if pd.isna(value) or value == '' or value == ',' or str(value).strip() == '':
        return None
    
    try:
        # 尝试直接转换为浮点数
        return float(value)
    except (ValueError, TypeError):
        return None

def process_csv_files():
    """处理所有CSV文件，按城市整合数据"""
    
    # 使用绝对路径确保文件能正确找到
    csv_dir = r'e:\Deskep\Final\city\csv'
    city_data = {}
    
    # 定义文件映射和对应的指标字段
    file_mapping = {
        '地区生产总值.csv': {
            'gdp': 'GDP (亿元)',
            'gdp_per_capita': '人均GDP (元)', 
            'gdp_growth': 'GDP增长率 (%)'
        },
        '人口数.csv': {
            'population': '常住人口 (万人)',
            'urbanization_rate': '城镇化率 (%)'
        },
        '地方一般公共预算收支状况.csv': {
            'public_revenue': '地方一般公共预算收入 (万元)',
            'public_expenditure': '地方一般公共预算支出 (万元)'
        },
        '社会消费品零售总额及批发零售贸易业情况.csv': {
            'retail_sales': '社会消费品零售总额 (万元)',
            'designated_retail': '限额以上单位商品零售额 (万元)',
            'wholesale_retail_sales': '限额以上批发零售业商品销售总额 (万元)'
        },
        '规模以上服务业营业收入及增速.csv': {
            'service_revenue': '规模以上服务业营业收入 (万元)',
            'service_growth': '规模以上服务业营业收入增速 (%)'
        }
    }
    
    # 处理每个CSV文件
    for filename, indicators in file_mapping.items():
        filepath = os.path.join(csv_dir, filename)
        print(f"正在处理文件: {filename}")
        print(f"文件路径: {filepath}")
        
        # 检查文件是否存在
        if not os.path.exists(filepath):
            print(f"警告：文件不存在: {filepath}")
            continue
            
        try:
            df = pd.read_csv(filepath, encoding='utf-8')
        except UnicodeDecodeError:
            try:
                df = pd.read_csv(filepath, encoding='gbk')
            except Exception as e:
                print(f"读取文件失败: {filename}, 错误: {e}")
                continue
        except Exception as e:
            print(f"读取文件失败: {filename}, 错误: {e}")
            continue
        
        # 根据不同文件的结构处理数据
        if filename == '地区生产总值.csv':
            # GDP文件结构
            city_col = 'Unnamed: 0'
            gdp_col = 'Unnamed: 2'  # 全市GDP
            per_capita_col = 'Unnamed: 4'  # 全市人均GDP
            growth_col = 'Unnamed: 6'  # 全市增长率
            
            for idx, row in df.iterrows():
                city_name = clean_city_name(row[city_col])
                if city_name:
                    if city_name not in city_data:
                        city_data[city_name] = {}
                    
                    city_data[city_name]['GDP (亿元)'] = extract_numeric_value(row[gdp_col])
                    city_data[city_name]['人均GDP (元)'] = extract_numeric_value(row[per_capita_col])
                    city_data[city_name]['GDP增长率 (%)'] = extract_numeric_value(row[growth_col])
        
        elif filename == '人口数.csv':
            # 人口文件结构
            city_col = 'Unnamed: 0'
            pop_col = 'Unnamed: 2'  # 全市人口
            urban_col = 'Unnamed: 4'  # 城镇化率
            
            for idx, row in df.iterrows():
                city_name = clean_city_name(row[city_col])
                if city_name:
                    if city_name not in city_data:
                        city_data[city_name] = {}
                    
                    city_data[city_name]['常住人口 (万人)'] = extract_numeric_value(row[pop_col])
                    city_data[city_name]['城镇化率 (%)'] = extract_numeric_value(row[urban_col])
        
        elif filename == '地方一般公共预算收支状况.csv':
            # 财政文件结构
            city_col = 'Unnamed: 0'
            revenue_col = 'Unnamed: 2'
            expenditure_col = 'Unnamed: 3'
            
            for idx, row in df.iterrows():
                city_name = clean_city_name(row[city_col])
                if city_name:
                    if city_name not in city_data:
                        city_data[city_name] = {}
                    
                    city_data[city_name]['地方一般公共预算收入 (万元)'] = extract_numeric_value(row[revenue_col])
                    city_data[city_name]['地方一般公共预算支出 (万元)'] = extract_numeric_value(row[expenditure_col])
        
        elif filename == '社会消费品零售总额及批发零售贸易业情况.csv':
            # 消费文件结构
            city_col = 'Unnamed: 0'
            retail_col = 'Unnamed: 2'  # 全市社会消费品零售总额
            designated_col = 'Unnamed: 4'  # 全市限额以上单位商品零售额
            wholesale_col = 'Unnamed: 6'  # 全市限额以上批发零售业商品销售总额
            
            for idx, row in df.iterrows():
                city_name = clean_city_name(row[city_col])
                if city_name:
                    if city_name not in city_data:
                        city_data[city_name] = {}
                    
                    city_data[city_name]['社会消费品零售总额 (万元)'] = extract_numeric_value(row[retail_col])
                    city_data[city_name]['限额以上单位商品零售额 (万元)'] = extract_numeric_value(row[designated_col])
                    city_data[city_name]['限额以上批发零售业商品销售总额 (万元)'] = extract_numeric_value(row[wholesale_col])
        
        elif filename == '规模以上服务业营业收入及增速.csv':
            # 服务业文件结构
            city_col = 'Unnamed: 0'
            revenue_col = 'Unnamed: 2'  # 全市规模以上服务业营业收入
            growth_col = 'Unnamed: 4'  # 全市规模以上服务业营业收入增速
            
            for idx, row in df.iterrows():
                city_name = clean_city_name(row[city_col])
                if city_name:
                    if city_name not in city_data:
                        city_data[city_name] = {}
                    
                    city_data[city_name]['规模以上服务业营业收入 (万元)'] = extract_numeric_value(row[revenue_col])
                    city_data[city_name]['规模以上服务业营业收入增速 (%)'] = extract_numeric_value(row[growth_col])
    
    # 过滤掉没有有效数据的城市
    filtered_city_data = {}
    for city_name, data in city_data.items():
        # 检查是否有至少一个非空的数值
        has_data = any(value is not None for value in data.values())
        if has_data and city_name:
            filtered_city_data[city_name] = data
    
    return filtered_city_data

def save_to_json(city_data, output_file='e:/Deskep/Final/city/json/city_indicators.json'):

    """保存数据到JSON文件"""
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(city_data, f, ensure_ascii=False, indent=2)
        print(f"数据已成功保存到 {output_file}")
        print(f"共处理了 {len(city_data)} 个城市的数据")
    except Exception as e:
        print(f"保存文件时出错: {e}")

def main():
    """主函数"""
    print("开始处理城市指标数据...")
    
    # 处理CSV文件
    city_data = process_csv_files()
    
    # 显示处理结果摘要
    print(f"\n处理完成！共收集了 {len(city_data)} 个城市的数据")
    
    # 显示前几个城市的数据作为示例
    print("\n前5个城市的数据示例:")
    for i, (city_name, data) in enumerate(city_data.items()):
        if i >= 5:
            break
        print(f"\n{city_name}:")
        for indicator, value in data.items():
            print(f"  {indicator}: {value}")
    
    # 保存到JSON文件
    save_to_json(city_data)

if __name__ == "__main__":
    main()