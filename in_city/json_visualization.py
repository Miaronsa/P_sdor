#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import folium
import numpy as np
from typing import Dict, List, Any
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors


def load_city_json(json_file_path: str) -> Dict[str, Any]:
    """加载单个城市的JSON文件"""
    try:
        with open(json_file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"加载文件 {json_file_path} 时出错: {e}")
        return {}


def get_color_from_density(poi_count: int, max_poi_count: int) -> str:
    """根据POI密度生成颜色，使用优化的颜色映射"""
    if max_poi_count == 0:
        return '#2166ac'  # 默认深蓝色
    
    # 计算密度比例 (0-1)
    raw_ratio = poi_count / max_poi_count
    
    # 使用平方根缩放来增加颜色差距，同时避免过度极端
    if poi_count == 0:
        density_ratio = 0
    else:
        # 平方根缩放: sqrt(poi_count / max_poi_count)
        density_ratio = np.sqrt(raw_ratio)
    
    # 增加颜色范围，使用0.05-0.95来保证有明显的颜色差异
    density_ratio = 0.05 + density_ratio * 0.9
    
    # 使用更鲜明的颜色映射
    # 低密度: 深蓝色 (#2166ac)
    # 中低密度: 浅蓝色 (#67a9cf) 
    # 中高密度: 橙色 (#f4a582)
    # 高密度: 深红色 (#b2182b)
    
    if density_ratio <= 0.33:
        # 从深蓝色到浅蓝色
        t = density_ratio * 3  # 0-1
        r = int(33 + (103 - 33) * t)
        g = int(102 + (169 - 102) * t)
        b = int(172 + (207 - 172) * t)
    elif density_ratio <= 0.66:
        # 从浅蓝色到橙色
        t = (density_ratio - 0.33) * 3  # 0-1
        r = int(103 + (244 - 103) * t)
        g = int(169 + (165 - 169) * t)
        b = int(207 + (130 - 207) * t)
    else:
        # 从橙色到深红色
        t = (density_ratio - 0.66) * 3  # 0-1
        r = int(244 + (178 - 244) * t)
        g = int(165 + (24 - 165) * t)
        b = int(130 + (43 - 130) * t)
    
    # 确保颜色值在有效范围内
    r = max(0, min(255, r))
    g = max(0, min(255, g))
    b = max(0, min(255, b))
    
    return f'#{r:02x}{g:02x}{b:02x}'


def create_single_city_map(city_data: Dict[str, Any], output_dir: str = "html") -> str:
    """为单个城市创建H3网格可视化地图，颜色基于POI密度"""
    try:
        city_name = city_data.get('city_name', '未知城市')
        hex_data = city_data.get('hexes', [])
        
        if not hex_data:
            print(f"没有 {city_name} 的H3数据可供可视化")
            return None
        
        # 计算地图中心点
        lats = [hex_info['lat'] for hex_info in hex_data]
        lngs = [hex_info['lng'] for hex_info in hex_data]
        center_lat = sum(lats) / len(lats)
        center_lng = sum(lngs) / len(lngs)
        
        # 获取最大POI数量用于归一化颜色
        poi_counts = [hex_info.get('poi_count', 0) for hex_info in hex_data]
        max_poi_count = max(poi_counts) if poi_counts else 1
        
        print(f"{city_name} 最大POI密度: {max_poi_count}")
        
        # 创建folium地图
        m = folium.Map(
            location=[center_lat, center_lng],
            zoom_start=10,
            tiles='OpenStreetMap'
        )
        
        # 添加H3网格 - 颜色基于POI密度
        for i, hex_info in enumerate(hex_data):
            poi_count = hex_info.get('poi_count', 0)
            hex_color = get_color_from_density(poi_count, max_poi_count)
            
            # 为每个H3六边形创建多边形
            folium.Polygon(
                locations=[(lat, lng) for lng, lat in hex_info['boundary']],
                popup=f"""
                    <b>H3网格信息</b><br>
                    H3 ID: {hex_info['h3_index']}<br>
                    POI数量: {poi_count}<br>
                    POI类型分布: {hex_info.get('poi_type_distribution', {})}
                """,
                tooltip=f"H3网格 {i+1} - POI: {poi_count}个",
                color=hex_color,
                weight=0.5,  # 减少边框粗细
                fillOpacity=0.7,  # 调整透明度
                fillColor=hex_color
            ).add_to(m)
        
        # 添加POI密度最高的hex标记
        if poi_counts:
            max_poi_hex = max(hex_data, key=lambda x: x.get('poi_count', 0))
            max_poi_count_actual = max_poi_hex.get('poi_count', 0)
            if max_poi_count_actual > 0:
                # 添加大的圆形标记
                folium.CircleMarker(
                    location=[max_poi_hex['lat'], max_poi_hex['lng']],
                    radius=15,
                    popup=f"""
                        <b>🏆 POI密度最高区域</b><br>
                        H3 ID: {max_poi_hex['h3_index']}<br>
                        POI数量: {max_poi_count_actual}<br>
                        位置: {max_poi_hex['lat']:.6f}, {max_poi_hex['lng']:.6f}<br>
                        <b>热点区域！</b>
                    """,
                    color='gold',
                    fillColor='red',
                    fillOpacity=1.0,
                    weight=4
                ).add_to(m)
                
                # 添加一个更小的内圈标记
                folium.CircleMarker(
                    location=[max_poi_hex['lat'], max_poi_hex['lng']],
                    radius=6,
                    color='white',
                    fillColor='yellow',
                    fillOpacity=1.0,
                    weight=2
                ).add_to(m)
        
        # 添加图例和标题
        title_html = f'''
                     <h3 align="center" style="font-size:20px"><b>{city_name} - H3网格POI密度可视化</b></h3>
                     <p align="center">网格数量: {len(hex_data)}</p>
                     <p align="center">分辨率: {city_data.get('resolution', 7)}</p>
                     <p align="center">最大POI密度: {max_poi_count}</p>
                     <p align="center" style="color: #b2182b;">深红色 = 最高密度</p>
                     <p align="center" style="color: #f4a582;">橙色 = 中高密度</p>
                     <p align="center" style="color: #67a9cf;">浅蓝色 = 中低密度</p>
                     <p align="center" style="color: #2166ac;">深蓝色 = 最低密度</p>
                     <p align="center">🏆 金色标记 = 密度最高区域</p>
                     '''
        m.get_root().html.add_child(folium.Element(title_html))
        
        # 保存地图
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, f"{city_name}_h3_poi_density_map.html")
        m.save(output_file)
        
        print(f"POI密度地图已保存到: {output_file}")
        return output_file
        
    except Exception as e:
        print(f"创建 {city_name} POI密度地图时出错: {e}")
        return None


def create_all_cities_overview_map(json_dir: str = "json", output_dir: str = "html") -> str:
    """创建所有城市的汇总地图，使用POI密度颜色编码"""
    try:
        all_cities_data = {}
        all_hex_data = []
        
        # 读取所有单个城市的JSON文件
        for filename in os.listdir(json_dir):
            if filename.endswith('_h3_grid.json') and not filename.startswith('all_cities'):
                json_path = os.path.join(json_dir, filename)
                city_data = load_city_json(json_path)
                if city_data:
                    city_name = city_data.get('city_name', filename.replace('_h3_grid.json', ''))
                    all_cities_data[city_name] = city_data
                    # 收集所有hex数据
                    hex_data = city_data.get('hexes', [])
                    for hex_info in hex_data:
                        hex_info['city_name'] = city_name  # 添加城市名标识
                        all_hex_data.append(hex_info)
        
        if not all_cities_data:
            print("没有找到城市数据文件")
            return None
        
        # 计算全局最大POI数量用于颜色归一化
        all_poi_counts = [hex_info.get('poi_count', 0) for hex_info in all_hex_data]
        global_max_poi = max(all_poi_counts) if all_poi_counts else 1
        print(f"全局最大POI密度: {global_max_poi}")
        
        # 收集所有城市的中心点
        all_centers = []
        for city_name, city_data in all_cities_data.items():
            hex_data = city_data.get('hexes', [])
            if hex_data:
                lats = [hex_info['lat'] for hex_info in hex_data]
                lngs = [hex_info['lng'] for hex_info in hex_data]
                center_lat = sum(lats) / len(lats)
                center_lng = sum(lngs) / len(lngs)
                total_pois = sum(hex_info.get('poi_count', 0) for hex_info in hex_data)
                all_centers.append((center_lat, center_lng, city_name, len(hex_data), total_pois))
        
        if not all_centers:
            print("没有有效的城市中心点数据")
            return None
        
        # 计算总体地图中心
        overall_center_lat = sum([center[0] for center in all_centers]) / len(all_centers)
        overall_center_lng = sum([center[1] for center in all_centers]) / len(all_centers)
        
        # 创建汇总地图
        m = folium.Map(
            location=[overall_center_lat, overall_center_lng],
            zoom_start=6,
            tiles='OpenStreetMap'
        )
        
        # 为所有H3网格添加基于POI密度的颜色多边形
        for hex_info in all_hex_data:
            poi_count = hex_info.get('poi_count', 0)
            hex_color = get_color_from_density(poi_count, global_max_poi)
            city_name = hex_info.get('city_name', '未知')
            
            folium.Polygon(
                locations=[(lat, lng) for lng, lat in hex_info['boundary']],
                popup=f"""
                    <b>城市: {city_name}</b><br>
                    H3 ID: {hex_info['h3_index']}<br>
                    POI数量: {poi_count}<br>
                    POI类型: {hex_info.get('poi_type_distribution', {})}
                """,
                tooltip=f"{city_name} - POI: {poi_count}",
                color=hex_color,
                weight=0.3,  # 更细的边框
                fillOpacity=0.6,  # 适中的透明度
                fillColor=hex_color
            ).add_to(m)
        
        # 为每个城市添加中心点标记
        marker_colors = ['darkgreen', 'darkblue', 'darkred', 'purple', 'orange', 'black']
        
        for i, (lat, lng, city_name, hex_count, total_pois) in enumerate(all_centers):
            color = marker_colors[i % len(marker_colors)]
            
            folium.Marker(
                location=[lat, lng],
                popup=folium.Popup(f"""
                    <b>{city_name}</b><br>
                    H3网格数量: {hex_count}<br>
                    总POI数量: {total_pois}<br>
                    平均POI密度: {total_pois/hex_count:.1f}<br>
                    中心位置: {lat:.6f}, {lng:.6f}
                """, max_width=300),
                tooltip=f"{city_name} (网格:{hex_count}, POI:{total_pois})",
                icon=folium.Icon(color=color, icon='info-sign')
            ).add_to(m)
        
        # 添加全局POI密度最高的hex标记
        if all_hex_data:
            global_max_hex = max(all_hex_data, key=lambda x: x.get('poi_count', 0))
            global_max_poi_count = global_max_hex.get('poi_count', 0)
            if global_max_poi_count > 0:
                # 添加全局最高密度标记
                folium.CircleMarker(
                    location=[global_max_hex['lat'], global_max_hex['lng']],
                    radius=20,
                    popup=f"""
                        <b>🏆 全局POI密度最高区域</b><br>
                        城市: {global_max_hex.get('city_name', '未知')}<br>
                        H3 ID: {global_max_hex['h3_index']}<br>
                        POI数量: {global_max_poi_count}<br>
                        位置: {global_max_hex['lat']:.6f}, {global_max_hex['lng']:.6f}<br>
                        <b>全局热点！</b>
                    """,
                    color='gold',
                    fillColor='red',
                    fillOpacity=1.0,
                    weight=5
                ).add_to(m)
                
                # 内圈标记
                folium.CircleMarker(
                    location=[global_max_hex['lat'], global_max_hex['lng']],
                    radius=8,
                    color='white',
                    fillColor='yellow',
                    fillOpacity=1.0,
                    weight=3
                ).add_to(m)
        
        # 添加标题和图例
        title_html = f'''
                     <h3 align="center" style="font-size:20px"><b>所有城市H3网格POI密度分布</b></h3>
                     <p align="center">总城市数量: {len(all_cities_data)}</p>
                     <p align="center">总网格数量: {len(all_hex_data)}</p>
                     <p align="center">全局最大POI密度: {global_max_poi}</p>
                     <p align="center" style="color: #b2182b;">深红色 = 最高密度</p>
                     <p align="center" style="color: #f4a582;">橙色 = 中高密度</p>
                     <p align="center" style="color: #67a9cf;">浅蓝色 = 中低密度</p>
                     <p align="center" style="color: #2166ac;">深蓝色 = 最低密度</p>
                     <p align="center">🏆 金色圆圈 = 全局密度最高区域</p>
                     '''
        m.get_root().html.add_child(folium.Element(title_html))
        
        # 保存地图
        os.makedirs(output_dir, exist_ok=True)
        output_file = os.path.join(output_dir, "all_cities_poi_density_overview.html")
        m.save(output_file)
        
        print(f"汇总POI密度地图已保存到: {output_file}")
        return output_file
        
    except Exception as e:
        print(f"创建汇总POI密度地图时出错: {e}")
        return None


def visualize_all_cities(json_dir: str = "json", html_dir: str = "html"):
    """可视化所有城市的H3网格"""
    print("开始可视化所有城市的H3网格...")
    
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_dir = os.path.join(script_dir, json_dir)
    html_dir = os.path.join(script_dir, html_dir)
    
    if not os.path.exists(json_dir):
        print(f"JSON目录不存在: {json_dir}")
        return
    
    # 确保HTML输出目录存在
    os.makedirs(html_dir, exist_ok=True)
    
    processed_cities = 0
    skipped_cities = 0
    
    # 处理单个城市文件
    for filename in os.listdir(json_dir):
        if filename.endswith('_h3_grid.json') and not filename.startswith('all_cities'):
            city_name = filename.replace('_h3_grid.json', '')
            html_filename = f"{city_name}_h3_poi_density_map.html"
            html_filepath = os.path.join(html_dir, html_filename)
            
            # 检查HTML文件是否已存在
            if os.path.exists(html_filepath):
                print(f"城市 {city_name} 的POI密度地图已存在，跳过")
                skipped_cities += 1
                continue
            
            # 加载城市数据并创建地图
            json_filepath = os.path.join(json_dir, filename)
            city_data = load_city_json(json_filepath)
            
            if city_data:
                result = create_single_city_map(city_data, html_dir)
                if result:
                    processed_cities += 1
                    print(f"成功为 {city_name} 创建地图")
                else:
                    print(f"为 {city_name} 创建地图失败")
            else:
                print(f"加载 {city_name} 数据失败")
    
    # 总是更新all_cities汇总地图
    print("\n更新所有城市的汇总地图...")
    result = create_all_cities_overview_map(json_dir, html_dir)
    if result:
        print("汇总地图更新成功")
    else:
        print("汇总地图更新失败")
    
    print(f"\n可视化完成!")
    print(f"处理了 {processed_cities} 个新城市")
    print(f"跳过了 {skipped_cities} 个已存在的城市")
    print(f"HTML文件保存在: {html_dir}")


if __name__ == "__main__":
    visualize_all_cities()
