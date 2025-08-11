import os
import pandas as pd

xlsx_dir = r"e:\Deskep\Final\city\xlsx"
csv_dir = r"e:\Deskep\Final\city\csv"
os.makedirs(csv_dir, exist_ok=True)

for filename in os.listdir(xlsx_dir):
    if filename.endswith('.xlsx'):
        xlsx_path = os.path.join(xlsx_dir, filename)
        csv_filename = filename.replace('.xlsx', '.csv')
        csv_path = os.path.join(csv_dir, csv_filename)
        df = pd.read_excel(xlsx_path)
        df.to_csv(csv_path, index=False, encoding='utf-8-sig')
print('转换完成！')
