import json
import pandas as pd

def analyze_city_data():
    """分析城市数据的统计信息"""
    
    # 读取JSON文件
    with open('city_indicators.json', 'r', encoding='utf-8') as f:
        city_data = json.load(f)
    
    print("=== 城市指标数据汇总分析 ===\n")
    
    print(f"总城市数量: {len(city_data)}")
    
    # 统计各指标的数据完整性
    indicators = {
        'GDP (亿元)': 'GDP',
        '人均GDP (元)': '人均GDP', 
        'GDP增长率 (%)': 'GDP增长率',
        '常住人口 (万人)': '常住人口',
        '城镇化率 (%)': '城镇化率',
        '地方一般公共预算收入 (万元)': '地方一般公共预算收入',
        '地方一般公共预算支出 (万元)': '地方一般公共预算支出',
        '社会消费品零售总额 (万元)': '社会消费品零售总额',
        '限额以上单位商品零售额 (万元)': '限额以上单位商品零售额',
        '限额以上批发零售业商品销售总额 (万元)': '限额以上批发零售业商品销售总额',
        '规模以上服务业营业收入 (万元)': '规模以上服务业营业收入',
        '规模以上服务业营业收入增速 (%)': '规模以上服务业营业收入增速'
    }
    
    print("\n=== 数据完整性统计 ===")
    for key, name in indicators.items():
        count = sum(1 for city_data_item in city_data.values() 
                   if city_data_item.get(key) is not None)
        percentage = (count / len(city_data)) * 100
        print(f"{name}: {count}/{len(city_data)} ({percentage:.1f}%)")
    
    # 显示一些主要城市的数据
    major_cities = ['北京市', '上海市', '广州市', '深圳市', '成都市', '杭州市']
    
    print(f"\n=== 主要城市数据示例 ===")
    for city in major_cities:
        if city in city_data:
            print(f"\n{city}:")
            data = city_data[city]
            print(f"  GDP: {data.get('GDP (亿元)', 'N/A')} 亿元")
            print(f"  人均GDP: {data.get('人均GDP (元)', 'N/A')} 元")
            print(f"  常住人口: {data.get('常住人口 (万人)', 'N/A')} 万人")
            print(f"  城镇化率: {data.get('城镇化率 (%)', 'N/A')}%")
    
    # 按照MD文件的六个主要指标分类显示
    print(f"\n=== 按照city.md中定义的六大指标分类 ===")
    
    print("\n1. 地区生产总值指标:")
    print("   - GDP (亿元)")
    print("   - 人均GDP (元)")
    print("   - GDP增长率 (%)")
    
    print("\n2. 地方一般公共服务指标:")
    print("   - 地方一般公共预算收入 (万元)")
    print("   - 地方一般公共预算支出 (万元)")
    
    print("\n3. 人口数指标:")
    print("   - 常住人口 (万人)")
    print("   - 城镇化率 (%)")
    
    print("\n4. 社会消费品零售总额指标:")
    print("   - 社会消费品零售总额 (万元)")
    print("   - 限额以上单位商品零售额 (万元)")
    print("   - 限额以上批发零售业商品销售总额 (万元)")
    
    print("\n5. 规模以上服务业营业收入及增速指标:")
    print("   - 规模以上服务业营业收入 (万元)")
    print("   - 规模以上服务业营业收入增速 (%)")
    
    # 统计各省份城市数量
    provinces = {}
    for city in city_data.keys():
        if '省' in city:
            continue
        # 简单的省份推断（基于城市名称特点）
        if city in ['北京市', '上海市', '天津市', '重庆市']:
            prov = '直辖市'
        else:
            prov = '其他省份'
        provinces[prov] = provinces.get(prov, 0) + 1
    
    print(f"\n=== 城市分布 ===")
    for prov, count in provinces.items():
        print(f"{prov}: {count}个城市")
    
    print(f"\n数据文件已生成: city_indicators.json")
    print(f"文件大小: {len(str(city_data))} 字符")

if __name__ == "__main__":
    analyze_city_data()
