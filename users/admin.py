import csv
import datetime
import django
from rangefilter.filter import DateRangeFilter, DateTimeRangeFilter
from django.contrib import admin
from users.models import CustomUser
from django.utils.translation import gettext_lazy as _
import pandas
from django.conf import settings
from django.http import HttpResponse, HttpResponseForbidden
from django.contrib.auth.admin import UserAdmin

# Register your models here.

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['first_name', 'last_name', 'date_joined', 'email', 'is_active', 'email_confirm']
    list_editable = ['email_confirm']
    list_display_links = ('first_name', 'last_name', 'date_joined', 'email',)
    fieldsets = (
        (None, {'fields': ('first_name', 'last_name', 'email', 'password')}),
        ('Permissions', {'fields': ('is_staff', 'is_active')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'is_staff', 'is_active', 'date_joined')}
        ),
    )

    search_fields = ('email',)
    ordering = ('-date_joined',)

    csv_fields = ['first_name', 'last_name', 'email', ]
    list_filter = ('email_confirm', ('date_joined', DateRangeFilter),)
    # CSV module
    def export_as_csv(admin_model, request, queryset):
        # everyone has perms to export as csv unless explicitly defined
        if getattr(settings, 'DJANGO_EXPORTS_REQUIRE_PERM', None):
            admin_opts = admin_model
            has_csv_permission = request.user.objects_name.all("%s" % (admin_opts))
        else:
            has_csv_permission = admin_model.has_csv_permission(request) \
                if (hasattr(admin_model, 'has_csv_permission') and callable(getattr(admin_model, 'has_csv_permission'))) \
                else True
        if has_csv_permission:
            start_date = request.GET.get("date_joined__range__gte", "")
            end_date = request.GET.get("date_joined__range__lte", "all_date_")
            list_editable = request.GET.get('email_confirm__exact', "all")
            if request.GET.get('email_confirm__exact') == '1':
                list_editable = "yes"
            if request.GET.get('email_confirm__exact') == '0':
                list_editable = "not"
            if getattr(admin_model, 'csv_fields', None):
                field_names = admin_model.csv_fields
            if django.VERSION[0] == 1 and django.VERSION[1] <= 5:
                response = HttpResponse(mimetype='text/csv')
            else:
                response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename=emails_{}_{}_confirm_{}.csv'.format(start_date, end_date, list_editable)
            queryset = queryset.values_list(*field_names)
            pandas.DataFrame(list(queryset), columns=field_names).to_csv(response, index=False, encoding='utf-8')
            return response
        return HttpResponseForbidden()
    export_as_csv.short_description = (_("Save to .csv"))
    actions = [export_as_csv]

admin.site.register(CustomUser, CustomUserAdmin)
