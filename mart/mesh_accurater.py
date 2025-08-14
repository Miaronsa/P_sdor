import json
import os
import h3
import folium
from folium import plugins
import numpy as np
from datetime import datetime
import argparse

class MeshAccurater:
    def __init__(self):
        self.input_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../in_city/json"))
        self.html_output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../mart/html"))
        self.json_output_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../mart/json"))
        self.target_resolution = 12
        # 确保输出目录存在
        os.makedirs(self.html_output_dir, exist_ok=True)
        os.makedirs(self.json_output_dir, exist_ok=True)
        
    def load_city_data(self, filename):
        """加载城市的hex网格数据"""
        filepath = os.path.join(self.input_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"加载文件 {filename} 失败: {e}")
            return None
    
    def find_mall_hexes(self, city_data):
        """找到包含商场的hex"""
        mall_hexes = []
        mall_keywords = ['商场', '购物', '商城', '百货', '超市', '大型超市', '商业综合体', 
                        '购物中心', '商业中心', 'mall', 'shopping']
        
        for hex_data in city_data.get('hexes', []):
            pois = hex_data.get('pois', [])
            poi_types = hex_data.get('poi_type_distribution', {})
            
            # 检查POI类型分布
            has_mall = False
            for poi_type in poi_types.keys():
                if any(keyword in poi_type.lower() for keyword in mall_keywords):
                    has_mall = True
                    break
            
            # 如果没有在类型中找到，检查具体POI
            if not has_mall:
                for poi in pois:
                    poi_name = poi.get('name', '').lower()
                    poi_type = poi.get('type', '').lower()
                    if any(keyword in poi_name or keyword in poi_type for keyword in mall_keywords):
                        has_mall = True
                        break
            
            if has_mall:
                mall_hexes.append(hex_data)
                
        return mall_hexes
    
    def subdivide_hex_to_resolution_12(self, hex_index):
        """将hex细分到分辨率12"""
        try:
            # 获取当前hex的分辨率
            current_res = h3.get_resolution(hex_index)
            
            if current_res >= self.target_resolution:
                return [hex_index]
            
            # 递归细分到目标分辨率
            children = [hex_index]
            for res in range(current_res + 1, self.target_resolution + 1):
                new_children = []
                for child in children:
                    new_children.extend(h3.cell_to_children(child, res))
                children = new_children
                
            return children
        except Exception as e:
            print(f"细分hex {hex_index} 失败: {e}")
            return []
    
    # def create_visualization_map(self, city_name, mall_hexes, subdivided_data):
    #     """创建可视化地图（已禁用）"""
    #     pass
        
    def process_city(self, filename, control_visualization=True):
        """处理单个城市的数据"""
        print(f"\n处理文件: {filename}")
        
        # 加载数据
        city_data = self.load_city_data(filename)
        if not city_data:
            return
            
        city_name = city_data.get('city_name', filename.replace('_h3_grid.json', ''))
        print(f"城市: {city_name}")
        
        # 找到商场hex
        mall_hexes = self.find_mall_hexes(city_data)
        print(f"找到商场hex数量: {len(mall_hexes)}")
        
        if not mall_hexes:
            print(f"{city_name}: 未找到商场数据")
            return
            
        # 细分hex到分辨率12
        all_subdivided_hexes = []
        hex_details = []
        
        for hex_data in mall_hexes:
            hex_index = hex_data.get('h3_index')
            if hex_index:
                subdivided = self.subdivide_hex_to_resolution_12(hex_index)
                all_subdivided_hexes.extend(subdivided)
                
                hex_details.append({
                    'original_hex': hex_index,
                    'subdivided_count': len(subdivided),
                    'subdivided_hexes': subdivided,
                    'poi_count': hex_data.get('poi_count', 0),
                    'center': hex_data.get('center', [])
                })
        
        print(f"细分后总hex数量: {len(all_subdivided_hexes)}")
        
        # 输出文件路径
        json_output_file = os.path.join(self.json_output_dir, f"{city_name}_商场网格_分辨率12.json")
        html_output_file = os.path.join(self.html_output_dir, f"{city_name}_商场网格分析.html")

        # 如果目标文件已存在则跳过
        if os.path.exists(json_output_file) and os.path.exists(html_output_file):
            print(f"{city_name}: 已存在结果文件，跳过生成。")
            return

        # 准备输出数据
        output_data = {
            'city_name': city_name,
            'processing_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'original_resolution': city_data.get('resolution', 7),
            'target_resolution': self.target_resolution,
            'original_mall_hexes': len(mall_hexes),
            'subdivided_hexes_count': len(all_subdivided_hexes),
            'subdivided_hexes': list(set(all_subdivided_hexes)),  # 去重
            'hex_details': hex_details
        }

        # 保存JSON数据（仅当文件不存在时保存）
        if not os.path.exists(json_output_file):
            with open(json_output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, ensure_ascii=False, indent=2)
            print(f"JSON数据已保存: {json_output_file}")
        else:
            print(f"JSON文件已存在: {json_output_file}")

    # 创建可视化地图（已禁用）
    # if control_visualization:
    #     if not os.path.exists(html_output_file):
    #         self.create_visualization_map(city_name, mall_hexes, output_data)
    #     else:
    #         print(f"HTML文件已存在: {html_output_file}")

    def process_all_cities(self, control_visualization=False):
        """处理所有城市数据"""
        print("开始处理所有城市的商场网格数据...")
        
        # 获取所有JSON文件
        json_files = [f for f in os.listdir(self.input_dir) if f.endswith('_h3_grid.json')]
        
        if not json_files:
            print(f"在目录 {self.input_dir} 中未找到城市数据文件")
            return
            
        print(f"找到 {len(json_files)} 个城市数据文件")
        
        for filename in json_files:
                try:
                    self.process_city(filename, control_visualization=True)
                except Exception as e:
                    print(f"处理 {filename} 时出错: {e}")
                
        print("\n所有城市处理完成！")
        print(f"HTML文件保存在: {os.path.abspath(self.html_output_dir)}")
        print(f"JSON文件保存在: {os.path.abspath(self.json_output_dir)}")

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="商场网格处理与可视化")
    parser.add_argument('--visual', action='store_true', help='是否生成可视化HTML')
    args = parser.parse_args()

    accurater = MeshAccurater()
    accurater.process_all_cities(control_visualization=args.visual)

if __name__ == "__main__":
    main()
