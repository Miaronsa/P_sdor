import os
import pandas as pd

def process_unclassified_csv():
    """
    处理csv目录中的CSV文件，仅保留指定的列
    首先检查csv/unclassified文件夹，然后检查csv根目录
    """
    csv_root_dir = r"e:\Deskep\P_sdor\in_city\csv"
    unclassified_dir = r"e:\Deskep\P_sdor\in_city\csv\unclassified"
    classified_dir = r"e:\Deskep\P_sdor\in_city\csv\classified"
    
    # 确保classified目录存在
    os.makedirs(classified_dir, exist_ok=True)
    
    # 指定要保留的列
    required_columns = ['id', 'name', 'location', 'pname', 'cityname', 'adname', 'bigType', 'midType', 'smallType']
    
    total_processed = 0
    total_skipped = 0
    
    # 首先处理unclassified目录中的CSV文件
    if os.path.exists(unclassified_dir):
        csv_files_unclassified = [f for f in os.listdir(unclassified_dir) if f.endswith('.csv')]
        if csv_files_unclassified:
            print(f"在unclassified目录中找到 {len(csv_files_unclassified)} 个CSV文件")
            processed, skipped = process_csv_files(csv_files_unclassified, unclassified_dir, classified_dir, required_columns)
            total_processed += processed
            total_skipped += skipped
        else:
            print("unclassified目录中没有找到CSV文件")
    
    # 然后处理CSV根目录中的CSV文件
    csv_files_root = [f for f in os.listdir(csv_root_dir) 
                      if f.endswith('.csv') and os.path.isfile(os.path.join(csv_root_dir, f))]
    
    if csv_files_root:
        print(f"在csv根目录中找到 {len(csv_files_root)} 个CSV文件")
        processed, skipped = process_csv_files(csv_files_root, csv_root_dir, classified_dir, required_columns)
        total_processed += processed
        total_skipped += skipped
    else:
        print("csv根目录中没有找到CSV文件")
    
    print(f"\n处理完成！总计: {total_processed} 个文件已处理, {total_skipped} 个文件已跳过")

def process_csv_files(csv_files, input_dir, output_dir, required_columns):
    """
    处理指定目录中的CSV文件列表
    返回 (processed_count, skipped_count)
    """
    processed_count = 0
    skipped_count = 0
    
    for filename in csv_files:
        input_path = os.path.join(input_dir, filename)
        output_path = os.path.join(output_dir, filename)
        
        # 检查classified目录中是否已经存在目标CSV文件
        if os.path.exists(output_path):
            print(f"跳过 {filename}，classified目录中已存在目标文件")
            skipped_count += 1
            continue
        
        try:
            print(f"正在处理: {filename}")
            
            # 读取CSV文件
            df = pd.read_csv(input_path, encoding='utf-8')
            
            # 检查哪些必需列存在
            existing_columns = []
            missing_columns = []
            
            for col in required_columns:
                if col in df.columns:
                    existing_columns.append(col)
                else:
                    missing_columns.append(col)
            
            if missing_columns:
                print(f"  警告: 文件 {filename} 缺少列: {missing_columns}")
            
            if existing_columns:
                # 只保留存在的必需列
                df_filtered = df[existing_columns].copy()
                
                # 保存处理后的文件到classified目录
                df_filtered.to_csv(output_path, index=False, encoding='utf-8-sig')
                print(f"  处理完成: {filename} (保留了 {len(existing_columns)} 列)")
                print(f"  保留的列: {existing_columns}")
                processed_count += 1
            else:
                print(f"  错误: 文件 {filename} 不包含任何必需的列")
                
        except Exception as e:
            print(f"  处理文件 {filename} 时出错: {str(e)}")
    
    return processed_count, skipped_count

if __name__ == "__main__":
    process_unclassified_csv()