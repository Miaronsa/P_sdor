#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
商场hex可视化器
根据商场hex分析结果在实际地图上进行可视化
"""

import json
import folium
import os
import h3
from folium import plugins

def visualize_mart_hex_analysis(json_path, output_html):
    """根据商场hex分析结果创建可视化地图"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    city_name = data.get('city_name', '未知城市')
    mart_hex_analysis = data.get('mart_hex_analysis', [])
    
    if not mart_hex_analysis:
        print("没有商场hex分析数据！")
        return

    print(f"正在为 {city_name} 创建商场hex可视化地图...")
    print(f"商场hex数量: {len(mart_hex_analysis)}")

    # 计算地图中心点
    all_centers = []
    for analysis in mart_hex_analysis:
        mart_center = analysis['mart_hex_details']['center']
        all_centers.append(mart_center)
        for neighbor_detail in analysis['neighbor_hex_details']:
            all_centers.append(neighbor_detail['center'])

    if not all_centers:
        print("没有中心点数据，无法生成地图")
        return

    center_lat = sum([c[0] for c in all_centers]) / len(all_centers)
    center_lng = sum([c[1] for c in all_centers]) / len(all_centers)

    # 创建地图
    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=11,
        tiles='OpenStreetMap'
    )

    # 添加不同底图选项
    folium.TileLayer('CartoDB positron', name='CartoDB Positron').add_to(m)
    folium.TileLayer('CartoDB dark_matter', name='CartoDB Dark').add_to(m)

    # 统计数据
    total_mart_hexes = 0
    total_neighbor_hexes = 0
    
    # 为每个商场hex及其邻居添加标记
    for analysis in mart_hex_analysis:
        mart_hex_id = analysis['mart_hex']
        mart_details = analysis['mart_hex_details']
        neighbor_details = analysis['neighbor_hex_details']
        
        total_mart_hexes += 1
        total_neighbor_hexes += len(neighbor_details)
        
        # 添加商场hex（红色，大圆点）
        mart_center = mart_details['center']
        mart_poi_count = mart_details['poi_count']
        
        # 获取hex边界用于多边形显示
        try:
            hex_boundary = h3.h3_to_geo_boundary(mart_hex_id)
            hex_coords = [[lat, lng] for lat, lng in hex_boundary]
            
            # 添加商场hex多边形
            folium.Polygon(
                locations=hex_coords,
                color='#FF4444',
                weight=2,
                fill=True,
                fill_color='#FF4444',
                fill_opacity=0.3,
                popup=folium.Popup(f"""
                    <div style="width: 250px">
                        <h4>🏬 商场Hex</h4>
                        <p><b>Hex ID:</b> {mart_hex_id}</p>
                        <p><b>POI数量:</b> {mart_poi_count}</p>
                        <p><b>中心坐标:</b> {mart_center[0]:.6f}, {mart_center[1]:.6f}</p>
                        <p><b>类型:</b> 商场聚集区</p>
                    </div>
                """, max_width=300),
                tooltip=f"商场Hex: {mart_poi_count} POIs"
            ).add_to(m)
            
        except:
            pass
        
        # 商场hex中心点标记
        folium.CircleMarker(
            location=mart_center,
            radius=10,
            color='#DD0000',
            fill=True,
            fill_color='#FF4444',
            fill_opacity=0.8,
            popup=f"商场Hex: {mart_poi_count} POIs",
            tooltip=f"🏬 商场Hex ({mart_poi_count} POIs)"
        ).add_to(m)
        
        # 添加邻居hex（绿色，小圆点）
        for neighbor_detail in neighbor_details:
            neighbor_hex_id = neighbor_detail['h3_index']
            neighbor_center = neighbor_detail['center']
            neighbor_poi_count = neighbor_detail['poi_count']
            has_mall = neighbor_detail.get('has_mall', False)
            
            # 获取邻居hex边界
            try:
                neighbor_boundary = h3.h3_to_geo_boundary(neighbor_hex_id)
                neighbor_coords = [[lat, lng] for lat, lng in neighbor_boundary]
                
                # 邻居hex多边形（如果也是商场hex则用橙色，否则用绿色）
                neighbor_color = '#FF8800' if has_mall else '#228B22'
                folium.Polygon(
                    locations=neighbor_coords,
                    color=neighbor_color,
                    weight=1,
                    fill=True,
                    fill_color=neighbor_color,
                    fill_opacity=0.2,
                    popup=folium.Popup(f"""
                        <div style="width: 250px">
                            <h4>{'🏬 邻居商场Hex' if has_mall else '🏘️ 邻居Hex'}</h4>
                            <p><b>Hex ID:</b> {neighbor_hex_id}</p>
                            <p><b>POI数量:</b> {neighbor_poi_count}</p>
                            <p><b>中心坐标:</b> {neighbor_center[0]:.6f}, {neighbor_center[1]:.6f}</p>
                            <p><b>类型:</b> {'也含商场' if has_mall else '普通邻居'}</p>
                        </div>
                    """, max_width=300),
                    tooltip=f"邻居Hex: {neighbor_poi_count} POIs"
                ).add_to(m)
                
            except:
                pass
            
            # 邻居hex中心点标记
            marker_color = '#FF8800' if has_mall else '#228B22'
            folium.CircleMarker(
                location=neighbor_center,
                radius=6 if has_mall else 4,
                color=marker_color,
                fill=True,
                fill_color=marker_color,
                fill_opacity=0.6,
                popup=f"邻居Hex: {neighbor_poi_count} POIs",
                tooltip=f"{'🏬' if has_mall else '🏘️'} 邻居 ({neighbor_poi_count} POIs)"
            ).add_to(m)

    # 添加图例
    legend_html = f"""
    <div style="position: fixed; 
                bottom: 50px; left: 50px; width: 280px; height: 180px; 
                background-color: white; border:2px solid grey; z-index:9999; 
                font-size:12px; padding: 10px">
    <h4>{city_name} 商场Hex分析</h4>
    <p><i class="fa fa-square" style="color:#FF4444"></i> 商场Hex ({total_mart_hexes}个)</p>
    <p><i class="fa fa-square" style="color:#FF8800"></i> 邻居商场Hex</p>
    <p><i class="fa fa-square" style="color:#228B22"></i> 普通邻居Hex ({total_neighbor_hexes}个)</p>
    <p><b>总分析区域:</b> {total_mart_hexes + total_neighbor_hexes} 个Hex</p>
    <p><b>平均每商场Hex:</b> {total_neighbor_hexes/total_mart_hexes:.1f} 个邻居</p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    # 添加图层控制
    folium.LayerControl().add_to(m)
    
    # 添加全屏按钮
    plugins.Fullscreen().add_to(m)

    # 保存地图
    os.makedirs(os.path.dirname(output_html), exist_ok=True)
    m.save(output_html)
    print(f"✅ 可视化地图已保存到: {output_html}")
    print(f"📊 统计: {total_mart_hexes}个商场Hex, {total_neighbor_hexes}个邻居Hex")


def analyze_poi_statistics(json_path):
    """分析POI统计信息"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    city_name = data.get('city_name', '未知城市')
    mart_hex_analysis = data.get('mart_hex_analysis', [])
    
    print(f"\n=== {city_name} 商场Hex POI统计分析 ===")
    
    total_mart_poi = 0
    total_neighbor_poi = 0
    max_mart_poi = 0
    min_mart_poi = float('inf')
    
    for analysis in mart_hex_analysis:
        mart_poi_count = analysis['mart_hex_details']['poi_count']
        total_mart_poi += mart_poi_count
        max_mart_poi = max(max_mart_poi, mart_poi_count)
        min_mart_poi = min(min_mart_poi, mart_poi_count)
        
        for neighbor_detail in analysis['neighbor_hex_details']:
            total_neighbor_poi += neighbor_detail['poi_count']
    
    avg_mart_poi = total_mart_poi / len(mart_hex_analysis) if mart_hex_analysis else 0
    total_neighbor_hexes = sum(len(analysis['neighbor_hex_details']) for analysis in mart_hex_analysis)
    avg_neighbor_poi = total_neighbor_poi / total_neighbor_hexes if total_neighbor_hexes else 0
    
    print(f"商场Hex POI统计:")
    print(f"  - 平均POI数: {avg_mart_poi:.1f}")
    print(f"  - 最大POI数: {max_mart_poi}")
    print(f"  - 最小POI数: {min_mart_poi}")
    print(f"  - 总计POI数: {total_mart_poi}")
    
    print(f"邻居Hex POI统计:")
    print(f"  - 平均POI数: {avg_neighbor_poi:.1f}")
    print(f"  - 总计POI数: {total_neighbor_poi}")
    
    print(f"整体统计:")
    print(f"  - 商场Hex vs 邻居Hex POI密度比: {avg_mart_poi/avg_neighbor_poi:.2f}:1" if avg_neighbor_poi > 0 else "  - 无邻居数据")


if __name__ == "__main__":
    base_dir = r"e:\Deskep\Final\in_city"
    json_path = os.path.join(base_dir, "mart_hex_analysis", "合肥市_mart_hex_analysis.json")
    output_html = os.path.join(base_dir, "html", "合肥市_mart_hex_analysis_map.html")
    
    # 生成可视化
    visualize_mart_hex_analysis(json_path, output_html)
    
    # 分析统计信息
    analyze_poi_statistics(json_path)
