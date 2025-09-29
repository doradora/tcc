import csv
import json
import re
from datetime import datetime

def parse_csv_to_json(csv_file_path, json_file_path):
    """解析 CSV 檔案並轉換為 JSON 格式"""
    
    # 建立中文欄位名稱到JSON屬性的映射
    field_mapping = {
        '廠牌及用途': 'brand',
        '規格': 'specification',
        '使用電流及電壓': 'power_info',
        '出廠/按裝日期': 'date_installed',
        '出廠/安裝日期': 'date_installed',  # 處理不同的寫法
        '維修保養周期': 'maintenance_cycle',
        '保固時程': 'warranty_period',
        '施工廠商名稱及電話': 'contractor_info',
        '安裝人員姓名及電話': 'installer_info', 
        '按裝人員姓名及電話': 'installer_info', # 處理不同的寫法
        '緊急維修人員姓名及電話': 'emergency_info',
        '負責維修人員姓名及電話': 'maintenance_info'
    }
    
    equipment_types = set()
    devices = []
    
    with open(csv_file_path, 'r', encoding='utf-8') as file:
        csv_reader = csv.reader(file)
        current_device = {}
        consecutive_empty_rows = 0
        
        for row in csv_reader:
            # 檢查是否為空行
            if not any(row):
                consecutive_empty_rows += 1
                continue
            
            # 重置空行計數器
            consecutive_empty_rows = 0
                
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
                field_name = row[1]  # 取得中文欄位名稱
                field_value = row[2]  # 取得欄位值
                
                # 根據中文欄位名稱映射到對應的屬性
                if field_name in field_mapping:
                    property_name = field_mapping[field_name]
                    
                    # 處理需要分離姓名電話的欄位
                    if property_name in ['contractor_info', 'installer_info', 'emergency_info', 'maintenance_info']:
                        parts = field_value.split(' ')
                        
                        if property_name == 'contractor_info':
                            # 施工廠商名稱及電話 (公司名稱 電話)
                            if len(parts) >= 2:
                                current_device['contractor_name'] = parts[0]
                                current_device['contractor_phone'] = parts[1]
                            else:
                                current_device['contractor_name'] = field_value
                                current_device['contractor_phone'] = ''
                                
                        elif property_name in ['installer_info', 'emergency_info', 'maintenance_info']:
                            # 人員姓名及電話 (通常格式: 公司 姓名 電話)
                            if len(parts) >= 3:
                                name_key = property_name.replace('_info', '_name')
                                phone_key = property_name.replace('_info', '_phone')
                                current_device[name_key] = f"{parts[0]} {parts[1]}"
                                current_device[phone_key] = parts[2]
                            else:
                                name_key = property_name.replace('_info', '_name')
                                phone_key = property_name.replace('_info', '_phone')
                                current_device[name_key] = field_value
                                current_device[phone_key] = ''
                    else:
                        # 直接映射的欄位
                        current_device[property_name] = field_value
                else:
                    # 如果找不到對應的映射，可以記錄未知欄位（可選）
                    print(f"未知欄位: {field_name} = {field_value}")
        
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
