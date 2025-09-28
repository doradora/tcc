import csv
import json
import re
from datetime import datetime

def parse_csv_to_json(csv_file_path, json_file_path):
    """解析 CSV 檔案並轉換為 JSON 格式"""
    
    equipment_types = set()
    devices = []
    
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        current_device = {}
        
        for row in csv_reader:
            # 跳過空行
            if not any(row):
                continue
                
            # 檢查是否為設備開始行（包含中文數字和設備種類）
            if row[0] and row[1] and not row[0].isdigit():
                # 如果有之前的設備資料，先保存
                if current_device:
                    devices.append(current_device)
                    current_device = {}
                
                # 開始新設備
                equipment_type = row[1]
                equipment_types.add(equipment_type)
                current_device = {
                    'equipment_type': equipment_type
                }
            
            # 檢查是否為資料行（第一欄為數字）
            elif row[0].isdigit() and len(row) >= 3:
                field_num = int(row[0])
                field_value = row[2]
                
                # 根據欄位編號映射到對應的屬性
                if field_num == 1:  # 廠牌及用途
                    current_device['brand'] = field_value
                elif field_num == 2:  # 規格
                    current_device['specification'] = field_value
                elif field_num == 3:  # 使用電流及電壓
                    current_device['power_info'] = field_value
                elif field_num == 4:  # 出廠/安裝日期
                    current_device['date_installed'] = field_value
                elif field_num == 5:  # 維修保養周期
                    current_device['maintenance_cycle'] = field_value
                elif field_num == 6:  # 保固時程
                    current_device['warranty_period'] = field_value
                elif field_num == 7:  # 施工廠商名稱及電話
                    # 分離名稱和電話
                    parts = field_value.split(' ')
                    if len(parts) >= 2:
                        current_device['contractor_name'] = parts[0]
                        current_device['contractor_phone'] = parts[1]
                    else:
                        current_device['contractor_name'] = field_value
                        current_device['contractor_phone'] = ''
                elif field_num == 8:  # 安裝人員姓名及電話
                    parts = field_value.split(' ')
                    if len(parts) >= 3:
                        current_device['installer_name'] = f"{parts[0]} {parts[1]}"
                        current_device['installer_phone'] = parts[2]
                    else:
                        current_device['installer_name'] = field_value
                        current_device['installer_phone'] = ''
                elif field_num == 9:  # 緊急維修人員姓名及電話
                    parts = field_value.split(' ')
                    if len(parts) >= 3:
                        current_device['emergency_name'] = f"{parts[0]} {parts[1]}"
                        current_device['emergency_phone'] = parts[2]
                    else:
                        current_device['emergency_name'] = field_value
                        current_device['emergency_phone'] = ''
                elif field_num == 10:  # 負責維修人員姓名及電話
                    parts = field_value.split(' ')
                    if len(parts) >= 3:
                        current_device['maintenance_name'] = f"{parts[0]} {parts[1]}"
                        current_device['maintenance_phone'] = parts[2]
                    else:
                        current_device['maintenance_name'] = field_value
                        current_device['maintenance_phone'] = ''
        
        # 保存最後一個設備
        if current_device:
            devices.append(current_device)
    
    # 建立 JSON 結構
    json_data = {
        'equipment_types': [{'name': et} for et in sorted(equipment_types)],
        'devices': devices
    }
    
    # 寫入 JSON 檔案
    with open(json_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(json_data, json_file, ensure_ascii=False, indent=2)
    
    print(f"轉換完成！")
    print(f"設備種類數量: {len(equipment_types)}")
    print(f"設備數量: {len(devices)}")
    print(f"設備種類: {list(equipment_types)}")

if __name__ == "__main__":
    csv_file = "devices/testimport.csv"
    json_file = "devices/all_devices.json"
    
    parse_csv_to_json(csv_file, json_file)
