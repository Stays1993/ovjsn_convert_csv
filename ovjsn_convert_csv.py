import json
import csv
import re
import os
from datetime import datetime

def parse_comment(comment):
    """解析Comment字符串，返回设备名到数量的字典"""
    if not comment:
        return {}
    lines = comment.split('\r\n')
    devices = {}
    for line in lines:
        line = line.strip()
        if not line:
            continue
        match = re.match(r'([^×x]+)[×x](\d+)', line)
        if match:
            name = match.group(1).strip()
            count = int(match.group(2))
            devices[name] = count
        else:
            devices[line] = 1
    return devices

def convert_json_to_csv(input_path, output_path, timestamp):
    """转换单个.ovjsn文件到CSV，文件名前加时间戳"""
    with open(input_path, 'r', encoding='utf-8-sig') as f:
        data = json.load(f)
    
    obj_items = data.get('ObjItems', [])
    if not obj_items:
        print(f"警告: {input_path} 中未找到 ObjItems，跳过")
        return
    
    first_item = obj_items[0]
    folder_obj = first_item.get('Object', {})
    original_name = folder_obj.get('Name', 'output')
    original_name = original_name.replace('/', '_').replace('\\', '_')
    csv_filename = f"{timestamp}_{original_name}.csv"
    full_output_path = os.path.join(output_path, csv_filename)
    
    obj_detail = folder_obj.get('ObjectDetail', {})
    children = obj_detail.get('ObjChildren', [])
    
    all_devices = set()
    rows_data = []
    for child in children:
        child_obj = child.get('Object', {})
        name = child_obj.get('Name', '')
        comment = child_obj.get('Comment', '')
        devices = parse_comment(comment)
        rows_data.append({'Name': name, 'devices': devices})
        all_devices.update(devices.keys())
    
    sorted_devices = sorted(all_devices)
    
    with open(full_output_path, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Name'] + sorted_devices)
        for row in rows_data:
            row_list = [row['Name']]
            for dev in sorted_devices:
                count = row['devices'].get(dev, '')
                row_list.append(count if count != '' else '')
            writer.writerow(row_list)
    
    print(f"已转换: {os.path.basename(input_path)} -> {csv_filename} ({len(rows_data)} 条记录, {len(sorted_devices)} 种设备)")

def main():
    base_dir = os.path.dirname(os.path.abspath(__file__))
    input_dir = os.path.join(base_dir, 'input')
    output_dir = os.path.join(base_dir, 'output')
    
    os.makedirs(output_dir, exist_ok=True)
    
    if not os.path.exists(input_dir):
        print(f"错误: 输入目录不存在 - {input_dir}")
        return
    
    ovjsn_files = [f for f in os.listdir(input_dir) if f.lower().endswith('.ovjsn')]
    if not ovjsn_files:
        print(f"输入目录中没有 .ovjsn 文件: {input_dir}")
        return
    
    # 生成时间戳（年月日_时分秒）
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    print(f"找到 {len(ovjsn_files)} 个 .ovjsn 文件，开始转换... (时间戳: {timestamp})")
    for file_name in ovjsn_files:
        input_path = os.path.join(input_dir, file_name)
        convert_json_to_csv(input_path, output_dir, timestamp)
    
    print(f"转换完成，输出目录: {output_dir}")

if __name__ == '__main__':
    main()