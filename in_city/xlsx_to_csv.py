import os
import pandas as pd

def process_all_xlsx():
    """
    将xlsx文件夹下的所有xlsx文件转换为csv，并保存到csv/unclassified/目录下。
    如果目标文件已存在，则跳过。
    """
    # 定义源目录和目标目录
    base_dir = os.path.dirname(os.path.abspath(__file__))
    xlsx_dir = os.path.join(base_dir, "xlsx")
    output_dir = os.path.join(base_dir, "csv", "unclassified")
    
    # 确保目录存在
    os.makedirs(output_dir, exist_ok=True)

    # 检查源目录是否存在
    if not os.path.exists(xlsx_dir):
        print(f"错误：源目录不存在: {xlsx_dir}")
        return

    print(f"开始处理目录: {xlsx_dir}")
    for filename in os.listdir(xlsx_dir):
        if filename.endswith('.xlsx'):
            xlsx_path = os.path.join(xlsx_dir, filename)
            csv_filename = filename.replace('.xlsx', '.csv')
            csv_path = os.path.join(output_dir, csv_filename)
            
            # 检查目标文件夹中是否已经存在CSV文件
            if os.path.exists(csv_path):
                print(f'跳过 {filename}，目标文件已存在: {csv_path}')
                continue
                
            try:
                print(f'正在转换: {filename}')
                df = pd.read_excel(xlsx_path)
                df.to_csv(csv_path, index=False, encoding='utf-8-sig')
                print(f'  -> 转换完成: {csv_path}')
            except Exception as e:
                print(f"  转换文件 {filename} 时出错: {e}")
            
    print('所有XLSX文件转换完成！')

if __name__ == "__main__":
    process_all_xlsx()
