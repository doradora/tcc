from django.contrib import admin
from .models import EquipmentType, Devices

# 註冊設備種類模型
@admin.register(EquipmentType)
class EquipmentTypeAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']

# 註冊設備模型
@admin.register(Devices)
class DevicesAdmin(admin.ModelAdmin):
    list_display = ['equipment_type', 'brand', 'specification', 'date_installed', 'contractor_name']
    list_filter = ['equipment_type', 'date_installed']
    search_fields = ['brand', 'specification', 'contractor_name']
    date_hierarchy = 'date_installed'
    
    # 將欄位分組顯示
    fieldsets = (
        ('基本資訊', {
            'fields': ('equipment_type', 'brand', 'specification', 'power_info', 'date_installed')
        }),
        ('維修資訊', {
            'fields': ('maintenance_cycle', 'warranty_period')
        }),
        ('施工廠商', {
            'fields': ('contractor_name', 'contractor_phone')
        }),
        ('安裝人員', {
            'fields': ('installer_name', 'installer_phone')
        }),
        ('維修人員', {
            'fields': ('emergency_name', 'emergency_phone', 'maintenance_name', 'maintenance_phone')
        }),
    )
