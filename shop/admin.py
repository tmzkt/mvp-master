from django.contrib import admin
from .models import Product

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    ordering = ['-created']
    list_display = ('name', 'created', 'available', 'id')
    list_display_links = ('name',)
    list_editable = ('available',)

