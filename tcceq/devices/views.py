from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator
from django.db import models
from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
import qrcode
import io
import os
from django.conf import settings
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.graphics import renderPDF
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.barcode import createBarcodeDrawing
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.cidfonts import UnicodeCIDFont
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

def register_chinese_font():
    """註冊中文字體函數 - 支援一般與粗體"""
    try:
        # 您指定的 Noto Sans TC 字體路徑
        font_path = os.path.join(settings.BASE_DIR, 'media', 'fonts', 'static','NotoSansTC-bold.ttf')
        
        if os.path.exists(font_path):
            # 註冊一般字重
            pdfmetrics.registerFont(TTFont('NotoSansTC', font_path))
            
            # 註冊粗體字重 - 使用同一個 Variable Font 文件
            # Variable Font 可以透過同一個文件產生不同字重
            pdfmetrics.registerFont(TTFont('NotoSansTC-Bold', font_path))
            
            return ('NotoSansTC', 'NotoSansTC-Bold')
        else:
            # 字體文件不存在時的備用方案
            raise FileNotFoundError(f"字體文件不存在: {font_path}")
            
    except Exception as e:
        print(f"註冊 Noto Sans TC 字體失敗: {e}")
        try:
            # 備用方案1：使用 Windows 系統的中文字體
            pdfmetrics.registerFont(UnicodeCIDFont('STSong-Light'))
            return ('STSong-Light', 'STSong-Light')  # 系統字體通常沒有分別的粗體
        except:
            try:
                # 備用方案2：使用 HeiseiMin-W3 (日文字體但支援中文)
                pdfmetrics.registerFont(UnicodeCIDFont('HeiseiMin-W3'))
                return ('HeiseiMin-W3', 'HeiseiMin-W3')
            except:
                # 最後備用：使用 Helvetica
                return ('Helvetica', 'Helvetica-Bold')

@require_http_methods(["POST"])
def download_qrcodes(request):
    """下載選中設備的 QR code 貼紙 PDF - 直接輸出貼紙尺寸"""
    device_ids = request.POST.getlist('device_ids')
    
    if not device_ids:
        return HttpResponse("沒有選擇設備", status=400)
    
    # 取得選中的設備
    devices = Devices.objects.filter(id__in=device_ids).select_related('equipment_type')
    
    if not devices.exists():
        return HttpResponse("找不到指定的設備", status=404)
    
    # 建立 PDF
    buffer = io.BytesIO()
    
    # 貼紙尺寸 (30mm x 40mm)
    sticker_width = 30 * mm
    sticker_height = 40 * mm
    
    # 使用貼紙尺寸作為頁面尺寸
    p = canvas.Canvas(buffer, pagesize=(sticker_width, sticker_height))
    
    # 註冊中文字體 - 現在返回一般和粗體字體名稱
    chinese_font, chinese_font_bold = register_chinese_font()
    
    for i, device in enumerate(devices):
        # 如果不是第一個設備，創建新頁面
        if i > 0:
            p.showPage()
        
        # 產生設備詳細頁面的完整 URL
        current_site = get_current_site(request)
        device_url = f"{request.scheme}://{current_site.domain}{reverse('devices:device_detail', args=[device.id])}"
        
        # QR code 大小和位置 (調整為適合貼紙尺寸)
        qr_size = 22 * mm  # 稍微縮小QR code為中文文字留空間
        qr_x = (sticker_width - qr_size) / 2  # QR code 水平置中
        qr_y = 10 * mm  # QR code 位置
        
        # 使用 reportlab 的 QR code
        qr_widget = QrCodeWidget(device_url)
        qr_widget.barWidth = qr_size
        qr_widget.barHeight = qr_size
        
        drawing = Drawing(qr_size, qr_size)
        drawing.add(qr_widget)
        renderPDF.draw(drawing, p, qr_x, qr_y)
        
        # 添加設備資訊文字 - 使用粗體中文字體
        p.setFont(chinese_font_bold, 8)  # 使用粗體字體
        
        # 設備類型 (QR code 上方) - 使用粗體
        text_y = qr_y + qr_size + 4 * mm
        device_info = f"{device.equipment_type.name}"
        if len(device_info) > 10:  # 中文字符較寬，限制長度
            device_info = device_info[:10] + "..."
        p.drawCentredString(sticker_width/2, text_y, device_info)

        # 設備品牌 (QR code 上方第二行) - 使用粗體
        text_y = qr_y + qr_size + 0.5 * mm
        brand_info = f"{device.brand}"
        if len(brand_info) > 10:
            brand_info = brand_info[:10] + "..."
        p.drawCentredString(sticker_width/2, text_y, brand_info)
        
        # 切換到一般中文字體（規格用一般字體）
        p.setFont(chinese_font, 8)  # 規格用較小的一般字體
        
        # 規格 (再下方) - 支援多行顯示，最多3行
        text_y = qr_y - 1.5 * mm
        spec_info = f"{device.specification}"
        
        # 將長文字分割成多行，每行最多13個字符，最多顯示3行
        max_chars_per_line = 10
        max_lines = 3
        spec_lines = []
        
        for j in range(0, len(spec_info), max_chars_per_line):
            if len(spec_lines) >= max_lines:
                break
            line_text = spec_info[j:j + max_chars_per_line]
            spec_lines.append(line_text)
        
        # 如果文字超過3行，在第三行末尾加上省略號
        if len(spec_info) > max_chars_per_line * max_lines:
            if len(spec_lines) == max_lines:
                spec_lines[-1] = spec_lines[-1][:10] + "..."
        
        # 繪製每一行
        line_height = 2.8 * mm
        for j, line in enumerate(spec_lines):
            current_y = text_y - (j * line_height)
            p.drawCentredString(sticker_width/2, current_y, line)
        
    
    # 完成 PDF
    p.save()
    buffer.seek(0)
    
    # 準備回應
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="device_qr_stickers.pdf"'
    
    return response

@require_http_methods(["GET"])
def download_all_qrcodes(request):
    """下載所有設備的 QR code 貼紙 PDF"""
    # 取得所有設備
    devices = Devices.objects.all()
    
    if not devices.exists():
        return HttpResponse("系統中沒有設備資料", status=404)
    
    # 建立 PDF
    buffer = io.BytesIO()
    
    # 貼紙尺寸 (30mm x 40mm)
    sticker_width = 30 * mm
    sticker_height = 40 * mm
    
    # 使用貼紙尺寸作為頁面尺寸
    p = canvas.Canvas(buffer, pagesize=(sticker_width, sticker_height))
    
    # 註冊中文字體 - 現在返回一般和粗體字體名稱
    chinese_font, chinese_font_bold = register_chinese_font()
    
    for i, device in enumerate(devices):
        # 如果不是第一個設備，創建新頁面
        if i > 0:
            p.showPage()
        
        # 產生設備詳細頁面的完整 URL
        current_site = get_current_site(request)
        device_url = f"{request.scheme}://{current_site.domain}{reverse('devices:device_detail', args=[device.id])}"
        
        # QR code 大小和位置 (調整為適合貼紙尺寸)
        qr_size = 22 * mm  # 稍微縮小QR code為中文文字留空間
        qr_x = (sticker_width - qr_size) / 2  # QR code 水平置中
        qr_y = 10 * mm  # QR code 位置
        
        # 使用 reportlab 的 QR code
        qr_widget = QrCodeWidget(device_url)
        qr_widget.barWidth = qr_size
        qr_widget.barHeight = qr_size
        
        drawing = Drawing(qr_size, qr_size)
        drawing.add(qr_widget)
        renderPDF.draw(drawing, p, qr_x, qr_y)
        
        # 添加設備資訊文字 - 使用粗體中文字體
        p.setFont(chinese_font_bold, 8)  # 使用粗體字體
        
        # 設備類型 (QR code 上方) - 使用粗體
        text_y = qr_y + qr_size + 4 * mm
        device_info = f"{device.equipment_type.name}"
        if len(device_info) > 10:  # 中文字符較寬，限制長度
            device_info = device_info[:10] + "..."
        p.drawCentredString(sticker_width/2, text_y, device_info)

        # 設備品牌 (QR code 上方第二行) - 使用粗體
        p.setFont(chinese_font_bold, 8)
        text_y = qr_y + qr_size + 0.5 * mm
        brand_info = f"{device.brand}"
        if len(brand_info) > 10:
            brand_info = brand_info[:10] + "..."
        p.drawCentredString(sticker_width/2, text_y, brand_info)
        
        # 切換到一般中文字體（規格用一般字體）
        p.setFont(chinese_font, 8)  # 規格用較小的一般字體
        
        # 規格 (再下方) - 支援多行顯示，最多3行
        text_y = qr_y - 1 * mm
        spec_info = f"{device.specification}"
        
        # 將長文字分割成多行，每行最多16個字符，最多顯示3行
        max_chars_per_line = 10
        max_lines = 3
        spec_lines = []
        
        for j in range(0, len(spec_info), max_chars_per_line):
            if len(spec_lines) >= max_lines:
                break
            line_text = spec_info[j:j + max_chars_per_line]
            spec_lines.append(line_text)
        
        # 如果文字超過3行，在第三行末尾加上省略號
        if len(spec_info) > max_chars_per_line * max_lines:
            if len(spec_lines) == max_lines:
                spec_lines[-1] = spec_lines[-1][:10] + "..."
        
        # 繪製每一行
        line_height = 2.8 * mm
        for j, line in enumerate(spec_lines):
            current_y = text_y - (j * line_height)
            p.drawCentredString(sticker_width/2, current_y, line)
        
    
    # 完成 PDF
    p.save()
    buffer.seek(0)
    
    # 準備回應
    response = HttpResponse(buffer.read(), content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="all_devices_qr_stickers.pdf"'
    
    return response
