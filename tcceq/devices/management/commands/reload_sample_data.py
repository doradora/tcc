import json
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from devices.models import EquipmentType, Devices


class Command(BaseCommand):
    help = '清除現有資料並重新載入更新後的 sample_data.json 資料到資料庫'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='devices/all_devices.json',
            help='指定 JSON 檔案路徑 (預設: devices/all_devices.json)'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='清除現有資料'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        clear_existing = options['clear_existing']
        
        # 確認檔案存在
        if not os.path.exists(file_path):
            self.stdout.write(
                self.style.ERROR(f'檔案不存在: {file_path}')
            )
            return

        try:
            # 讀取 JSON 檔案
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            self.stdout.write('開始載入資料...')
            
            with transaction.atomic():
                # 清除現有資料（如果指定）
                if clear_existing:
                    devices_deleted = Devices.objects.count()
                    equipment_types_deleted = EquipmentType.objects.count()
                    
                    Devices.objects.all().delete()
                    EquipmentType.objects.all().delete()
                    
                    self.stdout.write(f'已清除 {devices_deleted} 個設備和 {equipment_types_deleted} 個設備種類')
                
                # 載入設備種類
                equipment_types_created = 0
                for et_data in data.get('equipment_types', []):
                    equipment_type, created = EquipmentType.objects.get_or_create(
                        name=et_data['name']
                    )
                    if created:
                        equipment_types_created += 1
                        self.stdout.write(f'建立設備種類: {equipment_type.name}')
                
                # 載入設備資料
                devices_created = 0
                devices_skipped = 0
                
                for device_data in data.get('devices', []):
                    # 檢查是否有設備種類
                    if 'equipment_type' not in device_data or not device_data['equipment_type']:
                        devices_skipped += 1
                        self.stdout.write(
                            self.style.WARNING(f'跳過設備（缺少設備種類）: {device_data.get("specification", "未知規格")}')
                        )
                        continue
                    
                    # 取得設備種類
                    try:
                        equipment_type = EquipmentType.objects.get(
                            name=device_data['equipment_type']
                        )
                    except EquipmentType.DoesNotExist:
                        # 如果設備種類不存在，自動建立
                        equipment_type = EquipmentType.objects.create(
                            name=device_data['equipment_type']
                        )
                        self.stdout.write(f'自動建立設備種類: {equipment_type.name}')
                    
                    # 處理安裝日期 - 如果沒有提供則使用預設值
                    date_installed = None
                    if 'date_installed' in device_data and device_data['date_installed']:
                        date_str = device_data['date_installed']
                        try:
                            date_installed = datetime.strptime(date_str, '%Y/%m/%d').date()
                        except ValueError:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'日期格式錯誤: {date_str}，將使用預設日期'
                                )
                            )
                            # 使用預設日期 (例如：2024/1/1)
                            date_installed = datetime(2024, 1, 1).date()
                    else:
                        # 如果沒有提供日期，使用預設日期
                        date_installed = datetime(2024, 1, 1).date()
                        self.stdout.write(
                            self.style.WARNING(
                                f'設備缺少安裝日期，使用預設日期 2024/1/1: {device_data.get("brand", "未知品牌")}'
                            )
                        )
                    
                    # 檢查是否已存在相同規格的設備（避免重複）
                    if device_data.get('specification') and Devices.objects.filter(
                        equipment_type=equipment_type,
                        specification=device_data['specification']
                    ).exists():
                        devices_skipped += 1
                        self.stdout.write(f'設備已存在，跳過: {device_data["specification"]}')
                        continue
                    
                    # 建立設備 - 為每個欄位提供預設值
                    device = Devices.objects.create(
                        equipment_type=equipment_type,
                        brand=device_data.get('brand', ''),
                        specification=device_data.get('specification', ''),
                        power_info=device_data.get('power_info', ''),
                        date_installed=date_installed,
                        maintenance_cycle=device_data.get('maintenance_cycle', ''),
                        warranty_period=device_data.get('warranty_period', ''),
                        contractor_name=device_data.get('contractor_name', ''),
                        contractor_phone=device_data.get('contractor_phone', ''),
                        installer_name=device_data.get('installer_name', ''),
                        installer_phone=device_data.get('installer_phone', ''),
                        emergency_name=device_data.get('emergency_name', ''),
                        emergency_phone=device_data.get('emergency_phone', ''),
                        maintenance_name=device_data.get('maintenance_name', ''),
                        maintenance_phone=device_data.get('maintenance_phone', '')
                    )
                    devices_created += 1
                    if devices_created % 50 == 0:  # 每50個設備顯示一次進度
                        self.stdout.write(f'已建立 {devices_created} 個設備...')
                
            # 顯示結果
            total_equipment_types = EquipmentType.objects.count()
            total_devices = Devices.objects.count()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'資料載入完成！'
                    f'新增了 {equipment_types_created} 個設備種類、{devices_created} 個設備'
                )
            )
            
            if devices_skipped > 0:
                self.stdout.write(
                    self.style.WARNING(f'跳過了 {devices_skipped} 個設備（重複或資料不完整）')
                )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'目前資料庫中共有 {total_equipment_types} 個設備種類、{total_devices} 個設備'
                )
            )
            
        except json.JSONDecodeError as e:
            self.stdout.write(
                self.style.ERROR(f'JSON 檔案格式錯誤: {e}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'載入資料時發生錯誤: {e}')
            )
