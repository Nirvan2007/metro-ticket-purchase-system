from django.contrib import admin
from .models import Wallet, Station, Ticket, OTP, PurchaseRequest

@admin.register(Station)
class StationAdmin(admin.ModelAdmin):
    list_display = ('name', 'lines')

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id','start','end','user','price','status','created_at')
    list_filter = ('status','start','end')

@admin.register(PurchaseRequest)
class PurchaseRequestAdmin(admin.ModelAdmin):
    list_display = ('id','user','start_name','end_name','price','created_at')

admin.site.register(Wallet)
admin.site.register(OTP)
