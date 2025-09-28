from django.db import models

class EquipmentType(models.Model):
    name = models.CharField(max_length=100)   # 設備種類名稱
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "設備種類"
        verbose_name_plural = "設備種類"

class Devices(models.Model):
    equipment_type = models.ForeignKey(EquipmentType, on_delete=models.CASCADE)  # 設備種類
    brand = models.CharField(max_length=100)              # 廠牌及用途
    specification = models.CharField(max_length=100)       # 規格
    power_info = models.CharField(max_length=50)           # 使用電流及電壓
    date_installed = models.DateField()                    # 出廠/安裝日期
    maintenance_cycle = models.CharField(max_length=20)    # 維修保養周期
    warranty_period = models.CharField(max_length=50)      # 保固時程
    contractor_name = models.CharField(max_length=100)     # 施工廠商名稱
    contractor_phone = models.CharField(max_length=20)     # 施工廠商電話
    installer_name = models.CharField(max_length=50)       # 安裝人員姓名
    installer_phone = models.CharField(max_length=20)      # 安裝人員電話
    emergency_name = models.CharField(max_length=50)       # 緊急維修人員姓名
    emergency_phone = models.CharField(max_length=20)      # 緊急維修人員電話
    maintenance_name = models.CharField(max_length=50)     # 負責維修人員姓名
    maintenance_phone = models.CharField(max_length=20)    # 負責維修人員電話
    
    def __str__(self):
        return f"{self.equipment_type.name} - {self.brand} ({self.specification})"
    
    class Meta:
        verbose_name = "設備"
        verbose_name_plural = "設備"