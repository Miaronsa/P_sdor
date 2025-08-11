#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import osmnx as ox
import geopandas as gpd
from shapely.geometry import Point, Polygon
import pandas as pd
import time
from typing import Dict, List, Any


def load_city_json(json_file_path: str) -> Dict[str, Any]:
    """加载单个城市的JSON文件"""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"加载文件 {json_file_path} 时出错: {e}")
        return {}


def extract_mall_pois(city_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """提取城市数据中midType为"商场"相关的POI"""
    mall_pois = []
    city_name = city_data.get('city_name', '未知城市')
    
    print(f"正在提取 {city_name} 的商场POI...")
    
    # 商场相关的关键词
    mall_keywords = ['商场', '购物中心', '商城', '百货', '广场', '奥特莱斯', '商业街', '商业广场']
    
    # 遍历所有hex
    for hex_info in city_data.get('hexes', []):
        # 遍历每个hex中的POI
        for poi in hex_info.get('pois', []):
            mid_type = poi.get('mid_type', '')
            name = poi.get('name', '')
            
            # 检查是否为商场类型的POI (检查类型或名称)
            is_mall = any(keyword in mid_type for keyword in mall_keywords) or \
                     any(keyword in name for keyword in mall_keywords)
            
            if is_mall:
                mall_poi = poi.copy()
                mall_poi['hex_id'] = hex_info.get('h3_index', '')
                mall_poi['hex_center'] = hex_info.get('center', [])
                mall_pois.append(mall_poi)
    
    print(f"在 {city_name} 中找到 {len(mall_pois)} 个商场相关POI")
    
    # 打印找到的商场名称
    for poi in mall_pois:
        print(f"  - {poi.get('name', '未知')} ({poi.get('mid_type', '未知类型')})")
    
    return mall_pois


def get_poi_area_data(poi_name: str, poi_lat: float, poi_lng: float, city_name: str = "") -> Dict[str, Any]:
    """获取POI对应的面状数据"""
    try:
        print(f"正在获取 {poi_name} 的面状数据...")
        
        # 尝试不同的查询方式
        query_formats = [
            f"{poi_name}, {city_name}",
            f"{poi_name}, China",
            f"{poi_name}"
        ]
        
        gdf = None
        for query in query_formats:
            try:
                print(f"  尝试查询: {query}")
                gdf = ox.geocode_to_gdf(query)
                if gdf is not None and not gdf.empty:
                    print(f"  查询成功: {query}")
                    break
                time.sleep(1)  # 避免请求过于频繁
            except Exception as e:
                print(f"  查询 {query} 失败: {e}")
                continue
        
        if gdf is None or gdf.empty:
            print(f"  无法找到 {poi_name} 的面状数据，使用缓冲区近似...")
            # 如果找不到面状数据，创建一个缓冲区作为近似
            point = Point(poi_lng, poi_lat)
            # 创建300米的缓冲区（约0.0027度）
            buffer_area = point.buffer(0.0027)
            
            result = {
                'poi_name': poi_name,
                'geometry_type': 'buffered_point',
                'area_km2': 0.283,  # 300米半径圆的面积约0.283平方公里
                'bounds': list(buffer_area.bounds),
                'centroid': [poi_lat, poi_lng],
                'geometry': buffer_area.__geo_interface__,
                'data_source': 'buffer_approximation',
                'buffer_radius_m': 300
            }
            return result
            
        # 获取第一个结果的几何体
        geometry = gdf.geometry.iloc[0]
        
        # 如果是多边形集合，选择面积最大的
        if hasattr(geometry, 'geom_type') and geometry.geom_type == 'MultiPolygon':
            geometry = max(geometry.geoms, key=lambda a: a.area)
        
        # 计算面积（粗略估算，以平方度为单位转换为平方公里）
        area_degrees = geometry.area
        # 粗略转换：1度约等于111公里
        area_km2 = area_degrees * (111 ** 2)
        
        # 获取中心点
        centroid = geometry.centroid
        centroid_coords = [centroid.y, centroid.x]  # [lat, lng]
        
        # 获取边界框
        bounds = list(geometry.bounds)  # [minx, miny, maxx, maxy]
        
        result = {
            'poi_name': poi_name,
            'geometry_type': geometry.geom_type,
            'area_km2': area_km2,
            'bounds': bounds,
            'centroid': centroid_coords,
            'geometry': geometry.__geo_interface__,
            'data_source': 'osm_query'
        }
        
        print(f"  成功获取 {poi_name} 的面状数据，面积: {area_km2:.3f} km²")
        return result
        
    except Exception as e:
        print(f"获取 {poi_name} 面状数据时出错: {e}")
        return {}


def process_mall_areas(json_dir: str = "json", output_dir: str = "mall_areas"):
    """处理所有城市的商场POI，获取面状数据"""
    print("开始处理城市商场POI的面状数据...")
    
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_dir = os.path.join(script_dir, json_dir)
    output_dir = os.path.join(script_dir, output_dir)
    
    if not os.path.exists(json_dir):
        print(f"JSON目录不存在: {json_dir}")
        return
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    all_mall_areas = {}
    
    # 处理每个城市的JSON文件
    for filename in os.listdir(json_dir):
        if filename.endswith('_h3_grid.json') and not filename.startswith('all_cities'):
            city_name = filename.replace('_h3_grid.json', '')
            print(f"\n正在处理城市: {city_name}")
            
            # 检查是否已经处理过
            city_output_file = os.path.join(output_dir, f"{city_name}_mall_areas.json")
            if os.path.exists(city_output_file):
                print(f"城市 {city_name} 的商场面状数据已存在，跳过")
                # 仍然加载已存在的数据用于汇总
                try:
                    with open(city_output_file, 'r', encoding='utf-8') as f:
                        existing_data = json.load(f)
                    all_mall_areas[city_name] = existing_data
                except:
                    pass
                continue
            
            # 加载城市数据
            json_filepath = os.path.join(json_dir, filename)
            city_data = load_city_json(json_filepath)
            
            if not city_data:
                print(f"无法加载 {city_name} 的数据")
                continue
            
            # 提取商场POI
            mall_pois = extract_mall_pois(city_data)
            
            if not mall_pois:
                print(f"{city_name} 没有找到商场POI")
                continue
            
            # 获取每个商场的面状数据
            city_mall_areas = []
            for i, poi in enumerate(mall_pois):
                poi_name = poi.get('name', '未知商场')
                print(f"  处理商场 {i+1}/{len(mall_pois)}: {poi_name}")
                
                area_data = get_poi_area_data(
                    poi_name,
                    poi.get('lat', 0),
                    poi.get('lng', 0),
                    city_name
                )
                
                if area_data:
                    # 合并POI信息和面状数据
                    combined_data = {
                        **poi,  # 原POI信息
                        'area_data': area_data  # 面状数据
                    }
                    city_mall_areas.append(combined_data)
                
                # 添加延迟避免请求过于频繁
                time.sleep(2)
            
            # 保存城市的商场面状数据
            if city_mall_areas:
                city_result = {
                    'city_name': city_name,
                    'total_malls': len(city_mall_areas),
                    'processing_time': time.strftime("%Y-%m-%d %H:%M:%S"),
                    'malls': city_mall_areas
                }
                
                with open(city_output_file, 'w', encoding='utf-8') as f:
                    json.dump(city_result, f, ensure_ascii=False, indent=2)
                
                print(f"  成功保存 {len(city_mall_areas)} 个商场的面状数据到: {city_output_file}")
                all_mall_areas[city_name] = city_result
            else:
                print(f"  {city_name} 没有成功获取任何商场面状数据")
    
    # 保存汇总结果
    if all_mall_areas:
        summary_file = os.path.join(output_dir, "all_cities_mall_areas_summary.json")
        summary_data = {
            'processed_cities': list(all_mall_areas.keys()),
            'total_cities': len(all_mall_areas),
            'total_malls': sum(len(city_data['malls']) for city_data in all_mall_areas.values()),
            'generation_time': time.strftime("%Y-%m-%d %H:%M:%S"),
            'cities_summary': {
                city: {
                    'mall_count': len(data['malls']),
                    'mall_names': [mall.get('name', '未知') for mall in data['malls']]
                }
                for city, data in all_mall_areas.items()
            }
        }
        
        with open(summary_file, 'w', encoding='utf-8') as f:
            json.dump(summary_data, f, ensure_ascii=False, indent=2)
        
        print(f"\n处理完成！")
        print(f"共处理了 {len(all_mall_areas)} 个城市")
        print(f"总共获取了 {summary_data['total_malls']} 个商场的面状数据")
        print(f"结果保存在: {output_dir}")
        print(f"汇总文件: {summary_file}")
    else:
        print("没有成功处理任何城市的商场数据")


if __name__ == "__main__":
    process_mall_areas()