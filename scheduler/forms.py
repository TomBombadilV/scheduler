from django.forms import ModelForm
from django import forms
from .models import WeekSchedule, Employee, no_past, only_monday, WEEKDAY_CHOICES
from . import widgets

class NewEmployeeForm(ModelForm):
    class Meta:
        model = Employee
        fields = ['lastName', 'firstName', 'position', 'hours', 'quad']

    def process(self):
        cd = self.cleaned_data
        print(cd['firstName'])

class GenerateScheduleForm(forms.Form):
    currentWeek = forms.DateField(required=True, label="For the week of ", widget=forms.TextInput(attrs={'autocomplete':'off'}))
    #currentWeek = forms.DateField(required=True, label="For the week of ", widget=forms.TextInput(attrs={'type': 'week'}))
    coreGroupMeeting = forms.BooleanField(required=False, label="")
    coreGroupMeetingDay = forms.ChoiceField(choices=WEEKDAY_CHOICES, initial="M", label="Core Group Meeting", widget=forms.Select(attrs={'disabled':'disabled'}))
    staffMeeting = forms.BooleanField(required=False, label="")
    staffMeetingI = forms.ChoiceField(choices=WEEKDAY_CHOICES, initial="Th", label="Staff Meeting I", widget=forms.Select(attrs={'disabled':'disabled'}))
    staffMeetingII = forms.ChoiceField(choices=WEEKDAY_CHOICES, initial="F", label="Staff Meeting II", widget=forms.Select(attrs={'disabled':'disabled'}))
    quadOneMeeting = forms.BooleanField(required=False, label="")
    quadOneMeetingDay = forms.ChoiceField(choices=WEEKDAY_CHOICES, initial="M", label="Quad One", widget=forms.Select(attrs={'disabled':'disabled'}))
    quadTwoMeeting = forms.BooleanField(required=False, label="")
    quadTwoMeetingDay = forms.ChoiceField(choices=WEEKDAY_CHOICES, initial="T", label="Quad Two", widget=forms.Select(attrs={'disabled':'disabled'}))
    quadThreeMeeting = forms.BooleanField(required=False, label="")
    quadThreeMeetingDay = forms.ChoiceField(choices=WEEKDAY_CHOICES, initial="W", label="Quad Three", widget=forms.Select(attrs={'disabled':'disabled'}))
    quadFourMeeting = forms.BooleanField(required=False, label="")
    quadFourMeetingDay = forms.ChoiceField(choices=WEEKDAY_CHOICES, initial="Th", label="Quad Four", widget=forms.Select(attrs={'disabled':'disabled'}))

class WeekScheduleForm(ModelForm):
    class Meta:
        model = WeekSchedule
        fields = ['employee', 'mondayShift', 'tuesdayShift', 'wednesdayShift', 'thursdayShift', 'fridayShift', 'saturdayShift', 'sundayShift']

    def __init__(self, *args, **kwargs):
        super(WeekScheduleForm, self).__init__(*args, **kwargs)
        if self.instance.id:
            self.fields['employee'].disabled = True