from django.contrib import admin
from datetime import datetime
from .models import *

class WorkRecordAdmin(admin.ModelAdmin):
    list_display = ('employee', 'date', 'clock_in', 'clock_out')
    list_filter = ('employee', 'date')
    search_fields = ('employee__name', 'date')
    actions = ['bulk_set_clock_out']

    def bulk_set_clock_out(self, request, queryset):
        # Action to set the clock_out time for selected records
        rows_updated = queryset.update(clock_out=datetime.now())
        self.message_user(request, f'{rows_updated} work records were updated.')

    bulk_set_clock_out.short_description = 'Set Clock Out for Selected Records'

admin.site.register(Employee)
admin.site.register(WorkRecord, WorkRecordAdmin)