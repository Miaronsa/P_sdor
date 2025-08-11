#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
商场hex分析器
识别包含商场POI的hex（mart_hex），计算其自身和相邻6个hex的各类POI数量
"""

import json
import os
import h3
from typing import Dict, List, Any, Set
from collections import defaultdict


def load_city_json(json_file_path: str) -> Dict[str, Any]:
    """加载单个城市的JSON文件"""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"加载文件 {json_file_path} 时出错: {e}")
        return {}


def find_mart_hexes(city_data: Dict[str, Any]) -> Set[str]:
    """找到包含商场POI的hex"""
    mart_hexes = set()
    
    for hex_info in city_data.get('hexes', []):
        h3_index = hex_info.get('h3_index', '')
        
        # 检查是否包含商场POI
        has_mall = False
        for poi in hex_info.get('pois', []):
            big_type = poi.get('big_type', '')
            mid_type = poi.get('mid_type', '')
            
            if big_type == "购物服务" and mid_type == "商场":
                has_mall = True
                break
        
        if has_mall:
            mart_hexes.add(h3_index)
    
    return mart_hexes


def get_hex_neighbors(h3_index: str) -> List[str]:
    """获取hex的6个相邻hex"""
    try:
        # 兼容h3 4.x，使用grid_disk
        neighbors = set(h3.grid_disk(h3_index, 1))
        neighbors.discard(h3_index)  # 移除自身，只保留6个相邻hex
        return list(neighbors)
    except Exception as e:
        print(f"获取hex {h3_index} 的邻居时出错: {e}")
        return []


def analyze_poi_distribution(city_data: Dict[str, Any], hex_indices: List[str]) -> Dict[str, Any]:
    """分析指定hex列表中的POI分布"""
    hex_index_set = set(hex_indices)
    poi_stats = {
        'total_pois': 0,
        'big_type_count': defaultdict(int),
        'mid_type_count': defaultdict(int),
        'poi_type_pairs': defaultdict(int),
        'hex_poi_counts': defaultdict(int)
    }
    
    for hex_info in city_data.get('hexes', []):
        h3_index = hex_info.get('h3_index', '')
        
        if h3_index in hex_index_set:
            pois = hex_info.get('pois', [])
            hex_poi_count = len(pois)
            poi_stats['hex_poi_counts'][h3_index] = hex_poi_count
            poi_stats['total_pois'] += hex_poi_count
            
            for poi in pois:
                big_type = poi.get('big_type', '')
                mid_type = poi.get('mid_type', '')
                
                if big_type:
                    poi_stats['big_type_count'][big_type] += 1
                if mid_type:
                    poi_stats['mid_type_count'][mid_type] += 1
                if big_type and mid_type:
                    poi_stats['poi_type_pairs'][f"{big_type}|{mid_type}"] += 1
    
    # 转换defaultdict为普通dict以便JSON序列化
    return {
        'total_pois': poi_stats['total_pois'],
        'big_type_count': dict(poi_stats['big_type_count']),
        'mid_type_count': dict(poi_stats['mid_type_count']),
        'poi_type_pairs': dict(poi_stats['poi_type_pairs']),
        'hex_poi_counts': dict(poi_stats['hex_poi_counts']),
        'analyzed_hex_count': len([h for h in hex_indices if h in poi_stats['hex_poi_counts']])
    }


def get_hex_details(city_data: Dict[str, Any], h3_index: str) -> Dict[str, Any]:
    """获取单个hex的详细信息"""
    for hex_info in city_data.get('hexes', []):
        if hex_info.get('h3_index') == h3_index:
            return {
                'h3_index': h3_index,
                'center': hex_info.get('center', []),
                'poi_count': len(hex_info.get('pois', [])),
                'has_mall': any(
                    poi.get('big_type') == "购物服务" and poi.get('mid_type') == "商场"
                    for poi in hex_info.get('pois', [])
                )
            }
    
    # 如果在数据中找不到该hex，返回基本信息
    try:
        center_coords = h3.h3_to_geo(h3_index)
        return {
            'h3_index': h3_index,
            'center': [center_coords[0], center_coords[1]],  # [lat, lng]
            'poi_count': 0,
            'has_mall': False
        }
    except:
        return {
            'h3_index': h3_index,
            'center': [0, 0],
            'poi_count': 0,
            'has_mall': False
        }


def analyze_mart_hexes(city_data: Dict[str, Any]) -> Dict[str, Any]:
    """分析商场hex及其邻居hex的POI分布"""
    city_name = city_data.get('city_name', '未知城市')
    print(f"正在分析城市: {city_name}")
    
    # 找到所有包含商场的hex
    mart_hexes = find_mart_hexes(city_data)
    print(f"找到 {len(mart_hexes)} 个包含商场的hex")
    
    if not mart_hexes:
        print(f"在 {city_name} 中未找到包含商场的hex")
        return {
            'city_name': city_name,
            'mart_hex_count': 0,
            'mart_hex_analysis': []
        }
    
    mart_hex_analysis = []
    
    for i, mart_hex in enumerate(mart_hexes, 1):
        print(f"处理商场hex {i}/{len(mart_hexes)}: {mart_hex}")
        
        # 获取相邻的6个hex
        neighbor_hexes = get_hex_neighbors(mart_hex)
        print(f"  找到 {len(neighbor_hexes)} 个相邻hex")
        
        # 分析商场hex自身的POI分布
        mart_hex_analysis_result = analyze_poi_distribution(city_data, [mart_hex])
        
        # 分析相邻hex的POI分布
        neighbor_analysis = analyze_poi_distribution(city_data, neighbor_hexes)
        
        # 分析所有7个hex（商场hex + 6个相邻hex）的总体分布
        all_hexes = [mart_hex] + neighbor_hexes
        total_analysis = analyze_poi_distribution(city_data, all_hexes)
        
        # 获取hex详细信息
        mart_hex_details = get_hex_details(city_data, mart_hex)
        neighbor_hex_details = [get_hex_details(city_data, h) for h in neighbor_hexes]
        
        mart_analysis = {
            'mart_hex': mart_hex,
            'mart_hex_details': mart_hex_details,
            'neighbor_hexes': neighbor_hexes,
            'neighbor_hex_details': neighbor_hex_details,
            'mart_hex_poi_stats': mart_hex_analysis_result,
            'neighbor_hexes_poi_stats': neighbor_analysis,
            'total_area_poi_stats': total_analysis
        }
        
        mart_hex_analysis.append(mart_analysis)
    
    result = {
        'city_name': city_name,
        'mart_hex_count': len(mart_hexes),
        'analysis_timestamp': str(pd.Timestamp.now()),
        'mart_hex_analysis': mart_hex_analysis,
        'summary': {
            'total_mart_hexes': len(mart_hexes),
            'total_analyzed_areas': len(mart_hexes) * 7,  # 每个商场hex分析7个hex（自身+6个邻居）
        }
    }
    
    return result


def process_cities(json_dir: str, output_dir: str):
    """处理所有城市的商场hex分析"""
    if not os.path.exists(json_dir):
        print(f"JSON目录不存在: {json_dir}")
        return
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    # 处理每个城市的JSON文件
    for filename in os.listdir(json_dir):
        if filename.endswith('_h3_grid.json') and not filename.startswith('all_cities'):
            city_name = filename.replace('_h3_grid.json', '')
            print(f"\n正在处理城市: {city_name}")
            
            # 检查是否已经处理过
            city_output_file = os.path.join(output_dir, f"{city_name}_mart_hex_analysis.json")
            if os.path.exists(city_output_file):
                print(f"城市 {city_name} 的商场hex分析已存在，跳过")
                continue
            
            # 加载城市数据
            json_filepath = os.path.join(json_dir, filename)
            city_data = load_city_json(json_filepath)
            
            if not city_data:
                print(f"无法加载 {city_name} 的数据")
                continue
            
            # 分析商场hex
            analysis_result = analyze_mart_hexes(city_data)
            
            # 保存分析结果
            with open(city_output_file, 'w', encoding='utf-8') as f:
                json.dump(analysis_result, f, ensure_ascii=False, indent=2)
            
            print(f"已保存 {city_name} 的商场hex分析结果到: {city_output_file}")
            
            # 显示简要统计
            if analysis_result.get('mart_hex_count', 0) > 0:
                print(f"  - 商场hex数量: {analysis_result['mart_hex_count']}")
                for analysis in analysis_result.get('mart_hex_analysis', []):
                    total_pois = analysis['total_area_poi_stats']['total_pois']
                    mart_hex_pois = analysis['mart_hex_poi_stats']['total_pois']
                    neighbor_pois = analysis['neighbor_hexes_poi_stats']['total_pois']
                    print(f"  - 商场hex {analysis['mart_hex'][:8]}...: 自身{mart_hex_pois}POI, 邻居{neighbor_pois}POI, 总计{total_pois}POI")


if __name__ == "__main__":
    import pandas as pd
    
    # 设置路径
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_dir = os.path.join(script_dir, 'json')
    output_dir = os.path.join(script_dir, 'mart_hex_analysis')
    
    print("商场hex分析器启动")
    print(f"JSON目录: {json_dir}")
    print(f"输出目录: {output_dir}")
    
    process_cities(json_dir, output_dir)
    
    print("\n商场hex分析完成！")
