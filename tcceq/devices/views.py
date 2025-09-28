from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db import models
from .models import Devices, EquipmentType

def device_list(request):
    """設備列表檢視"""
    devices = Devices.objects.all().select_related('equipment_type').order_by('equipment_type__name', 'brand')
    
    # 設備類型篩選
    equipment_type_id = request.GET.get('type')
    if equipment_type_id:
        devices = devices.filter(equipment_type_id=equipment_type_id)
    
    # 搜尋功能
    search_query = request.GET.get('search')
    if search_query:
        devices = devices.filter(
            models.Q(brand__icontains=search_query) |
            models.Q(specification__icontains=search_query) |
            models.Q(contractor_name__icontains=search_query)
        )
    
    # 分頁功能
    paginator = Paginator(devices, 10)  # 每頁顯示 10 個設備
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # 取得所有設備類型用於篩選下拉選單
    equipment_types = EquipmentType.objects.all()
    
    context = {
        'page_obj': page_obj,
        'equipment_types': equipment_types,
        'current_type': equipment_type_id,
        'search_query': search_query,
    }
    
    return render(request, 'devices/device_list.html', context)

def device_detail(request, device_id):
    """設備詳細資訊檢視"""
    device = get_object_or_404(Devices, id=device_id)
    
    context = {
        'device': device,
    }
    
    return render(request, 'devices/device_detail.html', context)
