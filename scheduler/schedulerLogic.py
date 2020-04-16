from __future__ import unicode_literals
from django import forms
from .models import (Employee, WeekSchedule, TempSchedule, VacationRequest, 
                     ShiftRequest, RecurringShiftRequest, WEEKDAY_CHOICES, 
                     SHIFT_CHOICES )

import datetime, calendar, random, numpy as np
from dateutil import parser

class WeekDay:
    dayVal = 0
    openingShift = 0
    closingShift = 0
    openingHour = 0
    
    def __init__(self, dayVal, openingShift, closingShift, openingHour):
        self.dayVal = dayVal
        self.openingShift = openingShift
        self.closingShift = closingShift
        self.openingHour = openingHour

class QuadMeeting:
    quad = 0
    isMeeting = False
    meetingDay = ''

    def __init__(self, quad, meetingDay):
        self.quad = quad
        self.meetingDay = meetingDay

# Makes schedule all pretty
class Style:
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'
	END = '\033[0m'

# Gets relevant data from form
def getFormData(form):
    selectedDate = form['currentWeek'].value()

    quadMeetings={}

    # Get quad meeting booleans
    isMeetingQuadOne = form['quadOneMeeting'].value()
    isMeetingQuadTwo = form['quadTwoMeeting'].value()
    isMeetingQuadThree = form['quadThreeMeeting'].value()
    isMeetingQuadFour = form['quadFourMeeting'].value()

    # If quad meeting is happening, add day to list of quad meetings
    if isMeetingQuadOne:
        quadMeetings['1'] = form['quadOneMeetingDay'].value()
    if isMeetingQuadTwo:
        quadMeetings['2'] = form['quadTwoMeetingDay'].value()
    if isMeetingQuadThree:
        quadMeetings['3'] = form['quadThreeMeetingDay'].value()
    if isMeetingQuadFour:
        quadMeetings['4'] = form['quadFourMeetingDay'].value()

    return selectedDate, quadMeetings

# Calculates first day (Monday) and last day (Sunday) for week of selected date
def calculateWeekRange(selectedDate):
    # Change unicode to datetime
    selectedDate = datetime.datetime.strptime(selectedDate, '%m/%d/%y')
    # Calculate start of week (Monday)
    diff = 0 - selectedDate.weekday()
    weekStart = selectedDate + datetime.timedelta(days = diff)
    # Calculate end of week (Sunday)
    weekEnd = weekStart + datetime.timedelta(days=6)
    weekStart = weekStart.date()
    weekEnd = weekEnd.date()
    return weekStart, weekEnd

# Initializes dictionary of hours left to be worked for the week per employee
def initHoursLeft(employees, hoursLeft):
    for employee in employees:
        hoursLeft[employee] = employee.hours

# Initializes dictionary of how many times each employee has opened and closed
def initOpenCloseCount(employees, openCount, closeCount):
    for employee in employees:
        openCount[employee] = 0
        closeCount[employee] = 0

# Initializes dictionary with empty shift arrays
def initSchedule(employees, schedule):
    for employee in employees:
        schedule[employee] = ['','','','','','','']

# Sets opening and closing shifts for each weekday
def initWeekDays(weekDays):
	for day in range(0,7): 
		opening, closingShift = "",""
		if day<4: 	#Mon through Thur opens at 9am, closes at 10pm
			openingShift, closingShift, openingHour = "7am", "2:30pm", "9am"
		elif day<6: 	#Friday and Sat opens at 9am, closes at 11pm
			openingShift, closingShift, openingHour = "7:30am", "3:30pm", "9am"
		elif day==6:	#Sunday opens at 10am, closes at 9pm
			openingShift, closingShift, openingHour = "8am", "1:30pm", "10am"
		else:
			print("There is a problem in initWeekDays")
		weekDay = WeekDay(day, openingShift, closingShift, openingHour)
		weekDays.append(weekDay)

# Sorts employees into MODs and Booksellers
def initEmployeeLists(employees, mods, booksellers):
    # Employee positions that can act as MOD
    canMod = ["SM", "AM", "SIM", "SLIM"]
    for employee in employees:
        if employee.position in canMod:
            mods.append(employee)
        else:
            booksellers.append(employee)

# Checks relevant vacation/shift requests and updates shifts accordingly
def initRequests(employees, vacationRequests, shiftRequests, 
                 recurringShiftRequests, weekStart, weekEnd, hoursLeft, 
                 schedule):
    today = datetime.datetime.today().date()
    for request in recurringShiftRequests:
        # List of full names of days of the week
        weekdayList = list(calendar.day_name)
        # Get full name of request weekday
        weekday = request.get_weekDay_display()
        # Get index of request weekday
        weekday = weekdayList.index(weekday)
        # Add request to schedule
        schedule[request.employee][weekday] = request.shift

    for request in vacationRequests:
        # Request occurs during selected week
        if (weekStart <= request.startDate <= weekEnd or 
            weekStart <= request.endDate <= weekEnd or 
            weekStart > request.startDate and 
            weekEnd < request.endDate):
            #Calculate length of request
            dayCount = (request.endDate - request.startDate).days + 1
            # Update employee schedule and hours worked with active request days
            for currDate in (request.startDate + datetime.timedelta(n) for n 
                             in range(dayCount)):
                # If date is part of active week
                if weekStart <= currDate <= weekEnd:
                    weekday = currDate.weekday()
                    # Get corresponding shift
                    schedule[request.employee][weekday] = "V"
                    currShift = "V"
                    hoursLeft[request.employee]-=7
                    print(currDate, hoursLeft[request.employee])

    for request in shiftRequests:
        # Request occurs during selected week
        if weekStart <= request.date <= weekEnd:
            weekday = request.date.weekday()
            schedule[request.employee][weekday] = request.shift
    
    return schedule

# Takes each day shift from weekSchedule object and puts into an array (for 
# indexing)
def weekScheduleToArray(weekSchedule, lastOrNextWeek, employee):
    lastOrNextWeek[employee] = []
    if weekSchedule:
        lastOrNextWeek[employee].append(weekSchedule.mondayShift)
        lastOrNextWeek[employee].append(weekSchedule.tuesdayShift)
        lastOrNextWeek[employee].append(weekSchedule.wednesdayShift)
        lastOrNextWeek[employee].append(weekSchedule.thursdayShift)
        lastOrNextWeek[employee].append(weekSchedule.fridayShift)
        lastOrNextWeek[employee].append(weekSchedule.saturdayShift)
        lastOrNextWeek[employee].append(weekSchedule.sundayShift)
    else:
        # If no schedule, then fill with empty array
        lastOrNextWeek[employee] = ['']*7
    return lastOrNextWeek

# Checks if schedules for last week and next week exist. Saves shifts in arrays
def initSurroundingShifts(employees, schedules, lastWeek, nextWeek, weekStart):
    lastWeekStart = weekStart - datetime.timedelta(days=7)
    nextWeekStart = weekStart + datetime.timedelta(days=7)
    lastWeekScheduleSet = schedules.filter(weekStart=lastWeekStart)
    nextWeekScheduleSet = schedules.filter(weekStart=nextWeekStart)
    if lastWeekScheduleSet:
        for employee in employees:
            # There should only be one. "first()" is to get it out of the query 
            # set. This is a WeekSchedule object
            employeeLastWeek = lastWeekScheduleSet.filter(employee=employee).first()
            # Turn into array so we can index the schedules
            weekScheduleToArray(employeeLastWeek, lastWeek, employee)
    if nextWeekScheduleSet:
        for employee in employees:
            employeeNextWeek = nextWeekScheduleSet.filter(employee=employee).first()   
            weekScheduleToArray(employeeNextWeek, nextWeek, employee)

# Initialize data
def initialize(selectedDate, weekDays, employees, mods, booksellers, 
               vacationRequests, shiftRequests, recurringShiftRequests,
               hoursLeft, openCount, closeCount, lastWeek, nextWeek, 
               schedules, schedule, scheduleRating):
    weekStart, weekEnd = calculateWeekRange(selectedDate)
    initHoursLeft(employees, hoursLeft)
    initOpenCloseCount(employees, openCount, closeCount)
    initSchedule(employees, schedule)
    initWeekDays(weekDays)
    initEmployeeLists(employees, mods, booksellers)
    initRequests(employees, vacationRequests, shiftRequests, 
                 recurringShiftRequests, weekStart, weekEnd, hoursLeft, 
                 schedule)
    print(hoursLeft)
    initSurroundingShifts(employees, schedules, lastWeek, nextWeek, weekStart)
    return weekStart, weekEnd

# Checks if anyone specifically requested this shift. Returns list of employees
# who requested this shift.
def checkRequests(day, shift, modCount, booksellerCount, employees, mods, schedule):
    shiftEmployees = []
    for employee in employees:
        # If employee has shift that matches this one, then add them to the list
        if schedule[employee][day.dayVal]==shift:
            if employee in mods:
                modCount+=1
            else:
                booksellerCount+=1
            shiftEmployees.append(employee)
    return shiftEmployees, modCount, booksellerCount

# Creates sorted array (MOD or BS) (sorted by whether employee has worked this 
# shift before or not) and probability array (MOD or BS) 
def calculateProbability(employees, countDict):
    # Sort list of employees by how many times they have already been scheduled 
    # for this shift
    sortedEmployees = sorted(employees, key=lambda x:countDict[x])
    # Number of employees scheduled for this shift once
    onceCount = 0
    for employee in employees:
        if countDict[employee]==1:
            onceCount+=1
    # Number of employees scheduled for this shift twice or more
    moreThanOnceCount = 0
    for employee in employees:
        if countDict[employee] > 1:
            moreThanOnceCount+=1
    # If every employee in the list has already worked this shift before, then 
    # it evens out again
    if onceCount+moreThanOnceCount == len(employees):
        onceCount = moreThanOnceCount
        moreThanOnceCount = 0
        for employee in employees:
            countDict[employee]-=1
    # If employee has worked this shift once, their probability of getting 
    # scheduled for it again tenths
    pOnce = float(0.1) / len(employees)
    # If employee has worked this shift more than once, their probability of 
    # getting scheduled for it again hundredths
    pMoreThanOnce = float(0.01) / len(employees) 
    # Probability for employees who haven't worked this shift yet
    pNeverDvd = 1 - ((pOnce * onceCount) + (pMoreThanOnce * moreThanOnceCount))
    pNeverDivisor = len(employees) - (onceCount + moreThanOnceCount)
    pNever =  pNeverDvd / pNeverDivisor 
    #Probability array corresponding to sorted employee list
    pEmployeeArr = []
    # Fill probability array
    for i in range(0, len(employees)-(onceCount+moreThanOnceCount)):
        pEmployeeArr.append(pNever)
    for i in range(0, onceCount):
        pEmployeeArr.append(pOnce)
    for i in range(0, moreThanOnceCount):
        pEmployeeArr.append(pMoreThanOnce)
    return sortedEmployees, pEmployeeArr

# Calculate how many days worked either before or after given day 
# beforeOrAfter is True if before, False if after
def calculateDaysInARow(dayVal, employeeSchedule, daysWorked, beforeOrAfter):
    offShifts = ["", "OFF", "V"]
    currShift = employeeSchedule[dayVal]
    # Check if current day is still in the range of this week
    dayLimit = dayVal >= 0 if beforeOrAfter else dayVal < 6
    while currShift not in offShifts and dayLimit:
        # If day is within the week and wasn't off, increase days in a row 
        daysWorked+=1
        # If before, count down. If after, count up
        dayVal = dayVal - 1 if beforeOrAfter else dayVal + 1
        currShift = employeeSchedule[dayVal]
        # Check if current day is still in the range of this week
        dayLimit = dayVal >= 0 if beforeOrAfter else dayVal < 6
    return daysWorked

# Checks if working given day will cause employee to work > 5 days in a row
def checkDaysInARow(employee, day, schedule, lastWeek, nextWeek):
    # Day being scheduled
    today = day.dayVal
    daysWorkedBefore = 0
    daysWorkedAfter = 0
    # Calculate days worked before today in current schedule    
    if today > 0:
        dayVal = today-1
        daysWorkedBefore = calculateDaysInARow(dayVal, schedule[employee], 
                                               daysWorkedBefore, True)
    # Calculate days worked after today in current schedule
    if today < 6:
        dayVal = today+1
        daysWorkedAfter = calculateDaysInARow(dayVal, schedule[employee], 
                                              daysWorkedAfter, False)
    # If we have a schedule for last week AND this person has worked every day 
    # this week before today, then check days worked last week
    if lastWeek and daysWorkedBefore == today:
        dayVal = 6 # Sunday
        daysWorkedBefore = calculateDaysInARow(dayVal, lastWeek[employee], 
                                               daysWorkedBefore, True)
    # If we have a schedule for next week AND this person works every day this
    # week after today, then check next week
    if nextWeek and daysWorkedAfter == 6 - today:
        dayVal = 0 # Monday
        daysWorkedAfter = calculateDaysInARow(dayVal, nextWeek[employee], 
                                              daysWorkedAfter, False)
    # Days worked in a row will be days before + days after + selected day
    totalDaysWorked = daysWorkedBefore + daysWorkedAfter
    if totalDaysWorked >= 5:
        return False
    else:
        return True

# Gets the ending hour of the shift prior to today's shift
def getPreviousShift(employee, day, schedule, lastWeek):
    # Yesterday is part of last week's schedule
    if day.dayVal==0:
        # Employee has a schedule for last week
        if lastWeek:
            prevShift = lastWeek[employee][6]
        # Employee doesn't have a schedule for last week
        else:
            prevShift = "" 
    # Yesterday is part of this week's schedule
    else:
        # Get yesterday's shift from this week's schedule
        prevShift = schedule[employee][day.dayVal-1]
    # Get ending hour of shift (Minimum value if shift is empty, V, or OFF)
    offShifts = ["", "V", "OFF"]
    prevShift = 0 if prevShift in offShifts else parser.parse(prevShift).hour
    return prevShift

# Gets the starting hour of the shift after today's shift
def getNextShift(employee, day, schedule, nextWeek):
    # Tomorrow is part of next week's schedule
    if day.dayVal==6:
        # Employee has a schedule for next week
        if nextWeek:
            nextShift = nextWeek[employee][0]
        # Employee doesn't have a schedule for next week
        else: 
            nextShift = ""
    # Tomorrow is part of this week's schedule
    else:
        # Get tomorrow's shift from current schedule
        nextShift = schedule[employee][day.dayVal+1]
    # Get starting hour of shift (Maximum value if shift is empty, V, or OFF)
    offShifts = ["", "V", "OFF"]
    nextShift = 24 if nextShift in offShifts else parser.parse(nextShift).hour
    return nextShift

# Calculates time between previous shift and current shift
def sufficientTimeSincePrevShift(prevShift, currShift):
    # Shift is 8 hours long
    endOfPrevShift = prevShift+8
    # Hours left after end of shift
    hoursLeftInDay = 24-endOfPrevShift
    # Must have 12 hours between shifts
    if hoursLeftInDay+currShift >= 12:
        return True
    else:
        return False

# Calculates time between current shift and next shift
def sufficientTimeBeforeNextShift(nextShift, currShift):
    # Shift is 8 hours long
    endOfCurrShift = currShift+8
    # Hours left after end of shift
    hoursLeftInDay = 24-endOfCurrShift
    # Must have 12 hours between shifts
    if hoursLeftInDay+nextShift >= 12:
        return True
    else:
        return False

# Where all of the scheduling constraints are. 
# The constraints implemented here are:
# 1) Time between shifts must be at least 12 hours
# 2) Employee can't be already scheduled for another shift
# 3) Employee can't have worked full hours for the week
# 4) Employee can't work for more than 5 days in a row
def canWork(employee, day, shift, hoursLeft, schedule, lastWeek, nextWeek):
    available = False
    # If employee is not scheduled for a shift already
    if schedule[employee][day.dayVal]=='': 
        # Get and parse previous shift if it exists
        prevShift = getPreviousShift(employee, day, schedule, lastWeek)
        # Get and parse shift for the following day if it exists
        nextShift = getNextShift(employee, day, schedule, nextWeek)
        shift = parser.parse(shift).hour
        # Calculate time between prevShift and current shift. Must be >=12hours
        if sufficientTimeSincePrevShift(prevShift, shift):
            # Calculate time between next and current shift. Must be >=12hours
            if sufficientTimeBeforeNextShift(nextShift, shift):
                if hoursLeft[employee] > 0:
                    # Check how many days in a row the employee will work if 
                    # scheduled today
                    if checkDaysInARow(employee, day, schedule, lastWeek, 
                                       nextWeek):
                        available = True
    return available

# Checks if selected employees can work this shift and returns list of selected 
# employees. This is also where schedule rating happens
def select(sortedEmployees, randInts, shiftCrew, day, shift, pArr, hoursLeft, 
           schedule, lastWeek, nextWeek, scheduleRating):
    # randInts is the array of randomly generated ints corresponding to employees
    for r in randInts:
        # Counts how many times the selected employee has been unable to work
        counter = 0
        broken = False
        # Get randomly selected employee
        curr = sortedEmployees[r]
        # If selected employee can't work this shift, select another
        while not(canWork(curr, day, shift, hoursLeft, schedule, lastWeek, 
                  nextWeek)):        
            # If counter gets to 50, it is safe to say there are no available 
            # employees to work this shift
            counter+=1
            if counter > 50:
                broken = True
                break
            # Select another employee
            rand = np.random.choice(len(sortedEmployees),1,p=pArr)
            curr = sortedEmployees[rand[0]]
        # The selected employee can work this shift
        if not broken:
            shiftCrew.append(curr)
            schedule[curr][day.dayVal] = shift
        # Broken! No one is available for this shift. Update schedule rating
        else:
            # Opening shifts and closing shifts most important
            requiredShifts = ["7am", "7:30am", "8am", "1:30pm", "2:30pm", 
                              "3:30pm"]
            # Missing a required shift increases the schedule rating by 10
            if shift in requiredShifts:
                scheduleRating[0]+=10
            # Missing a less important shift increases the schedule rating by 1
            else:
                scheduleRating[0]+=1
            print "Breaking shift", shift, "on", WEEKDAY_CHOICES[day.dayVal][1]
    return shiftCrew

# Selects all quad members for scheduled quad meeting
def selectQuad(quad, day, employees, schedule, hoursLeft, lastWeek, nextWeek):
    quad = int(quad)
    # Quad meetings are at 6am
    shift = "6am"
    # Check if quad members can work this shift. If so, schedule them.
    for employee in employees:
        if employee.quad == int(quad):
            if canWork(employee, day, shift, hoursLeft, schedule, lastWeek, 
                       nextWeek):
                schedule[employee][day.dayVal] = shift
                hoursLeft[employee] -= 7
            else:
                print(employee.firstName, 
                      " isn't available for a quad meeting on ", 
                      WEEKDAY_CHOICES[day.dayVal][1], 
                      ". Please choose another one.")

# Selects opening or closing crew for the day
def selectShiftCrew(day, shift, employees, mods, booksellers, schedule,
                    lastWeek, nextWeek, shiftCount, hoursLeft, numMods, 
                    numBooksellers, scheduleRating):
    # Number of MODs and Booksellers that have been scheduled for this shift
    modCount, booksellerCount = 0, 0

    # Add employees who have requested to open to the opening crew
    shiftCrew, modCount, booksellerCount = checkRequests(   day, shift, modCount, 
                                                            booksellerCount, 
                                                            employees, mods, 
                                                            schedule )
    
    # Calculate probability array of how likely each employee is to be selected 
    # for this shift based on how many times they have already worked it
    sortedMods, pModArr = calculateProbability(mods, shiftCount)
    # Temporary fix because None is getting appended to bookseller array for some reason
    booksellers = [b for b in booksellers if b]
    sortedBooksellers, pBooksellerArr = calculateProbability(   booksellers, 
                                                                shiftCount )

    # Generate arrays of weighted "random" numbers using the probability arrays
    randModInts = np.random.choice(len(mods), numMods-modCount, p=pModArr) 
    randBooksellerInts = np.random.choice(  len(booksellers), 
                                            numBooksellers-booksellerCount, 
                                            p=pBooksellerArr)

    # Select 'em
    shiftCrew = select(sortedMods, randModInts, shiftCrew, day, shift, pModArr,
                       hoursLeft, schedule, lastWeek, nextWeek, scheduleRating)
    shiftCrew = select(sortedBooksellers, randBooksellerInts, shiftCrew, day, 
                       shift, pBooksellerArr, hoursLeft, schedule, lastWeek, 
                       nextWeek, scheduleRating)
    
    # Adjust count of how many times each employee has worked this shift and 
    # how many more hours they need to work
    for employee in shiftCrew:
        shiftCount[employee]+=1
        hoursLeft[employee]-=7

# Selects mid crew. Used for selecting any group of employees that is not 
# working a 6-2, opening, or closing shift. Differs from selectShiftCrew() in
# enough respects to warrant its own method.
def selectMids(day, employees, shift, mods, booksellers, schedule, lastWeek, 
               nextWeek, hoursLeft, numMods, numBooksellers, scheduleRating):
    # Number of MODs and Booksellers that have been scheduled for this shift
    modCount, booksellerCount = 0, 0

    # Add employees who have requested to open to the opening crew
    shiftCrew, modCount, booksellerCount = checkRequests(day, shift, modCount,
                                                         booksellerCount, 
                                                         employees, mods, 
                                                         schedule)

    # Generate arrays of random numbers corresponding to employees
    randModInts = random.sample(range(0, len(mods)), numMods-modCount)
    randBooksellerInts = random.sample(range(0, len(booksellers)), 
                                       numBooksellers - booksellerCount)

    # Generate even pModArr so we can re-use "select" method
    pModArr = [float(1)/len(mods)]*len(mods)
    pBooksellerArr = [float(1)/len(booksellers)]*len(booksellers)

    # Select 'em
    shiftCrew = select(mods, randModInts, shiftCrew, day, shift, pModArr, 
                       hoursLeft, schedule, lastWeek, nextWeek, scheduleRating)
    shiftCrew = select(booksellers, randBooksellerInts, shiftCrew, day, shift, 
                       pBooksellerArr, hoursLeft, schedule, lastWeek, nextWeek, 
                       scheduleRating)
    
    # Adjust hours left to work this week
    for employee in shiftCrew:
        hoursLeft[employee]-=7

# Checks if quad meeting is scheduled to happen for this day. Assumes that there
# is at most one quad meeting per day
def quadMtngToday(day, quadMeetings):
    today = WEEKDAY_CHOICES[day.dayVal][0]
    for quad in quadMeetings:
            if quadMeetings[quad]==today:
                return True, quad
    return False, None

# Calculates probability array for unscheduled days only. Prompts the scheduler
# to choose a day with less people scheduled
def getRelevantPArr(employeeCountArr, pArr, unscheduledDays):
    relevantPArr = []
    for day in unscheduledDays:
        relevantPArr.append(pArr[day.dayVal])
    # Need sum to make probability array add up to 100
    sumArr = sum(relevantPArr)
    for i, p in enumerate(relevantPArr):
        # Maff
        relevantPArr[i] = float(p)/sumArr
    return relevantPArr

# Makes sure everyone is working their full hours and fills "OFF" days
# Keeps distribution of "extra" mids as even as possible with a probability array
def fillSchedule(weekDays, employees, schedule, hoursLeft, lastWeek, nextWeek):
    # Number of extra mids scheduled per weekday. 
    numWorkingArr = [0 for i in range(7)]
    # Probability array starts out even
    pArr = [float(100)/7 for i in range(7)]
    for employee in employees:
        # Should be divisible by 7, but if not, we'll ignore the extra hours
        # While employee hasn't worked full hours
        while hoursLeft[employee]/7 > 0:
            # Get indices of unscheduled days
            unscheduledDays = []
            for day in weekDays:
                # If employee is not scheduled for this day
                if schedule[employee][day.dayVal]=="":
                    unscheduledDays.append(day)
            # Get probability array ONLY for unscheduled days
            relevantPArr = getRelevantPArr(numWorkingArr, pArr, unscheduledDays)
            # Choose random unscheduled day
            randomDay = np.random.choice(unscheduledDays, 1, p=relevantPArr)[0]
            # Make sure employee can actually work that day
            if canWork(employee, randomDay, "11am", hoursLeft, schedule, 
                       lastWeek, nextWeek):
                schedule[employee][randomDay.dayVal] = "11am"
                # Increase count of employees scheduled for this day
                numWorkingArr[randomDay.dayVal]+=1
                # Halve the probability of this day getting chosen again
                pArr[randomDay.dayVal] = pArr[randomDay.dayVal]/10
                # Adjust hours left for employee to work
                hoursLeft[employee]-=7
            #else:
            #    print("Something is broken in fillSchedule", employee.firstName, 
            #        hoursLeft[employee], schedule[employee])
        # Fill rest of empty schedule with "OFF" days
        for day in weekDays:
            if schedule[employee][day.dayVal]=="":
                schedule[employee][day.dayVal]="OFF"

# All the brains are here! Fills out the schedule by priority
def createSchedule(weekStart, weekEnd, quadMtngs, weekDays, employees, mods, 
                   booksellers, vacationRequests, shiftRequests, 
                   recurringShiftRequests, hoursLeft, openCount, closeCount,
                   lastWeek, nextWeek, schedules, schedule, scheduleRating):
    for day in weekDays:
        # Check if quad is meeting today, and if so, which one
        quadIsMeeting, quad = quadMtngToday(day, quadMtngs)
        if quadIsMeeting:
            selectQuad(quad, day, employees, schedule, hoursLeft, lastWeek, nextWeek)
 
    for day in weekDays:
        # Needs to be here so it resets every day
        # Number of MODs that need to be scheduled for opening
        numModsOpening = 1
        # Number of Booksellers that need to be scheduled for opening
        numBsOpening = 1 if quadMtngToday(day, quadMtngs)[0] else 2
        # Number of MODs and Booksellers that need to be scheduled for closing
        numModsClosing, numBooksellersClosing = 1, 3

        # Select opening crew
        selectShiftCrew(day, day.openingShift, employees, mods, booksellers, 
                        schedule, lastWeek, nextWeek, openCount, hoursLeft, 
                        numModsOpening, numBsOpening, scheduleRating)

        # Carolyn doesn't want to close
        """carolyn = None
        for bookseller in booksellers:
            if bookseller.firstName=="Carolyn" and bookseller.lastName=="Chan":
                carolyn = bookseller
                booksellers.remove(bookseller)"""

        # Select closing crew
        selectShiftCrew(day, day.closingShift, employees, mods, booksellers,
                        schedule, lastWeek, nextWeek, closeCount, hoursLeft,
                        numModsClosing, numBooksellersClosing, scheduleRating)

        """# Reinstate Carolyn
        booksellers.append(carolyn)"""

    # Reversed because weekend days have priority
    for day in reversed(weekDays):
        # Number of Booksellers coming in when the store opens
        numBooksellersOpenMid = 2 if day.dayVal==5 or day.dayVal==6 else 1
        # Number of MODs and Booksellers coming in at 11am
        numModsMid, numBsMid = 1, 1 if quadMtngToday(day, quadMtngs)[0] else 2
        # Number of MODs coming in at 12pm (only on Fri, Sat, Sun)
        numModsNoon = 1 if day.dayVal >= 4 else 0
        # Select mids coming in at opening time
        selectMids(day, employees, day.openingHour, mods, booksellers, 
                   schedule, lastWeek, nextWeek, hoursLeft, 0, 
                   numBooksellersOpenMid, scheduleRating)
        # Select mids coming in at 11am
        selectMids(day, employees, "11am", mods, booksellers, schedule, 
                   lastWeek, nextWeek, hoursLeft, numModsMid, numBsMid, 
                   scheduleRating)
        # Select mid MODs coming in at 12pm
        selectMids(day, employees, "12pm", mods, booksellers, schedule, 
                   lastWeek, nextWeek, hoursLeft, numModsNoon, 0, 
                   scheduleRating)
    # Fill remaining schedule for people aren't working their full hours
    fillSchedule(weekDays, employees, schedule, hoursLeft, lastWeek, nextWeek)

# Saves generated schedule in database temporarily for review
def saveSchedule(weekStart, employees, schedule):
    TempSchedule.objects.all().delete()
    for employee in employees:
        weekSchedule = TempSchedule(employee=employee, 
                                    weekStart=weekStart,
                                    mondayShift=schedule[employee][0],
                                    tuesdayShift=schedule[employee][1],
                                    wednesdayShift=schedule[employee][2],
                                    thursdayShift=schedule[employee][3],
                                    fridayShift=schedule[employee][4],
                                    saturdayShift=schedule[employee][5],
                                    sundayShift=schedule[employee][6])
        weekSchedule.save()

# Prints out schedule all pretty  
def printSchedule(employees, schedule, selectedDate, hoursLeft=None, 
                  openCount=None, closeCount=None):
    print(("------------------------------------------------------------------"
           "-------------------------------------------------------"))
    print(("                                    HPB SCHEDULE FOR THE WEEK OF"),
          selectedDate)
    print(("------------------------------------------------------------------"
           "-------------------------------------------------------"))
    maxLen = 0
    # Pad names with whitespace
    for employee in employees:
        s = employee.firstName+", "+employee.lastName
        if len(s) > maxLen:
            maxLen = len(s)
    for employee in employees:
        s = employee.lastName+", "+employee.firstName
        print(Style.BOLD+s.rjust(maxLen, " ")+Style.END),
        print'| ',
        for shift in schedule[employee]:
            print shift.center(10, " "),
        print str(hoursLeft[employee]).ljust(3) if hoursLeft else "",
        print openCount[employee] if openCount else "",
        print closeCount[employee] if closeCount else ""

# Initializes schedule-specific variables and generates a single schedule
def generateSchedule(employees, vacationRequests, shiftRequests, 
                     recurringShiftRequests, schedules, selectedDate, 
                     quadMeetings):
    weekDays = []
    mods = []
    booksellers = []
    hoursLeft = {}
    openCount = {}
    closeCount = {}
    lastWeek = {}
    nextWeek = {}
    schedule = {}
    scheduleRating = [0]

    params = {  'weekDays': weekDays,
                'employees': employees, 
                'mods': mods,
                'booksellers': booksellers,
                'vacationRequests': vacationRequests,
                'shiftRequests': shiftRequests,
                'recurringShiftRequests': recurringShiftRequests,
                'hoursLeft': hoursLeft,
                'openCount': openCount,
                'closeCount': closeCount,
                'lastWeek': lastWeek,
                'nextWeek': nextWeek,
                'schedules': schedules,
                'schedule': schedule,
                'scheduleRating': scheduleRating,
            }

    weekStart, weekEnd = initialize(selectedDate, **params)
    createSchedule(weekStart, weekEnd, quadMeetings, **params)
    return schedule, scheduleRating, weekStart

# Takes in form input and model data, runs schedule generation and selects 
# optimal schedule
def generate(form):
    # Initialize model data
    employees = Employee.objects.all()
    vacationRequests = VacationRequest.objects.all()
    shiftRequests = ShiftRequest.objects.all()
    recurringShiftRequests = RecurringShiftRequest.objects.all()
    schedules = WeekSchedule.objects.all()

    # Initialize form data
    selectedDate, quadMeetings = getFormData(form)

    params = {  'employees': employees,
                'vacationRequests': vacationRequests,
                'shiftRequests': shiftRequests,
                'recurringShiftRequests': recurringShiftRequests,
                'schedules': schedules,
                'selectedDate': selectedDate,
                'quadMeetings': quadMeetings
            }

    # Number of schedules to be generated and compared
    regenerate = 30

    # Based on how many shifts the scheduler is not able to fill. 0 is optimal
    scheduleRating = [100]

    for i in range(0, regenerate):
        # If schedule is already optimal, no need to generate any more schedules
        if scheduleRating[0]==0:
            break
        print "---------------Generating Schedule #", i+1, "------------------"
        # Generate a potential schedule
        tempSchedule, tempScheduleRating, weekStart = generateSchedule(**params)
        print "New schedule rating:", tempScheduleRating[0]
        # IF generated schedule is better, it replaces the old one
        if tempScheduleRating < scheduleRating:
            schedule = tempSchedule
            scheduleRating[0] = tempScheduleRating[0]

    saveSchedule(weekStart, employees, schedule)
    print "Final schedule rating:", scheduleRating[0]
    printSchedule(employees, schedule, selectedDate)