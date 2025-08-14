import os
import pandas as pd
import json
import h3
import folium
from folium import plugins
import matplotlib.cm as cm
import matplotlib.colors as mcolors

def create_poi_hex_matcher(city_name="安庆市", control_visualization=True):
    """
    1. 读取安庆市.csv，识别所有商场（midType为"商场"）
    2. 加载所有POI
    3. 对每个商场，确定其分辨率7的H3网格，筛选所有落在该网格内的POI
    4. 将这些POI分配到分辨率12的小hex
    5. 输出每个商场的json和html（可选）
    control_visualization: 是否生成可视化HTML
    """
    # 路径配置
    csv_path = f'./in_city/csv/classified/{city_name}.csv'
    hex_json_path = f'./mart/json/{city_name}_商场网格_分辨率12.json'
    output_json_dir = f'./mart/json/{city_name}/'
    output_html_dir = f'./mart/html/{city_name}/'
    hex_resolution = 12
    big_hex_resolution = 7

    os.makedirs(output_json_dir, exist_ok=True)
    os.makedirs(output_html_dir, exist_ok=True)

    # 读取分辨率12的hex列表
    with open(hex_json_path, 'r', encoding='utf-8') as f:
        hex_data = json.load(f)
    subdivided_hexes = set(hex_data['subdivided_hexes'])

    # 读取所有POI
    df = pd.read_csv(csv_path, encoding='utf-8')
    # 解析location为经纬度
    df[['lng', 'lat']] = df['location'].str.split(',', expand=True)
    df['lng'] = df['lng'].astype(float)
    df['lat'] = df['lat'].astype(float)

    # 识别所有商场（midType为"商场"）
    malls = df[df['midType'] == '商场']
    print(f"识别到 {len(malls)} 个商场")

    # 主流程：对每个商场处理
    for idx, mall_row in malls.iterrows():
        mall_name = mall_row['name']
        mall_lat = mall_row['lat']
        mall_lng = mall_row['lng']
        # 商场所在分辨率7的hex
        mall_big_hex = h3.latlng_to_cell(mall_lat, mall_lng, big_hex_resolution)
        mall_big_hex_boundary = h3.cell_to_boundary(mall_big_hex)
        print(f"商场: {mall_name}，分辨率7 hex: {mall_big_hex}")
        # 筛选所有落在该hex内的POI
        pois_in_mall_hex = []
        for _, poi_row in df.iterrows():
            poi_lat = poi_row['lat']
            poi_lng = poi_row['lng']
            poi_big_hex = h3.latlng_to_cell(poi_lat, poi_lng, big_hex_resolution)
            if poi_big_hex == mall_big_hex:
                pois_in_mall_hex.append(poi_row)
        print(f"商场 {mall_name} 区域内POI数: {len(pois_in_mall_hex)}")
        # 分配到分辨率12的小hex
        hex_poi_map = {}
        for poi_row in pois_in_mall_hex:
            poi_lat = poi_row['lat']
            poi_lng = poi_row['lng']
            small_hex = h3.latlng_to_cell(poi_lat, poi_lng, hex_resolution)
            if small_hex not in subdivided_hexes:
                continue
            if small_hex not in hex_poi_map:
                hex_center = h3.cell_to_latlng(small_hex)
                hex_boundary = h3.cell_to_boundary(small_hex)
                hex_poi_map[small_hex] = {
                    'hex_id': small_hex,
                    'center': {'lat': hex_center[0], 'lng': hex_center[1]},
                    'boundary': hex_boundary,
                    'pois': [],
                    'poi_count': 0
                }
            # POI内容
            poi_info = {col: str(poi_row[col]) for col in df.columns}
            poi_info['lat'] = float(poi_row['lat'])
            poi_info['lng'] = float(poi_row['lng'])
            hex_poi_map[small_hex]['pois'].append(poi_info)
            hex_poi_map[small_hex]['poi_count'] += 1
        # 输出JSON
        safe_mall_name = mall_name.replace('/', '_').replace('\\', '_').replace(':', '_')
        json_path = os.path.join(output_json_dir, f'{safe_mall_name}.json')
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({'mall_name': mall_name, 'city': city_name, 'hexes': list(hex_poi_map.values())}, f, ensure_ascii=False, indent=2)
        print(f"已输出 {json_path}，包含 {len(hex_poi_map)} 个hex")
        # 可视化HTML（可选）
        if control_visualization:
            create_visualization_html(hex_poi_map, mall_name, output_html_dir, mall_big_hex_boundary)
            print(f"已为 '{mall_name}' 生成可视化HTML文件。")
    print(f"处理完成! 结果保存在 {output_json_dir} 和 {output_html_dir}")

def get_coldmap_color(val, vmin, vmax):
    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    cmap = cm.get_cmap('coolwarm')
    rgba = cmap(norm(val))
    return mcolors.to_hex(rgba)

def create_visualization_html(hex_poi_map, mall_name, output_html_dir, mall_big_hex_boundary):
    if not hex_poi_map:
        return
    # 计算地图中心点
    all_centers = [hex_data['center'] for hex_data in hex_poi_map.values()]
    center_lat = sum(c['lat'] for c in all_centers) / len(all_centers)
    center_lng = sum(c['lng'] for c in all_centers) / len(all_centers)
    m = folium.Map(location=[center_lat, center_lng], zoom_start=14, tiles='OpenStreetMap')
    # 画商场大hex边界
    folium.Polygon(
        locations=mall_big_hex_boundary,
        color='black',
        weight=4,
        opacity=0.7,
        fill=False,
        popup=f"商场大hex"
    ).add_to(m)
    # 统计小hex poi数量范围
    poi_counts = [hex_data['poi_count'] for hex_data in hex_poi_map.values()]
    vmin = min(poi_counts) if poi_counts else 0
    vmax = max(poi_counts) if poi_counts else 1
    # 画小hex，颜色用coldmap
    for hex_id, hex_data in hex_poi_map.items():
        color = get_coldmap_color(hex_data['poi_count'], vmin, vmax)
        folium.Polygon(
            locations=hex_data['boundary'],
            color=color,
            weight=2,
            opacity=0.8,
            fill=True,
            fillOpacity=0.5,
            popup=f"Hex: {hex_id}<br>POI数量: {hex_data['poi_count']}"
        ).add_to(m)
        for poi in hex_data['pois']:
            popup_text = f"""
            <b>{poi.get('name','')}</b><br>
            类型: {poi.get('midType','')}<br>
            地址: {poi.get('adname','')}<br>
            """
            folium.Marker(
                location=[poi['lat'], poi['lng']],
                popup=folium.Popup(popup_text, max_width=300),
                tooltip=poi.get('name',''),
                icon=folium.Icon(color='red', icon='info-sign')
            ).add_to(m)
    # 热力图层
    heat_data = [[poi['lat'], poi['lng']] for hex_data in hex_poi_map.values() for poi in hex_data['pois']]
    if heat_data:
        plugins.HeatMap(heat_data).add_to(m)
    # 图例
    legend_html = f"""
    <div style='position: fixed; top: 10px; right: 10px; width: 200px; height: auto; background-color: white; border:2px solid grey; z-index:9999; font-size:14px; padding: 10px'>
    <h4>{mall_name}</h4>
    <p><b>Hex数量:</b> {len(hex_poi_map)}</p>
    <p><b>POI数量范围:</b> {vmin} ~ {vmax}</p>
    <p><b>大hex边界为黑色</b></p>
    <p><b>小hex颜色表示POI数量</b></p>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))
    html_path = os.path.join(output_html_dir, f'{mall_name.replace('/', '_').replace('\\', '_').replace(':', '_')}.html')
    m.save(html_path)

if __name__ == "__main__":
    # 运行时可选择是否生成可视化
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--visual', action='store_true', help='是否生成可视化HTML')
    args = parser.parse_args()
    create_poi_hex_matcher("安庆市", control_visualization=args.visual)