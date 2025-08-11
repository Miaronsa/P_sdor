#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import pandas as pd
import h3
import json
import os
from typing import Dict, List, Any, Tuple
from collections import defaultdict


def load_city_csv(csv_file_path: str) -> pd.DataFrame:
    """加载城市POI的CSV文件"""
    try:
        df = pd.read_csv(csv_file_path)
        print(f"加载CSV文件成功，共有 {len(df)} 条POI记录")
        return df
    except Exception as e:
        print(f"加载CSV文件 {csv_file_path} 时出错: {e}")
        return pd.DataFrame()


def load_city_h3_json(json_file_path: str) -> Dict[str, Any]:
    """加载城市H3网格的JSON文件"""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"加载JSON文件成功，共有 {data.get('total_hexes', 0)} 个H3网格")
        return data
    except Exception as e:
        print(f"加载JSON文件 {json_file_path} 时出错: {e}")
        return {}


def parse_location(location_str: str) -> Tuple[float, float]:
    """解析位置字符串，返回经纬度"""
    try:
        # 移除引号并分割
        location_str = location_str.strip('"')
        lng, lat = map(float, location_str.split(','))
        return lat, lng
    except Exception as e:
        print(f"解析位置 {location_str} 时出错: {e}")
        return None, None


def assign_pois_to_hexes(df: pd.DataFrame, h3_data: Dict[str, Any]) -> Dict[str, List[Dict]]:
    """将POI分配到H3网格中"""
    hex_poi_map = defaultdict(list)
    successful_assignments = 0
    failed_assignments = 0
    
    print("开始将POI分配到H3网格...")
    
    for idx, row in df.iterrows():
        if idx % 10000 == 0:
            print(f"已处理 {idx} / {len(df)} 条POI记录")
        
        # 解析位置
        lat, lng = parse_location(row['location'])
        if lat is None or lng is None:
            failed_assignments += 1
            continue
        
        # 获取该位置对应的H3网格ID
        try:
            h3_id = h3.latlng_to_cell(lat, lng, 7)  # 使用分辨率7
            
            # 创建POI信息
            poi_info = {
                'id': row['id'],
                'name': row['name'],
                'lat': lat,
                'lng': lng,
                'province': row['pname'],
                'city': row['cityname'],
                'district': row['adname'],
                'big_type': row['bigType'],
                'mid_type': row['midType'],
                'small_type': row['smallType']
            }
            
            hex_poi_map[h3_id].append(poi_info)
            successful_assignments += 1
            
        except Exception as e:
            failed_assignments += 1
            continue
    
    print(f"POI分配完成！成功: {successful_assignments}, 失败: {failed_assignments}")
    return hex_poi_map


def update_h3_with_pois(h3_data: Dict[str, Any], hex_poi_map: Dict[str, List[Dict]]) -> Dict[str, Any]:
    """更新H3网格数据，添加POI信息"""
    print("更新H3网格数据...")
    
    updated_hexes = []
    max_poi_density = 0
    highest_density_hex = None
    
    for hex_info in h3_data.get('hexes', []):
        h3_id = hex_info['h3_index']
        
        # 获取该网格的POI列表
        pois = hex_poi_map.get(h3_id, [])
        poi_count = len(pois)
        
        # 更新最高密度信息
        if poi_count > max_poi_density:
            max_poi_density = poi_count
            highest_density_hex = {
                'h3_index': h3_id,
                'poi_count': poi_count,
                'center': hex_info['center'],
                'boundary': hex_info['boundary']
            }
        
        # 统计POI类型分布
        poi_type_stats = defaultdict(int)
        for poi in pois:
            poi_type_stats[poi['big_type']] += 1
        
        # 更新hex信息
        updated_hex_info = hex_info.copy()
        updated_hex_info.update({
            'poi_count': poi_count,
            'pois': pois,
            'poi_type_distribution': dict(poi_type_stats)
        })
        
        updated_hexes.append(updated_hex_info)
    
    # 更新整体数据
    updated_data = h3_data.copy()
    updated_data['hexes'] = updated_hexes
    updated_data['total_poi_count'] = sum(len(pois) for pois in hex_poi_map.values())
    updated_data['highest_density_hex'] = highest_density_hex
    updated_data['max_poi_density'] = max_poi_density
    
    print(f"更新完成！总POI数量: {updated_data['total_poi_count']}")
    print(f"最高密度网格: {highest_density_hex['h3_index']} (POI数量: {max_poi_density})")
    
    return updated_data


def process_city_pois(city_name: str):
    """处理单个城市的POI数据"""
    print(f"\n开始处理城市: {city_name}")
    
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 构建文件路径
    csv_file = os.path.join(script_dir, "csv", "classified", f"{city_name}.csv")
    json_file = os.path.join(script_dir, "json", f"{city_name}_h3_grid.json")
    
    # 检查文件是否存在
    if not os.path.exists(csv_file):
        print(f"CSV文件不存在: {csv_file}")
        return False
    
    if not os.path.exists(json_file):
        print(f"JSON文件不存在: {json_file}")
        return False
    
    # 加载数据
    df = load_city_csv(csv_file)
    if df.empty:
        print(f"CSV文件为空或加载失败")
        return False
    
    h3_data = load_city_h3_json(json_file)
    if not h3_data:
        print(f"JSON文件为空或加载失败")
        return False
    
    # 检查JSON文件是否已经包含POI信息
    if any('poi_count' in hex_info for hex_info in h3_data.get('hexes', [])):
        print(f"城市 {city_name} 的H3网格已包含POI信息，跳过处理")
        return True
    
    # 分配POI到网格
    hex_poi_map = assign_pois_to_hexes(df, h3_data)
    
    # 更新H3数据
    updated_data = update_h3_with_pois(h3_data, hex_poi_map)
    
    # 保存更新后的数据
    try:
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(updated_data, f, ensure_ascii=False, indent=2)
        print(f"更新后的数据已保存到: {json_file}")
        return True
    except Exception as e:
        print(f"保存文件时出错: {e}")
        return False


def process_all_cities():
    """处理所有城市的POI数据"""
    print("开始处理所有城市的POI数据...")
    
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_dir = os.path.join(script_dir, "csv", "classified")
    
    if not os.path.exists(csv_dir):
        print(f"CSV目录不存在: {csv_dir}")
        return
    
    processed_cities = 0
    skipped_cities = 0
    failed_cities = 0
    
    # 获取所有城市CSV文件
    for filename in os.listdir(csv_dir):
        if filename.endswith('.csv'):
            city_name = filename.replace('.csv', '')
            
            result = process_city_pois(city_name)
            if result:
                processed_cities += 1
            else:
                failed_cities += 1
    
    print(f"\n所有城市处理完成！")
    print(f"成功处理: {processed_cities} 个城市")
    print(f"处理失败: {failed_cities} 个城市")


if __name__ == "__main__":
    process_all_cities()
