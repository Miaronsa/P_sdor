import pandas as pd
import h3
import json
import os
import osmnx as ox
import geopandas as gpd
from shapely.geometry import Polygon
import time


def get_city_names_from_csv():
    """从csv/classified文件夹下获取所有城市名"""
    # 获取脚本所在目录
    script_dir = os.path.dirname(os.path.abspath(__file__))
    csv_folder = os.path.join(script_dir, "csv", "classified")
    city_names = []
    
    print(f"正在查找CSV文件夹: {csv_folder}")
    
    if os.path.exists(csv_folder):
        files = os.listdir(csv_folder)
        print(f"找到的文件: {files}")
        for file in files:
            if file.endswith('.csv'):
                city_name = file.replace('.csv', '')
                city_names.append(city_name)
    else:
        print(f"CSV文件夹不存在: {csv_folder}")
    
    return city_names


def get_city_boundary(city_name):
    """获取城市边界"""
    try:
        # 尝试不同的查询格式
        query_formats = [
            f"{city_name}, China",
            f"{city_name}",
            f"{city_name}, 中国"
        ]
        
        gdf = None
        for query in query_formats:
            try:
                print(f"正在查询: {query}")
                gdf = ox.geocode_to_gdf(query)
                if gdf is not None and not gdf.empty:
                    break
                time.sleep(1)  # 避免请求过于频繁
            except Exception as e:
                print(f"查询 {query} 失败: {e}")
                continue
        
        if gdf is None or gdf.empty:
            print(f"无法找到城市 {city_name} 的边界")
            return None
            
        polygon = gdf.geometry.iloc[0]
        
        # 如果是多边形集合，选择面积最大的
        if hasattr(polygon, 'geom_type') and polygon.geom_type == 'MultiPolygon': # type: ignore
            polygon = max(polygon.geoms, key=lambda a: a.area) # type: ignore
        
        return polygon
        
    except Exception as e:
        print(f"获取城市 {city_name} 边界时出错: {e}")
        return None


def generate_h3_grid(polygon, resolution=7):
    """为给定的多边形生成H3网格"""
    try:
        # 将polygon转换为H3可识别的格式
        h3shape = h3.geo_to_h3shape(polygon.__geo_interface__)
        
        # 获取覆盖多边形的H3六边形
        hexes = h3.polygon_to_cells(h3shape, resolution)
        
        hex_data = []
        for hex_id in hexes:
            # 获取六边形边界
            boundary = [(lng, lat) for lat, lng in h3.cell_to_boundary(hex_id)]
            
            # 获取六边形中心点
            center = h3.cell_to_latlng(hex_id)
            
            hex_data.append({
                "h3_index": hex_id,
                "boundary": boundary,
                "center": center,
                "lat": center[0],
                "lng": center[1]
            })
        
        return hex_data
        
    except Exception as e:
        print(f"生成H3网格时出错: {e}")
        return []


def process_cities():
    """处理所有城市，生成H3网格"""
    # 获取所有城市名
    city_names = get_city_names_from_csv()
    print(f"找到 {len(city_names)} 个城市: {city_names}")
    
    # 获取脚本所在目录并创建输出文件夹
    script_dir = os.path.dirname(os.path.abspath(__file__))
    json_output_dir = os.path.join(script_dir, "json")
    os.makedirs(json_output_dir, exist_ok=True)
    
    all_results = {}
    
    for city_name in city_names:
        print(f"\n正在处理城市: {city_name}")
        
        # 检查是否已经存在该城市的H3网格文件
        city_output_file = os.path.join(json_output_dir, f"{city_name}_h3_grid.json")
        if os.path.exists(city_output_file):
            print(f"城市 {city_name} 的H3网格文件已存在，跳过处理")
            # 读取已存在的文件并加入汇总结果
            try:
                with open(city_output_file, "r", encoding="utf-8") as f:
                    existing_data = json.load(f)
                    all_results[city_name] = {
                        "total_hexes": existing_data.get("total_hexes", 0),
                        "hexes": existing_data.get("hexes", [])
                    }
                print(f"已加载 {city_name} 的现有数据：{existing_data.get('total_hexes', 0)} 个H3网格")
            except Exception as e:
                print(f"读取现有文件 {city_output_file} 时出错: {e}")
            continue
        
        # 获取城市边界
        polygon = get_city_boundary(city_name)
        if polygon is None:
            print(f"跳过城市 {city_name}")
            continue
        
        # 生成H3网格
        hex_data = generate_h3_grid(polygon, resolution=7)
        
        if hex_data:
            print(f"为 {city_name} 生成了 {len(hex_data)} 个H3网格")
            
            # 保存单个城市的结果
            city_output_file = os.path.join(json_output_dir, f"{city_name}_h3_grid.json")
            with open(city_output_file, "w", encoding="utf-8") as f:
                json.dump({
                    "city_name": city_name,
                    "total_hexes": len(hex_data),
                    "resolution": 7,
                    "hexes": hex_data
                }, f, ensure_ascii=False, indent=2)
            
            all_results[city_name] = {
                "total_hexes": len(hex_data),
                "hexes": hex_data
            }
        else:
            print(f"未能为 {city_name} 生成H3网格")
    
    # 保存所有城市的汇总结果
    if all_results:
        summary_file = os.path.join(json_output_dir, "all_cities_h3_summary.json")
        with open(summary_file, "w", encoding="utf-8") as f:
            json.dump({
                "processed_cities": list(all_results.keys()),
                "total_cities": len(all_results),
                "generation_time": time.strftime("%Y-%m-%d %H:%M:%S"),
                "cities": all_results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n处理完成！共处理了 {len(all_results)} 个城市")
        print(f"JSON结果保存在: {json_output_dir}")
    else:
        print("没有成功处理任何城市")


if __name__ == "__main__":
    process_cities()