# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.core.validators import validate_comma_separated_integer_list, MaxValueValidator
from django.core.exceptions import ValidationError
import datetime

#Constants
SHIFT_CHOICES = (
    ("OFF", "OFF"),
    ("V", "V"),
    ("6am", "6am-2pm"),
    ("7am", "7am-3pm"),
    ("7:30am", "7:30am-3:30pm"),
    ("8am", "8am-4pm"),
    ("9am", "9am-5pm"),
    ("10am", "10am-6pm"),
    ("11am", "11am-7pm"),
    ("12pm", "12pm-8pm"),
    ("1pm", "1pm-9pm"),
    ("1:30pm", "1:30pm-9:30pm"),
    ("2:30pm", "2:30pm-10:30pm"),
    ("3:30pm", "3:30pm-11:30pm"),
)
WEEKDAY_CHOICES = (
    ("M", "Monday"),
    ("T", "Tuesday"),
    ("W", "Wednesday"),
    ("Th", "Thursday"),
    ("F", "Friday"),
    ("Sa", "Saturday"),
    ("Su", "Sunday"),
)

#Validators
def no_past(value):
    today = datetime.date.today()
    if value < today:
        raise ValidationError("Cannot request a date in the past.")

def only_monday(value):
    wkday = value.weekday()
    if not(wkday==1):
        raise ValidationError("Week start must be a Monday.")

# Create your models here.
class Employee(models.Model):
    #Choices for employee position
    POSITION_CHOICES = (
        ("SM", "Senior Manager"),
        ("AM", "Assistant Manager"),
        ("SIM", "Store Inventory Merchandiser"),
        ("SLIM", "Shift Leader"),
        ("BSI", "Bookseller I"),
        ("BSII", "Bookseller II"),
        ("PT", "Part Time Bookseller"),
        ("TB", "Temporary Bookseller"),
    )
    QUAD_CHOICES = ((i+1,i+1) for i in range(4))
    firstName = models.CharField(max_length=20, default="")
    lastName = models.CharField(max_length=20, default="")
    position = models.CharField(max_length=20,
                                choices=POSITION_CHOICES,
                                default="BSII",)
    hours = models.IntegerField(default=35, validators=[MaxValueValidator(35)])
    quad = models.IntegerField(blank=True,
                                null=True,
                                choices=QUAD_CHOICES)
    isBuyer = models.BooleanField(default=False)

    def __str__(self):
        return self.lastName + ", " + self.firstName

    class Meta:
        ordering = ('lastName', 'firstName')

class WeekSchedule(models.Model):
    employee = models.ForeignKey(Employee, default="", on_delete=models.CASCADE)
    weekStart = models.DateField(default=datetime.date.today)
    mondayShift = models.CharField(max_length=15, default="", choices=SHIFT_CHOICES)
    tuesdayShift = models.CharField(max_length=15, default="", choices=SHIFT_CHOICES)
    wednesdayShift = models.CharField(max_length=15, default="", choices=SHIFT_CHOICES)
    thursdayShift = models.CharField(max_length=15, default="", choices=SHIFT_CHOICES)
    fridayShift = models.CharField(max_length=15, default="", choices=SHIFT_CHOICES)
    saturdayShift = models.CharField(max_length=15, default="", choices=SHIFT_CHOICES)
    sundayShift = models.CharField(max_length=15, default="", choices=SHIFT_CHOICES)

class TempSchedule(models.Model):
    employee = models.ForeignKey(Employee, default="", on_delete=models.CASCADE)
    weekStart = models.DateField(default=datetime.date.today)
    mondayShift = models.CharField(max_length=15, default="", choices=SHIFT_CHOICES)
    tuesdayShift = models.CharField(max_length=15, default="", choices=SHIFT_CHOICES)
    wednesdayShift = models.CharField(max_length=15, default="", choices=SHIFT_CHOICES)
    thursdayShift = models.CharField(max_length=15, default="", choices=SHIFT_CHOICES)
    fridayShift = models.CharField(max_length=15, default="", choices=SHIFT_CHOICES)
    saturdayShift = models.CharField(max_length=15, default="", choices=SHIFT_CHOICES)
    sundayShift = models.CharField(max_length=15, default="", choices=SHIFT_CHOICES)

class Request(models.Model):
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)

class VacationRequest(Request):
    startDate = models.DateField(default=datetime.date.today,)
    #                            validators=[no_past])
    endDate = models.DateField(default=datetime.date.today, )
    #                            validators=[no_past])
    
    def __str__(self):
        return self.employee + " : " + self.startDate

class ShiftRequest(Request):
    date = models.DateField(default=datetime.date.today, )
    #                        validators=[no_past])
    shift = models.CharField(max_length=15, default="", choices=SHIFT_CHOICES)
    #recurring = models.BooleanField(default=False)

    def __str__(self):
        return self.employee + " : " + self.shift

class RecurringShiftRequest(Request):
    weekDay = models.CharField(default="M", max_length=10, choices=WEEKDAY_CHOICES)
    shift = models.CharField(max_length=15, default="", choices=SHIFT_CHOICES)

    def __str__(self):
        return self.employee + " : " + self.weekDay + self.shift