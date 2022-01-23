from django.contrib import admin

from .models import Device, Result, DiseaseRisk, CommonRecomendations, CategoryRecomendations,\
    Recomendations, HealthData, CardioActivity, Disease


@admin.register(Recomendations)
class RecomendationsAdmin(admin.ModelAdmin):
    list_display = ('id', 'category', 'name_ru', 'name_en')


@admin.register(CategoryRecomendations)
class CategoryRecomendationsAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')


@admin.register(HealthData)
class HealthDataAdmin(admin.ModelAdmin):
    list_display = ('user', 'create', 'update')


@admin.register(CardioActivity)
class CardioActivityAdmin(admin.ModelAdmin):
    list_display = ('health_model', 'measuring_date')


class ResultAdmin(admin.ModelAdmin):
    # list_display = ('id', 'dashboard', )
    search_fields = ('dashboard__user__email', )


admin.site.register(Device)
admin.site.register(Result, ResultAdmin)
admin.site.register(DiseaseRisk)
admin.site.register(CommonRecomendations)
admin.site.register(Disease)



