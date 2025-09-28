import json
import os
from datetime import datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from devices.models import EquipmentType, Devices


class Command(BaseCommand):
    help = '載入 sample_data.json 資料到資料庫'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            default='devices/sample_data.json',
            help='指定 JSON 檔案路徑 (預設: devices/sample_data.json)'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        
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
                for device_data in data.get('devices', []):
                    # 取得設備種類
                    try:
                        equipment_type = EquipmentType.objects.get(
                            name=device_data['equipment_type']
                        )
                    except EquipmentType.DoesNotExist:
                        self.stdout.write(
                            self.style.ERROR(
                                f'找不到設備種類: {device_data["equipment_type"]}'
                            )
                        )
                        continue
                    
                    # 處理日期格式 (從 "2024/11/19" 轉換為 datetime.date)
                    date_str = device_data['date_installed']
                    try:
                        date_installed = datetime.strptime(date_str, '%Y/%m/%d').date()
                    except ValueError:
                        self.stdout.write(
                            self.style.ERROR(
                                f'日期格式錯誤: {date_str}，應為 YYYY/MM/DD'
                            )
                        )
                        continue
                    
                    # 建立設備
                    device = Devices.objects.create(
                        equipment_type=equipment_type,
                        brand=device_data['brand'],
                        specification=device_data['specification'],
                        power_info=device_data['power_info'],
                        date_installed=date_installed,
                        maintenance_cycle=device_data['maintenance_cycle'],
                        warranty_period=device_data['warranty_period'],
                        contractor_name=device_data['contractor_name'],
                        contractor_phone=device_data['contractor_phone'],
                        installer_name=device_data['installer_name'],
                        installer_phone=device_data['installer_phone'],
                        emergency_name=device_data['emergency_name'],
                        emergency_phone=device_data['emergency_phone'],
                        maintenance_name=device_data['maintenance_name'],
                        maintenance_phone=device_data['maintenance_phone']
                    )
                    devices_created += 1
                    self.stdout.write(f'建立設備: {device.specification}')
                
            # 顯示結果
            self.stdout.write(
                self.style.SUCCESS(
                    f'資料載入完成！'
                    f'新增了 {equipment_types_created} 個設備種類、{devices_created} 個設備'
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
