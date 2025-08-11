import csv
import json
import os
import re

# 输入和输出文件路径
input_csv_path = 'e:/Deskep/P_sdor/mart/csv/restaraunt_all/sales_customers.csv'
output_json_dir = 'e:/Deskep/P_sdor/mart/json'
output_json_path = os.path.join(output_json_dir, 'sales_customers_P_sdor.json')

# 确保输出目录存在
os.makedirs(output_json_dir, exist_ok=True)

# 读取 CSV 文件并处理数据
result = []
with open(input_csv_path, 'r', encoding='utf-8') as csv_file:
    reader = csv.reader(csv_file)
    next(reader)  # 跳过第一行
    headers = next(reader)  # 获取实际列名

    for row in reader:
        row_data = dict(zip(headers, row))

        # 提取省、市和区名称
        location = row_data['店铺位置']
        province_match = re.search(r'(\S+省)', location)
        province = province_match.group(1) if province_match else '未知省'
        city_match = re.search(r'(\S+市)', location)
        city = city_match.group(1) if city_match else '未知市'
        district_match = re.search(r'(\S+区)', location)
        district = district_match.group(1) if district_match else '未知区'

        # 对城市去除省名中重合的字符
        for char in province:
            city = city.replace(char, '')

        # 去除区名中与城市重合的部分
        for char in city:
            district = district.replace(char, '')

        # 从店铺名称中逐字符去除省、市和区名称中的字符
        store_name = row_data['店铺名称']
        for char in province + city + district:
            store_name = store_name.replace(char, '')
        mall_name = store_name.replace('小菜园', '').replace('店', '').strip()

        result.append({
            '省': province,
            '城市': city,
            '区': district,
            '商场名称': mall_name,
            '店铺位置': location,
            '营业额': row_data['营业额'],
            '客单价': row_data['平均客单价']
        })

# 保存为 JSON 文件
with open(output_json_path, 'w', encoding='utf-8') as json_file:
    json.dump(result, json_file, ensure_ascii=False, indent=4)

print(f'数据已保存到 {output_json_path}')