# in city项目
## 项目介绍
 1. 该项目旨在通过对城市进行res=7的网格划分，通过poi聚合以确定商场所在hex的属性

 2. res=7的每个hex会为其上的每一个res=10的hex提供该地块具有的属性，数据存储在xxs 市_mart_hex_indicators.json 文件中，包括：
    1. res=7的hex的id
    2. res=7的hex的中心坐标
    3. res=7的hex的poi计数（不分种类）
    4. res=7的hex的big_type_count（大类poi计数）
    5. res=7的hex的mid_type_count（中类poi计数）
    6. res=7的hex的small_type_count（小类poi计数）
    7. 相邻的res=7的hex的id
    8. 相邻的res=7的hex的中心坐标

 3. 以上八项指标将作为该地块上的固有属性赋予所有该地块上res=10的hex，作为表征该地块的人流量的指标

 ## 数据来源
 本项目的数据主要来源于：
 1. 高德数据poi获取——获取该城市所有poi的名称，种类，位置；

 2. ox提供的地理数据；

 ## 使用说明
 1. 将城市的poi数据（xlsx文件）放在xlsx文件夹下即可，命名为城市名_poi.xlsx

 2. 运行main.python即可，main.python的主要内容如下
    1. 执行数据转换：xls_to_csv.py将xlsx文件夹下的城市数据转换为csv格式（若已执行，则会自动跳过）,存储至csv/unclassified/文件夹下，命名为xx市.csv;
    2. 进行数据分类：csv_converter.py将csv/unclassified/文件夹下的城市数据分类，分类后存储至csv/classified/文件夹下（若已执行，则会自动跳过），命名为xx市.csv;
    3. 城市网格划分：city_to_mesh.py将读取csv/classified/文件夹下的城市数据，进行网格划分，划分后存储至csv/json/文件夹下，命名为xx市_h3_grid.json，并会保存所有城市的汇总结果存储在相同目录下，命名为all_cities_h3_summary.json
    4. poi数据分配：poi_hex.py将读取城市poi数据csv文件，将poi数据分配到每个hex中，分配后存储至csv/json/文件夹下，命名为xx市_h3_hex.json，完成poi网格分配（是否已完成poi分配会通过检测，若已包含，则会跳过该城市）
    5. mart_hex信息聚合：mart_mesh.py将提取 4 中经过poi分配后的含有商场的hex，计算其上的poi的数量并包含poi大中小类别的所有信息，获取其相邻hex的id，center，poi计数，有无商场情况，数据整理后命名为xx市_mart_hex_analysis.json，保存至mart_hex_analyis目录下
    6. 可视化：
        1. 城市poi_grid可视化：json_visualization.py提供了可视化函数，可将城市的poi聚合后的grid可视化，以及所有城市的汇总地图，使用poi密度颜色编码。可视化结果html文件保存至html/xx市/下，png文件保存至png/xx市/下，分别命名为xx市_h3_poi_density_map.html，xx市_h3_poi_density_map.png，会更新all_cities_poi_density_overview.html，png文件保存在png/xx市下（不会进行重复保存）

        2. 城市mart_grid可视化：mart_hex_visualize提供了可视化函数，可根据商场hex分析结果在实际地图上进行可视化，可视化结果html保存至html/xx市/文件夹下，png保存至png/xx市/文件夹下，分别命名为xx市41_mart_hex_analysis_map.html，xx市_mart_hex_analysis_map.png

 3. 本文件夹为该地块上的所有小hex提供了8种基本属性，用于后续模型训练：
    1. 该小hex的中心坐标
    2. 该小hex的poi计数（不分种类）
    3. 该小hex的big_type_count（大类poi计数）
    4. 该小hex的mid_type_count（中类poi计数）
    5. 该小hex的small_type_count（小类poi计数）
    6. 该小hex的相邻的小hex的id
    7. 该小hex的相邻的小hex的中心坐标
    8. 该小hex的是否有商场



    
    