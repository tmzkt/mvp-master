from django.contrib import admin
from .models import Payment

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'price', 'payment_amount', 'summa', 'end_date', 'create')
    readonly_fields = ('summa', 'end_date', 'create')




