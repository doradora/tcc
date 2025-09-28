import json
from django.core.management.base import BaseCommand
from django.db import transaction
from devices.models import EquipmentType, Devices
from datetime import datetime

class Command(BaseCommand):
    help = '從 JSON 檔案匯入設備資料'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='JSON 檔案路徑',
            default='devices/import_template.json'
        )

    def handle(self, *args, **options):
        file_path = options['file']
        
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
            
            with transaction.atomic():
                # 先匯入設備類型
                equipment_types_created = 0
                for eq_type_data in data.get('equipment_types', []):
                    equipment_type, created = EquipmentType.objects.get_or_create(
                        name=eq_type_data['name']
                    )
                    if created:
                        equipment_types_created += 1
                        self.stdout.write(
                            self.style.SUCCESS(f'建立設備類型: {equipment_type.name}')
                        )
                
                # 再匯入設備
                devices_created = 0
                for device_data in data.get('devices', []):
                    try:
                        # 取得設備類型
                        equipment_type = EquipmentType.objects.get(
                            name=device_data['equipment_type']
                        )
                        
                        # 檢查是否已存在相同設備
                        existing_device = Devices.objects.filter(
                            equipment_type=equipment_type,
                            brand=device_data['brand'],
                            specification=device_data['specification']
                        ).first()
                        
                        if existing_device:
                            self.stdout.write(
                                self.style.WARNING(
                                    f'設備已存在，跳過: {device_data["brand"]} - {device_data["specification"]}'
                                )
                            )
                            continue
                        
                        # 建立新設備
                        device = Devices.objects.create(
                            equipment_type=equipment_type,
                            brand=device_data['brand'],
                            specification=device_data['specification'],
                            power_info=device_data['power_info'],
                            date_installed=datetime.strptime(device_data['date_installed'], '%Y-%m-%d').date(),
                            maintenance_cycle=device_data['maintenance_cycle'],
                            warranty_period=device_data['warranty_period'],
                            contractor_name=device_data['contractor_name'],
                            contractor_phone=device_data['contractor_phone'],
                            installer_name=device_data['installer_name'],
                            installer_phone=device_data['installer_phone'],
                            emergency_name=device_data['emergency_name'],
                            emergency_phone=device_data['emergency_phone'],
                            maintenance_name=device_data['maintenance_name'],
                            maintenance_phone=device_data['maintenance_phone'],
                        )
                        devices_created += 1
                        self.stdout.write(
                            self.style.SUCCESS(
                                f'建立設備: {device.brand} - {device.specification}'
                            )
                        )
                    
                    except EquipmentType.DoesNotExist:
                        self.stdout.write(
                            self.style.ERROR(
                                f'找不到設備類型: {device_data["equipment_type"]}'
                            )
                        )
                        continue
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                f'建立設備時發生錯誤: {device_data.get("brand", "未知")} - {str(e)}'
                            )
                        )
                        continue
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'匯入完成！建立了 {equipment_types_created} 個設備類型和 {devices_created} 個設備'
                )
            )
        
        except FileNotFoundError:
            self.stdout.write(
                self.style.ERROR(f'找不到檔案: {file_path}')
            )
        except json.JSONDecodeError as e:
            self.stdout.write(
                self.style.ERROR(f'JSON 格式錯誤: {str(e)}')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'匯入時發生錯誤: {str(e)}')
            )
