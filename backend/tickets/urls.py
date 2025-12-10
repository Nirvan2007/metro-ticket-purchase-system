from django.urls import path
from . import views, admin

app_name = 'tickets'
urlpatterns = [
    path('', views.home, name='home'),
    path('line/', admin.add_line, name='add_line'),
    path('station/', admin.add_station, name='add_station'),
    path('buy-offline/', admin.buy_ticket_offline, name='buy_offline'),
    path('manage-line/', admin.manage_line, name='manage_line'),
    path('disable-line/', admin.disable_line, name='disable_line'),
    path('enable-line/', admin.enable_line, name='enable_line'),
    path('buy/', views.buy_ticket, name='buy_ticket'),
    path('verify-otp/<int:purchase_id>/', views.verify_otp, name='verify_otp'),
    path('tickets/', views.ticket_list, name='ticket_list'),
    path('scanner/', views.scanner_view, name='scanner'),
    path('wallet/', views.wallet_view, name='wallet'),
    path('api/scan/<int:ticket_id>/', views.scan_ticket_api, name='scan_ticket_api'),
]
