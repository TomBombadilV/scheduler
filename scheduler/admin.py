# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin
from .models import Employee, VacationRequest, ShiftRequest, RecurringShiftRequest

# Register your models here.
admin.site.register(Employee)
#admin.site.register(WeekSchedule)
#admin.site.register(Shift)
admin.site.register(VacationRequest)
admin.site.register(ShiftRequest)
admin.site.register(RecurringShiftRequest)