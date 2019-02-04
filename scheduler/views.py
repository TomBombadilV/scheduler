# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404, HttpResponseRedirect
from django.template import loader
from django.urls import reverse, reverse_lazy
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.forms import modelformset_factory
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import logout

from .forms import NewEmployeeForm, GenerateScheduleForm, WeekScheduleForm

from .models import Employee, VacationRequest, ShiftRequest, RecurringShiftRequest, WeekSchedule, TempSchedule, SHIFT_CHOICES

from .schedulerLogic import generate

from datetime import *

from collections import OrderedDict

# Create your views here.
@login_required
def index(request):
    employee_list = Employee.objects.order_by('lastName')
    template = loader.get_template('scheduler/index.html')
    form = GenerateScheduleForm()
    context = {
        'employee_list': employee_list,
        'quads': Employee.QUAD_CHOICES,
        'form': form,
    }
    if request.method=="POST":
        form = GenerateScheduleForm(request.POST)
        if form.is_valid():
            #print "FORM IS VALID"
            schedule = generate(form)
            return HttpResponseRedirect(reverse('scheduler:generate-schedule'))
        else:
            print "FAIL"
            form = GenerateScheduleForm()
            context = {
            'form': form,
            }
            return render(request, 'scheduler/index.html', context)
    else:
        form = GenerateScheduleForm()
        context = {
            'form': form,
        }
        return render(request, 'scheduler/index.html', context)
    #return render(request, 'scheduler/index.html', context)

@login_required
def generateSchedule(request):
    tempScheduleList = TempSchedule.objects.order_by('employee__lastName')
    weekScheduleList = WeekSchedule.objects.all()
    overrideFlag = False
    tempWeekStart = TempSchedule.objects.first().weekStart
    if weekScheduleList.filter(weekStart=tempWeekStart):
        overrideFlag = True
    context = {
        'temp_schedule_list': tempScheduleList,
        'override_flag': overrideFlag,
    }
    #WeekSchedule.objects.all().delete()
    return render(request, 'scheduler/generate-schedule.html', context)

@login_required
def tempScheduleDelete(request):
    TempSchedule.objects.all().delete()
    return HttpResponseRedirect(reverse('scheduler:index'))
    #return render(request, 'scheduler/index.html')

@login_required
def scheduleSave(request):
    tempSchedules = TempSchedule.objects.all()
    for tempSchedule in tempSchedules:
        newSchedule = WeekSchedule( employee = tempSchedule.employee,
                        weekStart = tempSchedule.weekStart,
                        mondayShift = tempSchedule.mondayShift,
                        tuesdayShift = tempSchedule.tuesdayShift,
                        wednesdayShift = tempSchedule.wednesdayShift,
                        thursdayShift = tempSchedule.thursdayShift,
                        fridayShift = tempSchedule.fridayShift,
                        saturdayShift = tempSchedule.saturdayShift,
                        sundayShift = tempSchedule.sundayShift)
        newSchedule.save()
    TempSchedule.objects.all().delete()
    return HttpResponseRedirect(reverse('scheduler:schedules'))
    #return render(request, 'scheduler/index.html')

@login_required
def scheduleOverride(request):
    tempScheduleWeekStart = TempSchedule.objects.first().weekStart
    overriddenSchedules = WeekSchedule.objects.filter(weekStart=tempScheduleWeekStart)
    overriddenSchedules.delete()
    scheduleSave(request)
    return HttpResponseRedirect(reverse('scheduler:schedules'))

@login_required
def manageEmployees(request):
    employee_list = Employee.objects.order_by('lastName')
    template = loader.get_template('scheduler/manageEmployees.html')
    if request.method=="POST":
        form = NewEmployeeForm(request.POST)
        if form.is_valid():
            messages.success(request, 'Employee saved successfully.')
            form.save()
            return HttpResponseRedirect(reverse('scheduler:manage-employees'))
        else:
            form = NewEmployeeForm()
    else:
        form = NewEmployeeForm()
        context = {
            'employee_list': employee_list,
            'positions' : Employee.POSITION_CHOICES,
            'form': form,
        }
        return render(request, 'scheduler/manageEmployees.html', context)

class EmployeeUpdate(LoginRequiredMixin, UpdateView):
    login_url = '/login/'
    redirect_field_name = 'redirect_to'

    model = Employee
    fields = ['firstName', 'lastName', 'position', 'hours', 'quad', 'isBuyer']
    template_name_suffix = '_update_form'

    def get_success_url(self):
        return reverse_lazy('scheduler:manage-employees')

class EmployeeDelete(LoginRequiredMixin, DeleteView):
    login_url = '/login/'
    redirect_field_name = 'redirect_to'

    model = Employee
    success_url = reverse_lazy('scheduler:manage-employees')

@login_required
def requests(request):
    vacation_request_list = VacationRequest.objects.order_by('startDate')
    shift_request_list = ShiftRequest.objects.order_by('date')
    recurring_shift_request_list = RecurringShiftRequest.objects.order_by('employee')
    #print recurring_shift_request_list
    template = loader.get_template('scheduler/requests.html')
    context = {
        'vacation_request_list': vacation_request_list,
        'shift_request_list' : shift_request_list,
        'recurring_shift_request_list' : recurring_shift_request_list,
    }
    return render(request, 'scheduler/requests.html', context)

@login_required
def requestPrompt(request):
    return render(request, 'scheduler/request-prompt.html')
 
# Needs to be lower case so it isn't confused with the eponymous class
class vacationRequest(LoginRequiredMixin, CreateView):
    login_url = '/login/'
    redirect_field_name = 'redirect_to'

    model = VacationRequest
    fields = ['employee', 'startDate', 'endDate']

    def get_success_url(self):
        return reverse_lazy('scheduler:requests')

class shiftRequest(LoginRequiredMixin, CreateView):
    login_url = '/login/'
    redirect_field_name = 'redirect_to'

    model = ShiftRequest
    fields = ['employee', 'date', 'shift']

    def get_success_url(self):
        return reverse_lazy('scheduler:requests')

class recurringShiftRequest(LoginRequiredMixin, CreateView):
    login_url = '/login/'
    redirect_field_name = 'redirect_to'
    
    model = RecurringShiftRequest
    fields = ['employee', 'weekDay', 'shift']

    def get_success_url(self):
        return reverse_lazy('scheduler:requests')

class VacationRequestUpdate(LoginRequiredMixin, UpdateView):
    login_url = '/login/'
    redirect_field_name = 'redirect_to'

    model = VacationRequest
    fields = ['employee', 'startDate', 'endDate']
    template_name_suffix = '_update_form'

    def get_success_url(self):
        return reverse_lazy('scheduler:requests')

class VacationRequestDelete(LoginRequiredMixin, DeleteView):
    login_url = '/login/'
    redirect_field_name = 'redirect_to'

    model = VacationRequest
    success_url = reverse_lazy('scheduler:requests')

class ShiftRequestUpdate(LoginRequiredMixin, UpdateView):
    login_url = '/login/'
    redirect_field_name = 'redirect_to'

    model = ShiftRequest
    fields = ['employee', 'date', 'shift']
    template_name_suffix = '_update_form'

    def get_success_url(self):
        return reverse_lazy('scheduler:requests')

class ShiftRequestDelete(LoginRequiredMixin, DeleteView):
    login_url = '/login/'
    redirect_field_name = 'redirect_to'

    model = ShiftRequest
    success_url = reverse_lazy('scheduler:requests')

class RecurringShiftRequestUpdate(LoginRequiredMixin, UpdateView):
    login_url = '/login/'
    redirect_field_name = 'redirect_to'

    model = RecurringShiftRequest
    fields = ['employee', 'weekDay', 'shift']
    template_name_suffix = '_update_form'

    def get_success_url(self):
        return reverse_lazy('scheduler:requests')

class RecurringShiftRequestDelete(LoginRequiredMixin, DeleteView):
    login_url = '/login/'
    redirect_field_name = 'redirect_to'

    model = RecurringShiftRequest
    success_url = reverse_lazy('scheduler:requests')

@login_required
def schedules(request, date=None):
    weekSchedules = WeekSchedule.objects.order_by("employee__lastName")
    template = loader.get_template('scheduler/schedules.html')
    if not date:
        monday = datetime.today() + timedelta(days=0-datetime.today().weekday())
        monday = monday.date()
    else:
        monday = datetime.strptime(date, "%Y-%m-%d").date()
    currSchedules = WeekSchedule.objects.filter(weekStart=monday)
    context = {
        'weekSchedules': weekSchedules,
        'monday': monday,
        'datetime': datetime,
        'currSchedules': currSchedules,
    }
    if request.method == "POST":
        # Get week start date from template
        selectedWeekStart = request.POST.get("week-start")
        # Re-format date
        selectedWeekStart = datetime.strptime(selectedWeekStart, "%b %d, %Y").strftime("%Y-%m-%d")
        if 'edit' in request.POST:
            return HttpResponseRedirect(reverse('scheduler:schedule-edit') + selectedWeekStart)
        elif 'delete' in request.POST:
            deleteSchedule(selectedWeekStart)
            return HttpResponseRedirect(reverse('scheduler:schedules'))
        elif 'coverage' in request.POST:
            return HttpResponseRedirect(reverse('scheduler:schedule-coverage') + selectedWeekStart)
        else:
            return HttpResponseRedirect(reverse('scheduler:schedules'))
    else:
        return render(request, 'scheduler/schedules.html', context)
        
def scheduleCoverage(request, date):
    # Get relevant schedules
    date = datetime.strptime(date, "%Y-%m-%d").date()
    selectedWeekSchedules = WeekSchedule.objects.filter(weekStart=date)
    #mon, tue, wed, thu, fri, sat, sun = {}, {}, {}, {}, {}, {}, {}
    weekShifts = ["mondayShift", "tuesdayShift", "wednesdayShift", "thursdayShift", "fridayShift", "saturdayShift", "sundayShift"]
    weekdayDicts = [{} for _ in range(7)]
    # Fill weekday dictionaries {key:value}=>{shift:employees}
    for weekSchedule in selectedWeekSchedules:
        # Enumerating weekday dictionary list so we can get the weekday shifts by name
        for dayIndex, weekdayDict in enumerate(weekdayDicts):
            # Get attribute name from day index (mondayShift, tuesdayShift, etc.)
            shiftName = weekShifts[dayIndex]
            # Get shift from week schedule by name
            shift = getattr(weekSchedule, shiftName)
            # Add employee to dictionary with shift as key (ignore if not working that day)
            if not(shift=="OFF" or shift=="V"):
                if shift in weekdayDict:
                    weekdayDict[shift].append(weekSchedule.employee)
                else:
                    weekdayDict[shift] = [weekSchedule.employee]

        """if weekSchedule.mondayShift in mon:
            mon[weekSchedule.mondayShift].append(weekSchedule.employee)
        else:
            mon[weekSchedule.mondayShift] = [weekSchedule.employee]"""

    shiftDict = [shift[0] for shift in SHIFT_CHOICES]
    weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    # Sort by shift
    for i, weekdayDict in enumerate(weekdayDicts):
        sortedWeekdayDict = OrderedDict([(shift, weekdayDict[shift]) for shift in shiftDict if shift in weekdayDict ])
        weekdayDicts[i] = sortedWeekdayDict

    weekdayDicts = zip(weekdays, weekdayDicts)

    context = {
        'date': date,
        'weekdayDicts': weekdayDicts,
    }
    return render(request, 'scheduler/coverage.html', context)

@login_required
def editSchedule(request, date):
    # Get relevant schedules
    date = datetime.strptime(date, "%Y-%m-%d").date()
    WeekScheduleFormSet = modelformset_factory(WeekSchedule, form=WeekScheduleForm, extra=0) # Django generates one extra form by default
    selectedWeekSchedules = WeekSchedule.objects.filter(weekStart=date)
    formset = WeekScheduleFormSet(queryset=selectedWeekSchedules)
    for form in formset:
        form.fields['employee'].widget.attrs['readonly'] = True
    #formset = WeekScheduleFormset()
    context = {
        'date': date,
        'formset': formset,
    }
    if request.method == "POST":
        formset = WeekScheduleFormSet(request.POST)
        if formset.is_valid():
            formset.save()
            print("successfully saved")
            return HttpResponseRedirect(reverse('scheduler:schedules')+date.strftime("%Y-%m-%d"))
        else:
            return render(request, 'scheduler/edit_schedule.html', context)
    else:
        return render(request, 'scheduler/edit_schedule.html', context)

def deleteSchedule(selectedWeekStart):
    # Get week start date from template
    #selectedWeekStart = request.POST.get("week-start")
    # Re-format date
    #selectedWeekStart = datetime.strptime(selectedWeekStart, "%b %d, %Y").strftime("%Y-%m-%d")
    # Get relevant schedules
    selectedWeekSchedules = WeekSchedule.objects.filter(weekStart=selectedWeekStart)
    selectedWeekSchedules.delete()

def logout(request):
    logout(request)
    # Redirect to a success page.
    return HttpResponseRedirect('logged_out.html')    