from django.urls import path
from . import views

app_name = 'devices'

urlpatterns = [
    # 設備列表頁面
    path('', views.device_list, name='device_list'),
    # 設備詳細資訊頁面
    path('<int:device_id>/', views.device_detail, name='device_detail'),
    # 下載選中的 QR codes
    path('download-qrcodes/', views.download_qrcodes, name='download_qrcodes'),
    # 下載所有 QR codes
    path('download-all-qrcodes/', views.download_all_qrcodes, name='download_all_qrcodes'),
]
