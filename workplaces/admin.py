from django.contrib import admin

from .models import Workplace


@admin.register(Workplace)
class WorkplaceAdmin(admin.ModelAdmin):
    list_display = ('id', 'desk_number', 'employee')
    list_display_links = ('id', 'desk_number')
    search_fields = ('employee__last_name', 'employee__first_name')
    autocomplete_fields = ('employee',)
