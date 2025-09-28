from devices.models import EquipmentType, Devices

print(f'設備種類數量: {EquipmentType.objects.count()}')
print(f'設備數量: {Devices.objects.count()}')

print('\n=== 設備種類 ===')
for et in EquipmentType.objects.all():
    print(f'- {et.name}')

print('\n=== 前5個設備 ===')
for device in Devices.objects.all()[:5]:
    print(f'- {device.specification} ({device.equipment_type.name})')
    print(f'  廠牌: {device.brand}')
    print(f'  安裝日期: {device.date_installed}')
    print('---')
