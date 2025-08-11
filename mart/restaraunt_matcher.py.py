import json
import csv
import os
from difflib import SequenceMatcher

# 读取 JSON 文件
def read_json(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

# 读取 CSV 文件
def read_csv(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        return list(reader)

# 写入更新后的 JSON 文件
def write_json(file_path, data):
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# 计算字符串相似度
def similarity(a, b):
    return SequenceMatcher(None, a, b).ratio()

# 根据城市匹配经纬度
def match_coordinates_by_city(json_data, csv_dir):
    # 获取所有可用的城市CSV文件
    csv_files = [f for f in os.listdir(csv_dir) if f.endswith('.csv')]
    
    # 创建城市名到CSV文件的映射
    city_csv_map = {}
    for csv_file in csv_files:
        city_name = csv_file.replace('.csv', '')
        city_csv_map[city_name] = os.path.join(csv_dir, csv_file)
    
    print(f"找到 {len(city_csv_map)} 个城市的CSV文件: {list(city_csv_map.keys())}")
    
    matched_count = 0
    total_count = len(json_data)
    
    for i, shop in enumerate(json_data):
        if i % 100 == 0:  # 每处理100个店铺打印一次进度
            print(f"处理进度: {i}/{total_count}")
        
        city = shop.get("城市", "")
        mall_name = shop.get("商场名称", "")
        location_desc = shop.get("店铺位置", "")
        
        # 清理城市名（去除"市"、"区"、"县"等后缀）
        clean_city = city.replace("市", "").replace("区", "").replace("县", "")
        
        # 查找匹配的城市CSV文件
        csv_file_path = None
        for city_name, csv_path in city_csv_map.items():
            if clean_city in city_name or city_name in clean_city:
                csv_file_path = csv_path
                break
        
        if csv_file_path:
            # 读取对应城市的CSV文件
            csv_data = read_csv(csv_file_path)
            
            # 尝试匹配商场名称或位置描述
            best_match = None
            best_score = 0.0
            
            for row in csv_data:
                csv_name = row.get('name', '')
                
                # 与商场名称匹配
                if mall_name and mall_name in csv_name:
                    score = similarity(mall_name, csv_name)
                    if score > best_score:
                        best_score = score
                        best_match = row
                
                # 与位置描述匹配
                if location_desc:
                    # 提取位置描述中的关键词进行匹配
                    keywords = [mall_name, city]
                    for keyword in keywords:
                        if keyword and keyword in csv_name:
                            score = similarity(keyword, csv_name)
                            if score > best_score and score > 0.6:
                                best_score = score
                                best_match = row
            
            # 如果找到匹配，添加经纬度
            if best_match and best_score > 0.3:  # 设置最低匹配阈值
                location = best_match.get('location', '')
                if location and ',' in location:
                    lng, lat = location.split(',')
                    shop["经纬度"] = {
                        "经度": float(lng.strip()),
                        "纬度": float(lat.strip())
                    }
                    shop["匹配来源"] = best_match.get('name', '')
                    shop["匹配得分"] = round(best_score, 3)
                    matched_count += 1
                else:
                    shop["经纬度"] = "位置格式错误"
            else:
                shop["经纬度"] = "未找到匹配"
        else:
            shop["经纬度"] = "无对应城市数据"
    
    print(f"成功匹配 {matched_count} 个店铺的经纬度")
    return json_data

if __name__ == "__main__":
    json_file = "e:\\Deskep\\P_sdor\\mart\\json\\sales_customers_P_sdor.json"
    csv_dir = "e:\\Deskep\\P_sdor\\in_city\\csv\\classified"

    print("开始读取JSON文件...")
    json_data = read_json(json_file)
    print(f"读取到 {len(json_data)} 个店铺数据")
    
    print("开始匹配经纬度...")
    updated_data = match_coordinates_by_city(json_data, csv_dir)
    
    print("保存更新后的JSON文件...")
    write_json(json_file, updated_data)
    print("经纬度匹配完成，已更新 JSON 文件。")