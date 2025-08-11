import os
import pandas as pd

xlsx_dir = r"e:\Deskep\Final\in_city\xlsx"
csv_dir = r"e:\Deskep\Final\in_city\csv"
classified_dir = os.path.join(csv_dir, "unclassified")
os.makedirs(csv_dir, exist_ok=True)
os.makedirs(classified_dir, exist_ok=True)

for filename in os.listdir(xlsx_dir):
    if filename.endswith('.xlsx'):
        xlsx_path = os.path.join(xlsx_dir, filename)
        csv_filename = filename.replace('.xlsx', '.csv')
        csv_path = os.path.join(csv_dir, csv_filename)
        classified_csv_path = os.path.join(classified_dir, csv_filename)
        
        # 检查classified文件夹中是否已经存在目标CSV文件
        if os.path.exists(classified_csv_path):
            print(f'跳过 {filename}，目标文件已存在: {classified_csv_path}')
            continue
            
        print(f'正在转换: {filename}')
        df = pd.read_excel(xlsx_path)
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
        print(f'转换完成: {csv_filename}')
        
print('所有转换完成！')
