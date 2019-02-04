from __future__ import unicode_literals
from django import forms
from .models import Employee, WeekSchedule, TempSchedule, VacationRequest, ShiftRequest, RecurringShiftRequest, WEEKDAY_CHOICES, SHIFT_CHOICES

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

class Style:
	BOLD = '\033[1m'
	UNDERLINE = '\033[4m'
	END = '\033[0m'

# Get relevant data from form
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

# Calculate first day (Monday) and last day (Sunday) for week of current selected date
def calculateWeekRange(selectedDate):
    # Change unicode to datetime
    selectedDate = datetime.datetime.strptime(selectedDate, '%m/%d/%y')
    # Calculate start of week (Monday)
    weekStart = selectedDate + datetime.timedelta(days=0-selectedDate.weekday())
    # Calculate end of week (Sunday)
    weekEnd = weekStart + datetime.timedelta(days=6)
    weekStart = weekStart.date()
    weekEnd = weekEnd.date()
    return weekStart, weekEnd

# Initialize dictionary of hours left to be worked for the week per employee
def initHoursLeft(employees, hoursLeft):
    for employee in employees:
        hoursLeft[employee] = employee.hours

# Initialize dictionary of how many times each employee has opened and closed
def initOpenCloseCount(employees, openCount, closeCount):
    for employee in employees:
        openCount[employee] = 0
        closeCount[employee] = 0

def initSchedule(employees, schedule):
    for employee in employees:
        schedule[employee] = ['','','','','','','']

# Set opening and closing shifts for each weekday
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
			print("There is a problem in initWeekDays().")
		weekDay = WeekDay(day, openingShift, closingShift, openingHour)
		weekDays.append(weekDay)

# Sort employees into MODs and Booksellers
def initEmployeeLists(employees, mods, booksellers):
    # Employee positions that can act as MOD
    canMod = ["SM", "AM", "SIM", "SLIM"]
    for employee in employees:
        if employee.position in canMod:
            mods.append(employee)
        else:
            booksellers.append(employee)

#Initialize shift objects for employees. Each employee has one shift for each weekday : 7 shifts + Last Sunday shift = 8 shifts
""" Removed Shift/Employee foreign key relationship
def initEmployeeShifts(employees):
    for employee in employees:
        for day in WEEKDAY_CHOICES:
            # day[0] for first part of tuple
            shift = Shift(employee=employee, weekDay=day[0])
            shift.save()
"""

# Check relevant vacation/shift requests and update employee shifts accordingly
def initRequests(   employees, vacationRequests, shiftRequests, 
                    recurringShiftRequests, weekStart, weekEnd, hoursLeft, 
                    schedule):
    today = datetime.datetime.today().date()
    for request in recurringShiftRequests:
        weekdayList = list(calendar.day_name)
        weekday = request.get_weekDay_display()
        weekday = weekdayList.index(weekday)
        schedule[request.employee][weekday] = request.shift
        
    for request in vacationRequests:
        #print request.startDate, request.endDate, weekStart, weekEnd
        #print(weekStart <= request.startDate <= weekEnd)
        #print(weekStart <= request.endDate <= weekEnd)
        #print(weekStart > request.startDate and weekEnd < request.endDate)

        # Period of request has already passed
        #if request.startDate < today and request.endDate < today:
            #print("Throwing away old request", request.startDate, request.endDate, request.employee.firstName)
            #request.delete()
        # Request occurs during selected week
        if (weekStart <= request.startDate <= weekEnd or 
            weekStart <= request.endDate <= weekEnd or 
            weekStart > request.startDate and 
            weekEnd < request.endDate):
            #print "THIS REQUEST IS ACTIVE"
            #Calculate length of request
            dayCount = (request.endDate - request.startDate).days+1
            # Update employee schedule and hours worked with active request days
            for currDate in (request.startDate + datetime.timedelta(n) for n in range(dayCount)):
                # If date is part of active week
                if weekStart <= currDate <= weekEnd:
                    weekday = currDate.weekday()
                    # Get corresponding shift
                    schedule[request.employee][weekday] = "V"
                    #currShift = request.employee.shift_set.get(weekDay=WEEKDAY_CHOICES[weekday][0])
                    # SHIFT_CHOICES[1][0] is the vacation shift
                    currShift = "V"
                    #currShift.shift = "V"
                    #currShift.save()
                    hoursLeft[request.employee] -= 7
                   # print request.employee.shift_set.all()
        # Request is not relevant to selected week
        #else:
        #    pass

    for request in shiftRequests:
        # Request occurs during selected week
        if weekStart <= request.date <= weekEnd:
            #print "THIS REQUEST IS ACTIVE"
            weekday = request.date.weekday()
            #print(weekday)
            #currShift = request.employee.shift_set.get(weekDay=WEEKDAY_CHOICES[weekday][0])
            schedule[request.employee][weekday] = request.shift
            #currShift.shift = request.shift
            #currShift.save()
            # If request is for a specific shift 
            #if not request.shift=="OFF":
            #    hoursLeft[request.employee] -= 7
            #print request.employee.shift_set.all()
        # Request is not relevant to selected week
        #else:
        #    pass
    
    return schedule

# Takes each day shift from weekSchedule object and puts into an array (for indexing)
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
        lastOrNextWeek[employee] = ['']*7
    return lastOrNextWeek

# Check if schedules for last week and next week exist. Save shifts
def initSurroundingShifts(employees, schedules, lastWeek, nextWeek, weekStart):
    lastWeekStart = weekStart - datetime.timedelta(days=7)
    nextWeekStart = weekStart + datetime.timedelta(days=7)
    lastWeekScheduleSet = schedules.filter(weekStart=lastWeekStart)
    nextWeekScheduleSet = schedules.filter(weekStart=nextWeekStart)
    if lastWeekScheduleSet:
        #print("IT EXISTS FOR LAST WEEK")
        for employee in employees:
            # There should only be one. "first()" is to get it out of the query set. This is a WeekSchedule object
            employeeLastWeek = lastWeekScheduleSet.filter(employee=employee).first()
            # So we can index the schedules
            weekScheduleToArray(employeeLastWeek, lastWeek, employee)
    if nextWeekScheduleSet:
        print("IT EXISTS FOR NEXT WEEK")
        for employee in employees:
            employeeNextWeek = nextWeekScheduleSet.filter(employee=employee).first()   
            weekScheduleToArray(employeeNextWeek, nextWeek, employee)

# Initialize data
def initialize( selectedDate, weekDays, employees, mods, booksellers, 
                vacationRequests, shiftRequests, recurringShiftRequests,
                hoursLeft, openCount, closeCount, lastWeek, nextWeek, 
                schedules, schedule, scheduleRating):
    weekStart, weekEnd = calculateWeekRange(selectedDate)
    initHoursLeft(employees, hoursLeft)
    initOpenCloseCount(employees, openCount, closeCount)
    initSchedule(employees, schedule)
    initWeekDays(weekDays)
    initEmployeeLists(employees, mods, booksellers)
    #initEmployeeShifts(employees)
    initRequests(   employees, vacationRequests, shiftRequests, 
                    recurringShiftRequests, weekStart, weekEnd, hoursLeft, 
                    schedule)
    initSurroundingShifts(employees, schedules, lastWeek, nextWeek, weekStart)
    return weekStart, weekEnd

# Check if anyone specifically requested this shift. Returns list of employees who requested this shift.
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

# Create sorted array (MOD or BS) (sorted by whether employee has worked this shift before or not) and probability array (MOD or BS) 
def calculateProbability(employees, countDict):
    # Sort list of employees by how many times they are already scheduled for this shift
    sortedEmployees = sorted(employees, key=lambda x:countDict[x])
    # Number of employees scheduled for this shift once
    onceCount = 0
    for employee in employees:
		if countDict[employee] == 1:
			onceCount+=1
    # Number of employees scheduled for this shift twice or more
    moreThanOnceCount = 0
    for employee in employees:
		if countDict[employee] > 1:
			moreThanOnceCount+=1
    # If every employee in the list has already worked this shift before, then it evens out again
    if onceCount+moreThanOnceCount == len(employees):
        onceCount = moreThanOnceCount
        moreThanOnceCount = 0
        for employee in employees:
		    countDict[employee] -= 1
    # If employee has worked this shift once, their probability of getting scheduled for it again tenths
    pOnce = float(0.1)/len(employees)
    # If employee has worked this shift more than once, their probability of getting scheduled for it again hundredths
    pMoreThanOnce = float(0.01)/len(employees) 
    # Probability for employees who haven't worked this shift yet
    pNever = (1-((pOnce*onceCount)+(pMoreThanOnce*moreThanOnceCount)))/(len(employees)-(onceCount+moreThanOnceCount))
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

# Calculate how many days worked either before or after given day based on beforeOrAfter boolean flag
def calculateDaysBeforeOrAfter(dayVal, employeeSchedule, daysWorked, beforeOrAfter):
    notWorking = ["OFF", "", "V"]
    currShift = employeeSchedule[dayVal]
    # If before, we're counting down. If after, we're counting up.
    dayLimit = dayVal >= 0 if beforeOrAfter else dayVal < 6
    while currShift not in notWorking and dayLimit:
        daysWorked+=1
        dayVal = dayVal-1 if beforeOrAfter else dayVal+1
        currShift = employeeSchedule[dayVal]
        dayLimit = dayVal >= 0 if beforeOrAfter else dayVal < 6
    return daysWorked

# Calculates how many days in a row employee has been working
def calculateDaysInARow(employee, day, schedule, lastWeek, nextWeek):
    today = day.dayVal
    daysWorkedBefore = 0
    daysWorkedAfter = 0
    # Calculate days worked before today in current schedule    
    if today > 0:
        dayVal = today-1
        """currShift = schedule[employee][dayVal]
        while currShift and dayVal >= 0:
            daysWorkedBefore+=1
            dayVal-=1
            currShift = schedule[employee][dayVal]
        print "daysWorkedBefore", today, daysWorkedBefore"""
        daysWorkedBefore = calculateDaysBeforeOrAfter(dayVal, schedule[employee], daysWorkedBefore, True)
    if today < 6:
        dayVal = today+1
        """currShift = schedule[employee][dayVal]
        while currShift and dayVal <6:
            daysWorkedAfter+=1
            dayVal+=1
            currShift = schedule[employee][dayVal]"""
        daysWorkedAfter = calculateDaysBeforeOrAfter(dayVal, schedule[employee], daysWorkedAfter, False)

    # If we have a schedule for last week AND this person has worked every day 
    # this week before today, then check days worked last week
    if lastWeek and daysWorkedBefore == today:
        dayVal = 6 # Sunday
        daysWorkedBefore = calculateDaysBeforeOrAfter(dayVal, lastWeek[employee], daysWorkedBefore, True)
        """currShift = lastWeek[employee][dayVal]
        while currShift and dayVal >= 0:
            daysWorkedBefore+=1
            dayVal-=1
            currShift = lastWeek[employee][dayVal]"""
    # If we have a schedule for next week AND this person works every day this
    # week after today, then check next week
    if nextWeek and daysWorkedAfter == 6-today:
        dayVal = 0 # Monday
        daysWorkedAfter = calculateDaysBeforeOrAfter(dayVal, nextWeek[employee], daysWorkedAfter, False)
        """currShift = nextWeek[employee][dayVal]
        daysWorkedAfter = 0
        while currShift and dayVal <= 6:
            daysWorkedAfter+=1
            dayVal+=1
            currShift = nextWeek[employee][dayVal]"""
    #print daysWorkedBefore, daysWorkedAfter, today, schedule[employee]
    if daysWorkedBefore+daysWorkedAfter >= 5:
        return False
    else:
        return True

# Get the shift prior to today's shift
def getPreviousShift(employee, day, schedule, lastWeek):
    if day.dayVal==0:
        # If employee had a shift last Sunday
        if lastWeek:
            prevShift = lastWeek[employee][6]
        #If employee didn't work here last week therefore doesn't have a shift last Sunday
        else:
            prevShift = "" # 0 is value representative of not having worked that day
    else:
        prevShift = schedule[employee][day.dayVal-1]
    prevShift = 0 if prevShift == "V" or prevShift == "OFF" else parser.parse(prevShift).hour
    return prevShift

# Get the shift after today's shift
def getNextShift(employee, day, schedule, nextWeek):
    # If it's the last day of the week
    if day.dayVal==6:
        # If employee has a shift next Monday
        if nextWeek:
            nextShift = nextWeek[employee][0]
        #If employee doesn't work next week therefore doesn't have a shift next Monday
        else: 
            nextShift = ""
    else:
        nextShift = schedule[employee][day.dayVal+1]
    nextShift = 24 if nextShift=="" or nextShift=="V" or nextShift=="OFF" else parser.parse(nextShift).hour
    return nextShift

# Calculate time between previous shift and current shift
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

# Calculate time between current shift and next shift
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

# Where all of the scheduling constraints are. Time between shifts, if they're already scheduled, etc.
def canWork(employee, day, shift, hoursLeft, schedule, lastWeek, nextWeek):
    available = False
    # If employee is not scheduled for a shift already
    if schedule[employee][day.dayVal]=='': 
        # Get and parse previous shift if it exists
        prevShift = getPreviousShift(employee, day, schedule, lastWeek)
        # Get and parse shift for the following day if it exists
        nextShift = getNextShift(employee, day, schedule, nextWeek)
        shift = parser.parse(shift).hour
        # Calculate time between prevShift and current shift. Should be at least 12 hours
        if sufficientTimeSincePrevShift(prevShift, shift):
            # Calculate time between next Shift and current shift. Should be at least 12 hours
            if sufficientTimeBeforeNextShift(nextShift, shift):
                if hoursLeft[employee] > 0:
                    # Calculate how many days in a row the employee will work if scheduled today
                    if calculateDaysInARow(employee, day, schedule, lastWeek, nextWeek):
                        available = True
    """                else:
                        print(employee.firstName, "will have worked more than 5 days in a row.")
                else:
                    print(employee.firstName, "has already worked full hours this week.")
            else:
                print(employee.firstName, "has less than 12 hours between this shift and next shift")
        else:
            print(employee.firstName, "has less than 12 hours between this shift and previous shift")
    else:
        print(employee.firstName, " is already scheduled to work on", WEEKDAY_CHOICES[day.dayVal][1])"""
    #if not available:
    #    print(employee, " can't work ",shift, " on ", WEEKDAY_CHOICES[day.dayVal][1])
    #else:
    #    print employee, "can work", shift, "on", WEEKDAY_CHOICES[day.dayVal][1]
    return available

# Check if selected employees can work this shift. If not, choose another. Update schedule, add to employee crew list
def select( sortedEmployees, randInts, shiftCrew, day, shift, pArr, hoursLeft, 
            schedule, lastWeek, nextWeek, scheduleRating):
    for r in randInts:
        counter = 0
        broken = False
        curr = sortedEmployees[r]
        # If selected employee is not available for this shift, select another
        while not(canWork(curr, day, shift, hoursLeft, schedule, lastWeek, nextWeek)):
            #print "counter incrementing ", counter
            counter+=1
            if counter > 50:
                broken = True
                break
            rand = np.random.choice(len(sortedEmployees),1,p=pArr)
            curr = sortedEmployees[rand[0]]
			#print(curr.firstName, pArr[r[0]])
        if not broken:
            shiftCrew.append(curr)
            schedule[curr][day.dayVal] = shift
            #hoursLeft[curr]-=7
        else:
            # Opening shifts and closing shifts most important
            requiredShifts = ["7am", "7:30am", "8am", "1:30pm", "2:30pm", "3:30pm"]
            if shift in requiredShifts:
                scheduleRating[0]+=10
            else:
                scheduleRating[0]+=1
            print "Breaking at shift", shift, " on ", WEEKDAY_CHOICES[day.dayVal][1], counter
    return shiftCrew

# Select all quad members for scheduled quad meeting
def selectQuad(quad, day, employees, schedule, hoursLeft, lastWeek, nextWeek):
    quad = int(quad)
    # Quad meetings are at 6am
    shift = "6am"
    # Check if quad members can work this shift. If not, print message
    for employee in employees:
        if employee.quad == int(quad):
            if canWork(employee, day, shift, hoursLeft, schedule, lastWeek, nextWeek):
                schedule[employee][day.dayVal] = shift
                hoursLeft[employee] -= 7
            else:
                print(employee.firstName, 
                " isn't available for a quad meeting on ", 
                WEEKDAY_CHOICES[day.dayVal][1], 
                ". Please choose another one.")

"""
# Select opening crew for the day
def selectOpen(day, employees, mods, booksellers, schedule, openCount, closeCount, hoursLeft):
    # Number of MODs and Booksellers that have been scheduled for this shift
    modCount, booksellerCount = 0, 0
    # Number of MODs and Booksellers that need to be scheduled for this shift
    numMods, numBooksellers = 1, 2
    # Add employees who have requested to open to the opening crew
    openingCrew, modCount, booksellerCount = checkRequests(day, day.openingShift, modCount, booksellerCount, employees, mods, schedule)
    
    sortedMods, pModArr = calculateProbability(mods, openCount)
    sortedBooksellers, pBooksellerArr = calculateProbability(booksellers, openCount)

    # Generate weighted "random" numbers using the probability arrays (these are arrays of numbers)
    randModInts = np.random.choice(len(mods), numMods-modCount, p=pModArr) 
    randBooksellerInts = np.random.choice(len(booksellers), numBooksellers-booksellerCount, p=pBooksellerArr)
    
    openingCrew = select(   sortedMods, randModInts, openingCrew, day, 
                            day.openingShift, pModArr, hoursLeft, schedule)
    openingCrew = select(   sortedBooksellers, randBooksellerInts, openingCrew, 
                            day, day.openingShift, pBooksellerArr, hoursLeft, schedule)
    
    for employee in openingCrew:
        openCount[employee]+=1
        hoursLeft[employee]-=7
    """

# Select shift crew for the day (opening and closing)
def selectShiftCrew(day, shift, employees, mods, booksellers, schedule,
                    lastWeek, nextWeek, shiftCount, hoursLeft, numMods, 
                    numBooksellers, scheduleRating):
    # Number of MODs and Booksellers that have been scheduled for this shift
    modCount, booksellerCount = 0, 0

    # Add employees who have requested to open to the opening crew
    shiftCrew, modCount, booksellerCount = checkRequests(  day, shift, modCount, booksellerCount, employees, 
                                mods, schedule)
    
    sortedMods, pModArr = calculateProbability(mods, shiftCount)
    sortedBooksellers, pBooksellerArr = calculateProbability(   booksellers, 
                                                                shiftCount)

    # Generate arrays of weighted "random" numbers using the probability arrays
    randModInts = np.random.choice(len(mods), numMods-modCount, p=pModArr) 
    randBooksellerInts = np.random.choice(  len(booksellers), 
                                            numBooksellers-booksellerCount, 
                                            p=pBooksellerArr)

    shiftCrew = select( sortedMods, randModInts, shiftCrew, day, shift, 
                        pModArr, hoursLeft, schedule, lastWeek, nextWeek, scheduleRating)
    shiftCrew = select( sortedBooksellers, randBooksellerInts, shiftCrew, day, 
                        shift, pBooksellerArr, hoursLeft, schedule,
                        lastWeek, nextWeek, scheduleRating)
    
    for employee in shiftCrew:
        shiftCount[employee]+=1
        hoursLeft[employee]-=7

    #print WEEKDAY_CHOICES[day.dayVal][1], shiftCrew, len(shiftCrew), numBooksellers

# Select mid crew. Differs from selectShiftCrew() in enough respects to warrant its own method
def selectMids( day, employees, shift, mods, booksellers, schedule, lastWeek, 
                nextWeek, hoursLeft, numMods, numBooksellers, scheduleRating):
    # Number of MODs and Booksellers that have been scheduled for this shift
    modCount, booksellerCount = 0, 0

    # Add employees who have requested to open to the opening crew
    shiftCrew, modCount, booksellerCount = checkRequests(  day, shift, modCount, booksellerCount, employees, 
                                mods, schedule)

    # Generate arrays of random numbers corresponding to employees
    randModInts = random.sample(range(0, len(mods)), numMods-modCount)
    randBooksellerInts = random.sample(range(0, len(booksellers)), numBooksellers-booksellerCount)

    # Generate even pModArr so we can re-use "select" method
    pModArr = [float(1)/len(mods)]*len(mods)
    pBooksellerArr = [float(1)/len(booksellers)]*len(booksellers)

    shiftCrew = select( mods, randModInts, shiftCrew, day, shift, 
                        pModArr, hoursLeft, schedule, lastWeek, 
                        nextWeek, scheduleRating)
    shiftCrew = select( booksellers, randBooksellerInts, shiftCrew, day, 
                        shift, pBooksellerArr, hoursLeft, schedule,
                        lastWeek, nextWeek, scheduleRating)
    
    for employee in shiftCrew:
        hoursLeft[employee]-=7

# Check if quad meeting is scheduled to happen for this day
def quadMeetingToday(day, quadMeetings):
    today = WEEKDAY_CHOICES[day.dayVal][0]
    for quad in quadMeetings:
            if quadMeetings[quad]==today:
                return True, quad
    return False, None

# Get probability array for unscheduled days only
def getRelevantPArr(employeeCountArr, pArr, unscheduledDays):
    relevantPArr = []
    for day in unscheduledDays:
        relevantPArr.append(pArr[day.dayVal])
    #print("pArr: ", pArr, "relevantPARR: ", relevantPArr)
    sumArr = sum(relevantPArr)
    for i, p in enumerate(relevantPArr):
        relevantPArr[i] = float(p)/sumArr
    #print relevantPArr
    return relevantPArr

# Make sure everyone is working their full hours
def fillSchedule(weekDays, employees, schedule, hoursLeft, lastWeek, nextWeek):
    # Array of count of extra mids per weekday
    employeeCountArr = [0 for i in range(7)]
    # Probability array starts out even
    pArr = [float(100)/7 for i in range(7)]
    for employee in employees:
        # Should be divisible by 7, but if it isn't, we'll ignore the extra hours
        while hoursLeft[employee]/7 > 0:
            # Fill array with indices of unscheduled days
            unscheduledDays = []
            for day in weekDays:
                if schedule[employee][day.dayVal]=="":
                    unscheduledDays.append(day)
            relevantPArr = getRelevantPArr(employeeCountArr, pArr, unscheduledDays)
            randomDay = np.random.choice(unscheduledDays, 1, p=relevantPArr)[0]
            #print(relevantPArr, randomDay.dayVal)
            #for day in unscheduledDays:
            #    print day.dayVal
            #randomDay = random.randint(0, len(unscheduledDays)-1)
            #randomDay = unscheduledDays[randomDay]
            #print randomDay, randomDay
            if canWork(employee, randomDay, "11am", hoursLeft, schedule, lastWeek, nextWeek):
                schedule[employee][randomDay.dayVal] = "11am"
                # Increase count of employees chosen for this day
                employeeCountArr[randomDay.dayVal]+=1
                # Halve the probability of this day getting chosen again
                pArr[randomDay.dayVal] = pArr[randomDay.dayVal]/10
                hoursLeft[employee]-=7
            """else:
                print "PROBLEMS!!! AHHHHH", employee.firstName, hoursLeft[employee], schedule[employee]
                for x in unscheduledDays:
                    print x.dayVal"""
            #print employee.firstName, hoursLeft[employee], unscheduledDays, randomDay
        for day in weekDays:
            if schedule[employee][day.dayVal]=="":
                schedule[employee][day.dayVal]="OFF"
    print pArr


# All the brains are here! Filling out the schedule by priority
def createSchedule( weekStart, weekEnd, quadMeetings, weekDays, employees, 
                    mods, booksellers, vacationRequests, shiftRequests, 
                    recurringShiftRequests, hoursLeft, openCount, closeCount,
                    lastWeek, nextWeek, schedules, schedule, scheduleRating):

    for day in weekDays:
        """
        for quad in quadMeetings:
            # If quad meeting is scheduled to happen for this day
            if quadMeetings[quad]==WEEKDAY_CHOICES[day.dayVal][0]:
                selectQuad(quad, day, employees, schedule, hoursLeft)
        """
        quadIsMeeting, quad = quadMeetingToday(day, quadMeetings)
        if quadIsMeeting:
            selectQuad(quad, day, employees, schedule, hoursLeft, lastWeek, nextWeek)
 
    for day in weekDays:
        #Needs to be here so it resets every day
        # Number of MODs and Booksellers that need to be scheduled for opening
        numModsOpening, numBooksellersOpening = 1, 1 if quadMeetingToday(day, quadMeetings)[0] else 2
        # Number of MODs and Booksellers that need to be scheduled for closing
        numModsClosing, numBooksellersClosing = 1, 3

        # Paul can't open I guess?
        paul = None
        for bookseller in booksellers:
            if bookseller.firstName=="Paul" and bookseller.lastName=="Shirley":
                paul = bookseller
                booksellers.remove(bookseller)

        # Select opening crew
        selectShiftCrew(day, day.openingShift, employees, mods, booksellers, 
                        schedule, lastWeek, nextWeek, openCount, hoursLeft, 
                        numModsOpening, numBooksellersOpening, scheduleRating)

        # Reinstate Paul
        booksellers.append(paul)

        # Carolyn doesn't want to close
        carolyn = None
        for bookseller in booksellers:
            if bookseller.firstName=="Carolyn" and bookseller.lastName=="Chan":
                carolyn = bookseller
                booksellers.remove(bookseller)

        # Select closing crew
        selectShiftCrew(day, day.closingShift, employees, mods, booksellers, 
                        schedule, lastWeek, nextWeek, closeCount, hoursLeft,
                        numModsClosing, numBooksellersClosing, scheduleRating)

        # Reinstate Carolyn
        booksellers.append(carolyn)

    # Reversed because weekend days have priority
    for day in reversed(weekDays):
        # Number of Booksellers coming in when the store opens
        numBooksellersOpenMid = 2 if day.dayVal==5 or day.dayVal==6 else 1
        # Number of MODs and Booksellers coming in at 11am
        #numModsMid, numBooksellersMid = 1, 2 if quadMeetingToday(day, quadMeetings)[0] else 3
        numModsMid, numBooksellersMid = 1, 1 if quadMeetingToday(day, quadMeetings)[0] else 2
        # Number of MODs coming in at 12pm (only on Fri, Sat, Sun)
        numModsNoon = 1 if day.dayVal==4 or day.dayVal==5 or day.dayVal==6 else 0
        # Select mids coming in at opening time
        selectMids( day, employees, day.openingHour, mods, booksellers, schedule, 
                    lastWeek, nextWeek, hoursLeft, 0, numBooksellersOpenMid, scheduleRating)
        # Select mids coming in at 11am
        selectMids( day, employees, "11am", mods, booksellers, schedule, 
                    lastWeek, nextWeek, hoursLeft, numModsMid, 
                    numBooksellersMid, scheduleRating)
        # Select mid MODs coming in at 12pm
        selectMids( day, employees, "12pm", mods, booksellers, schedule, 
                    lastWeek, nextWeek, hoursLeft, numModsNoon, 0, scheduleRating)
    fillSchedule(weekDays, employees, schedule, hoursLeft, lastWeek, nextWeek)

# Save generated schedule in database for review        
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

# Temporary. To see the schedule        
def printSchedule(  employees, schedule, hoursLeft, openCount, closeCount, 
                    selectedDate):
    print("------------------------------------------------------------------------------------------------------------------------------------")
    print("                                                  HPB SCHEDULE FOR THE WEEK OF", selectedDate)
    print("------------------------------------------------------------------------------------------------------------------------------------")
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
			#print(timeToShift(shift).center(15," ")),
        print str(hoursLeft[employee]).ljust(3),
        print openCount[employee],
        print closeCount[employee]

#def terminateShifts():  
#    Shift.objects.all().delete()

def generatePotentialSchedule(employees, vacationRequests, shiftRequests, recurringShiftRequests, schedules, selectedDate, quadMeetings):
    mods = []
    booksellers = []
    weekDays = []
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

    print("SCHEDULE RATING: ", scheduleRating)

    return schedule, scheduleRating, weekStart

def generate(form):
    employees = Employee.objects.all()
    vacationRequests = VacationRequest.objects.all()
    shiftRequests = ShiftRequest.objects.all()
    recurringShiftRequests = RecurringShiftRequest.objects.all()
    schedules = WeekSchedule.objects.all()

    selectedDate, quadMeetings = getFormData(form)

    """mods = []
    booksellers = []
    weekDays = []
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

    #TEMPORARY - PLEASE FIX (add new schedule class for long term schedule storage)
    #terminateShifts()

    weekStart, weekEnd = initialize(selectedDate, **params)
    scheduleA = createSchedule(weekStart, weekEnd, quadMeetings, **params)

    print("SCHEDULE RATING: ", scheduleRating)
    printSchedule(employees, schedule, hoursLeft, openCount, closeCount, selectedDate)

    mods = []
    booksellers = []
    weekDays = []
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
    scheduleB = createSchedule(weekStart, weekEnd, quadMeetings, **params)

    print ("SCHEDULE RATING: ", scheduleRating)
    printSchedule(employees, schedule, hoursLeft, openCount, closeCount, selectedDate)

    mods = []
    booksellers = []
    weekDays = []
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
    scheduleC = createSchedule(weekStart, weekEnd, quadMeetings, **params)

    print("SCHEDULE RATING: ", scheduleRating)
    printSchedule(employees, schedule, hoursLeft, openCount, closeCount, selectedDate)
    """
    regenerate = 10

    schedule, scheduleRating, weekStart =   generatePotentialSchedule( employees,
                                            vacationRequests, shiftRequests, 
                                            recurringShiftRequests, schedules, 
                                            selectedDate, quadMeetings)
    for i in range(0, regenerate):
        if scheduleRating[0]==0:
            break
        print "Regenerating schedule"
        tempSchedule, tempScheduleRating, weekStart = generatePotentialSchedule(employees,
                                                vacationRequests, shiftRequests, 
                                                recurringShiftRequests, schedules, 
                                                selectedDate, quadMeetings)
        print("New schedule rating: ", tempScheduleRating)
        if tempScheduleRating < scheduleRating:
            schedule = tempSchedule
            scheduleRating = tempScheduleRating
            print "Saving new schedule"
        else:
            print "Throwing out new schedule"

    saveSchedule(weekStart, employees, schedule)
    print("Final schedule rating", scheduleRating)
    #printSchedule(employees, schedule, hoursLeft, openCount, closeCount, selectedDate)
    return schedule

    #TEMPORARY - PLEASE FIX
    #terminateShifts()