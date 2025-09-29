from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db import models
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
import qrcode
import io
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.barcode import createBarcodeDrawing
from .models import Devices, EquipmentType

def device_list(request):
    """設備列表檢視"""
    devices = Devices.objects.all()
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

@require_http_methods(["POST"])
def download_qrcodes(request):
    """下載選中設備的 QR code 貼紙 PDF - 每頁一個 QR code"""
    device_ids = request.POST.getlist('device_ids')
    
    if not device_ids:
        return HttpResponse("沒有選擇設備", status=400)
    
    # 取得選中的設備
    devices = Devices.objects.filter(id__in=device_ids).select_related('equipment_type')
    
    if not devices.exists():
        return HttpResponse("找不到指定的設備", status=404)
    
    # 建立 PDF
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    
    # A4 頁面尺寸
    page_width, page_height = A4
    
    # 貼紙尺寸 (30mm x 40mm)
    sticker_width = 30 * mm
    sticker_height = 40 * mm
    
    # 計算置中位置
    center_x = (page_width - sticker_width) / 2
    center_y = (page_height - sticker_height) / 2
    
    for i, device in enumerate(devices):
        # 如果不是第一個設備，創建新頁面
        if i > 0:
            p.showPage()
        
        # 產生設備詳細頁面的完整 URL
        current_site = get_current_site(request)
        device_url = f"{request.scheme}://{current_site.domain}{reverse('devices:device_detail', args=[device.id])}"
        
        # QR code 大小和位置
        qr_size = 25 * mm  # QR code 大小
        qr_x = center_x + (sticker_width - qr_size) / 2  # QR code 水平置中
        qr_y = center_y + 8 * mm  # QR code 位置（稍微偏上）
        
        # 使用 reportlab 的 QR code
        qr_widget = QrCodeWidget(device_url)
        qr_widget.barWidth = qr_size
        qr_widget.barHeight = qr_size
        
        drawing = Drawing(qr_size, qr_size)
        drawing.add(qr_widget)
        renderPDF.draw(drawing, p, qr_x, qr_y)
        
        # 添加設備資訊文字
        p.setFont("Helvetica-Bold", 8)  # 標題字體
        
        # 設備類型 (QR code 上方)
        text_y = qr_y + qr_size + 3 * mm
        device_info = f"{device.equipment_type.name}"
        if len(device_info) > 25:  # 限制文字長度
            device_info = device_info[:22] + "..."
        p.drawCentredString(center_x + sticker_width/2, text_y, device_info)
        
        # 切換到一般字體
        p.setFont("Helvetica", 7)
        
        # 設備品牌 (QR code 下方)
        text_y = qr_y - 3 * mm
        brand_info = f"品牌: {device.brand}"
        if len(brand_info) > 30:
            brand_info = brand_info[:27] + "..."
        p.drawCentredString(center_x + sticker_width/2, text_y, brand_info)
        
        # 規格 (再下方)
        text_y = qr_y - 6 * mm
        spec_info = f"規格: {device.specification}"
        if len(spec_info) > 30:
            spec_info = spec_info[:27] + "..."
        p.drawCentredString(center_x + sticker_width/2, text_y, spec_info)
        
        # 安裝日期 (最下方)
        text_y = qr_y - 9 * mm
        date_info = f"安裝: {device.date_installed.strftime('%Y-%m-%d')}"
        p.drawCentredString(center_x + sticker_width/2, text_y, date_info)
        
        # 繪製貼紙邊框 (虛線，方便切割)
        p.setStrokeColorRGB(0.7, 0.7, 0.7)  # 灰色
        p.setLineWidth(0.5)
        p.setDash(2, 2)  # 虛線樣式
        p.rect(center_x, center_y, sticker_width, sticker_height, stroke=1, fill=0)
        
        # 重置線條樣式
        p.setDash()  # 重置為實線
        
        # 添加切割線標記（頁面四角）
        p.setStrokeColorRGB(0.5, 0.5, 0.5)
        p.setLineWidth(0.3)
        corner_mark_size = 5 * mm
        
        # 左上角
        p.line(center_x - corner_mark_size, center_y + sticker_height, center_x, center_y + sticker_height)
        p.line(center_x, center_y + sticker_height, center_x, center_y + sticker_height + corner_mark_size)
        
        # 右上角
        p.line(center_x + sticker_width, center_y + sticker_height + corner_mark_size, center_x + sticker_width, center_y + sticker_height)
        p.line(center_x + sticker_width, center_y + sticker_height, center_x + sticker_width + corner_mark_size, center_y + sticker_height)
        
        # 左下角
        p.line(center_x - corner_mark_size, center_y, center_x, center_y)
        p.line(center_x, center_y - corner_mark_size, center_x, center_y)
        
        # 右下角
        p.line(center_x + sticker_width + corner_mark_size, center_y, center_x + sticker_width, center_y)
        p.line(center_x + sticker_width, center_y, center_x + sticker_width, center_y - corner_mark_size)
    
    # 完成 PDF
    p.save()
    buffer.seek(0)
    
    # 準備回應
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="device_qr_stickers.pdf"'
    
    return response
