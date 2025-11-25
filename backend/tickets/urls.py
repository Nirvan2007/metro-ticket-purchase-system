from django.urls import path
from . import views

app_name = 'tickets'
urlpatterns = [
    path('', views.home, name='home'),
    path('buy/', views.buy_ticket, name='buy_ticket'),
    path('verify-otp/<int:purchase_id>/', views.verify_otp, name='verify_otp'),
    path('tickets/', views.ticket_list, name='ticket_list'),
    path('scanner/', views.scanner_view, name='scanner'),
    path('api/scan/<int:ticket_id>/', views.scan_ticket_api, name='scan_ticket_api'),
]
