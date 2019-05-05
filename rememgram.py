# The "second backend" of the remembot
# todo put more infos here
#
#

import datetime as dt
import calendar as cal
import rem_bot as rb

import pickle

#import sys


#days = {0:"Monday", 1:"Tuesday", 2:"Wednesday", 3:"Thursday", 4:"Friday", 5:"Saturday", 6:"Sunday"}
#months = {0:"January", 1:"February", 2:"March", 3:"April", 4:"May", 5:"June", 6:"July", 7:"August", 8:"September", 9:"October", 10:"November", 11:"December"}

#days_de = {0:"Montag", 1:"Dienstag", 2:"Mittwoch", 3:"Donnerstag", 4:"Freitag", 5:"Samstag", 6:"Sonntag"}
#months_de = {0:"Januar", 1:"Februar", 2:"März", 3:"April", 4:"Mai", 5:"Juni", 6:"Juli", 7:"August", 8:"September", 9:"Oktober", 10:"November", 11:"Dezember"}

days_lookup = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6, 'montag': 0, 'dienstag': 1, 'mittwoch': 2, 'donnerstag': 3, 'freitag': 4, 'samstag': 5, 'sonntag': 6}

today = dt.datetime.today()


#
#
# Possible time formats:
# - jeden nten wochentag wd jeden Monats um h:mm Uhr "n;wd;h:mm;wd" (weekday)
# [- jeden nten wochentag wd jedes Mten Monats um h:mm Uhr "n;wd;M;h:mm;wdm" (weekdayMonth)]
# [- jeden xten wochentag im Monat um h:mm Uhr "x;h:mm;wd" (weekday) [spezialfall von weekdayMonth, als solchen implementieren]]
#
# - jeden nten tag jeden Monats um h:mm uhr "n;h:mm;d" (date)
# [- jeden nten tag jedes Mten Monats um h:mm uhr "n;M;h:mm;dm" (dateMonth)]
# [- jeden xten tag im Monat um h:mm uhr "x;h:mm" (date) [spezialfall von dateMonth, als solchen implementieren]]
#
# - einmalig am nten wochentag wd im Mten monat im Jahr YYYY um h:mm "n;wd;M;YYYY;h:mm;swd" (singleWeekday)
# - einmalig am nten Tag im Mten monat im Jahr YYYY um h:mm "n;M;YYYY;h:mm;sd" (singleDate)
#
# /add 3. Freitag 3:14 "Hier kommt die Beschreibung rein"
# /add 2. 3:33 "Beschreibung"
# /add einmal 2. Montag 3.2019 8:30 "Die Beschreibung"
# /add einmal 7.3.2019 9:30 "Auch hier Beschreibung"
#

"""

Mit /add können neue Termine hinzugefügt werden. Es gibt dabei 4 Arten von Terminen:
1) Ein einmaliger Termin nach Wochentag, z.b.: 1x 1. Montag 3.2019 13:37 "Dies ist ein wichtiger Termin"
2) Ein einmaliger Termin nach Datum, z.b.: 20.4.2019 4:20 "Das solltest du nicht vergessen"
3) Ein monatlicher Termin nach Wochentag, z.b.: 2. Freitag 6:66 "Das Datum ist wichtig"
4) Ein monatlicher Termin nach Datum, z.b.: 3. 17:42 "Hier war doch was!"

Mit /all können alle Termine eingesehen werden. mit /allid können die ids der Termine angezeigt werden sodass diese mit /del <id> gelöscht werden können.
/help zeigt dir wieder diese Hilfe an.

"""

# Saves the time informations of a task
#
class schedule:
    def __init__(self,format,day,hour,minute,week_number=None,year=None,month=None):
        self.format = format
        self.day = day
        self.hour = hour
        self.minute = minute
        self.week_number = week_number
        self.year = year
        self.month = month

    def __str__(self):
        s = "schedule(" + ', '.join(self.format, self.day, self.hour, self.minute, self.week_number, self.year, self.month) + ")"
        return s

# A task which contains an unique id, his description, schedule and chat id(so that it knows to which chat it belongs)
class task:
    def __init__(self, id, description, schedule, chat_id):
        self.id = id
        self.description = description
        self.schedule = schedule
        self.chat_id = chat_id
        self.last_execution = None

    # returns true if the task needs an execution
    def need_execution(self):
        return not (self.get_previous_occurance() == self.last_execution)

    # gets the last time the task should have been executed
    def get_previous_occurance(self):
        schedule = self.schedule
        format = schedule.format
        now = dt.datetime.now()
        if format == "wd":  # (weekday) regular at every nth (i.e.) monday
            occ = get_nth_weekday(dt.datetime(now.year, now.month, 1, schedule.hour, schedule.minute), schedule.week_number, schedule.day)
            prev = get_nth_weekday(create_valid_date(now.year, now.month-1,1, schedule.hour, schedule.minute), schedule.week_number, schedule.day)

            # If there wasnt a first execution now, then there wasnt a last execution also
            prev = prev if self.last_execution else None
            return occ if (occ - now).days < 0 else prev

        elif format == "d": # (date) regular every (i.e.) 13.
            # get the valid day for this month
            occ_day = get_valid_day(now.year, now.month, schedule.day)
            # create the valid occurrence date for this month
            occ = create_valid_date(now.year, now.month, occ_day, schedule.hour, schedule.minute)

            # create the valid occurence date for the prev month(except the day)
            # we cant change the order of this since we have to ensure that now.month-1 is a valid month
            prev = create_valid_date(now.year, now.month-1, 1, schedule.hour, schedule.minute)
            # now can we be sure that prev.year and prev.month are valid and we change to the right day
            prev.replace(day=get_valid_day(prev.year, prev.month, schedule.day))

            # If there wasnt a first execution now, then there wasnt a last execution also
            prev = prev if self.last_execution else None

            # if the right date had already been this month it gets returned
            # otherwise the prev last month was the last one and gets returned
            return occ if (occ - now).days < 0 else prev

        elif format == "swd":   # (single weekday) just once at the nth (i.e.) monday
            occ = get_nth_weekday(dt.datetime(schedule.year, schedule.month, 1, schedule.hour, schedule.minute), schedule.week_number, schedule.day)
            return schedule if (occ - now).days < 0 else None

        elif format == "sd":    # (single date) just once some date
            print("SD")
            occ = dt.datetime(schedule.year, schedule.month, schedule.day, schedule.hour, schedule.minute)
            print("OCC: "+str(occ))
            print("NOW: "+str(now))
            return schedule if (occ - now).days < 0 else None


# Caps the day at the max or min if necessary
# Useful for transitions (i.e.) 30.1 -> 28.2
def get_valid_day(year, month, day):
    num_days = cal.monthrange(year,month)[1]
    day = max(1, day)
    day = min(num_days, day)

    return day


# Creates a valid date
# If a parameter is out of range it will be trimmed at max or min
def create_valid_date(year, month, day, hour, minute):
    num_days = cal.monthrange(year,month)[1]

    if minute > 59:
        hour += 1
        minute -= 60
    if hour > 23:
        day += 1
        hour -= 24
    if day > num_days:
        month += 1
        day -= num_days
    if month > 12:
        year += 1
        month -= 12

    if minute < 0:
        hour -= 1
        minute += 60
    if hour < 0:
        day -= 1
        hour += 24
    if day < 1:
        month -= 1
    if month < 1:
        year -= 1
        month += 12
    if day < 1: # looks ugly but is important in this order therewith the month can be corrected if necessary
        day += cal.monthrange(year,month)[1]  # its the changed(prev) month!

    return dt.datetime(year, month, day, hour, minute)


# Return the nth occurrence of week_day
# in the month in the year given by the_date
# If there are not enough occurences of the week_day in the month
# then the nth_week parameter gets decresed by 1
def get_nth_weekday(the_date, nth_week, week_day):
    temp = the_date.replace(day=1)
    adj = (week_day - temp.weekday()) % 7
    temp += dt.timedelta(days=adj)
    temp += dt.timedelta(weeks=nth_week-1)
    if temp.month > the_date.month:
        return get_nth_weekday(the_date,nth_week-1, week_day)
    else:
        return temp


# a quick way to expand years after 2000
# takes None, str and int as input type
# (i.e.) 19 -> 2019
def expand_year(year):
    if not year:
        year = None
    else:
        year = int(year)
        year += 2000 if year < 2000 else 0
    return year


# adds a task with parameters args, chat_id='chat_id' and a hash of this as id
def add_task(args, chat_id):
    tasks = load_tasks()

    description, format, day, hour, minute, week_number, year, month = parse_input(args)
    id = hash(tuple(args+[chat_id]))
    new_task = task(id,
                    description,
                    schedule(format, day, hour, minute, week_number, year, month),
                    chat_id)
    tasks.append(new_task)
    save_tasks(tasks)
    check_tasks()


# deletes all tasks with ids in 'remove_ids'
def delete_tasks(remove_ids):
    tasks = load_tasks()
    tmp = list(tasks)   # dont iterate over a changing list
    for task in tmp:
        if task.id in remove_ids:
            tasks.remove(task)
    save_tasks(tasks)


# delete all tasks of given chat
def delete_all_tasks(chat_id):
    tasks = load_tasks()
    tmp = list(tasks) # dont iterate over a changing list
    for task in tmp:
        if task.chat_id == chat_id:
            tasks.remove(task)
    save_tasks(tasks)


# returns the tasks sorted in dict by chat_ids: {id1:[task1.1,task1.2],...}
def get_tasks_by_chat():
    tasks = load_tasks()
    tasks_by_chat = {}

    for task in tasks:
        if task.chat_id in tasks_by_chat:
            tasks_by_chat[task.chat_id].append(task)
        else:
            tasks_by_chat[task.chat_id] = [task]

    return tasks_by_chat


# check if a task has to be executed
def check_tasks():
    tasks = load_tasks()

    print("\n[")
    tmp = list(tasks)
    for t in tmp:
        print("'"+t.description+"',")
    print("]")

    for task in tmp:
        print("Der task '"+str(task.description)+"' benötigt eine Ausführung: " + str(task.need_execution()))
        print("'"+task.description + "' hatte ein last_execution am:"+str(task.last_execution))

        if task.need_execution():
            execute_task(task)

            task.last_execution = task.get_previous_occurance() # save actual execution
            if "s" in task.schedule.format: # execute it just once
                print("remove at pos '"+str(tmp.index(task))+"' the '"+task.description+"'")
                tasks.remove(task)

    save_tasks(tasks)


# executes a task
def execute_task(task):
    rb.remind_task(task)


# parses the input it gets from the rem_bot (to add a task)
def parse_input(args):
    description = ""
    format = ""
    day = -1
    hour = -1
    minute = -1
    week_number = None
    year = None
    month = None

    # get description
    args_string = ' '.join(args).strip()
    fst = args_string.index('"')
    snd = args_string.index('"',fst+1)
    description = args_string[fst+1:snd].strip()
    args = (args_string[:fst] + args_string[snd+1:]).split()

    if args[0] == "einmal" or args[0] == "once" or args[0] == "1x":
        if len(args[1]) < 4:    # (i.e.) 'once 12. Monday 3.2019 8:30'
            format = "swd"
            week_number = int(args[1].split(".")[0])
            weekday = args[2]
            day = days_lookup[weekday.lower()]
            month = int(args[3].split(".")[0])
            year = args[3].split(".")[1]
            hour = args[4].split(":")[0]
            minute = args[4].split(":")[1]

        else:   # (i.e.) 'once 7.3.2019 9:30'
            format = "sd"
            tmp = args[1].split(".")
            day = tmp[0]
            month = int(tmp[1])
            year = tmp[2]
            hour = args[2].split(":")[0]
            minute = args[2].split(":")[1]

    else:
        if len(args) == 3:  # (i.e.) '3. Friday 3:14'
            format = "wd"
            week_number = int(args[0].split(".")[0])
            weekday = args[1]
            day = days_lookup[weekday.lower()]
            hour = args[2].split(":")[0]
            minute = args[2].split(":")[1]
        else:   # (i.e.) '2. 3:33'
            if args[0].split(".")[1]:   # (i.e.) '2.12 3:33'
                print("Wrong format!")
                print(args, description)
                raise ValueError
            format = "d"
            day = args[0].split(".")[0]
            hour = args[1].split(":")[0]
            minute = args[1].split(":")[1]


    return str(description), str(format), int(day), int(hour), int(minute), week_number, expand_year(year), month


# saves the tasks with a consistent name
def save_tasks(tasks):
    save_object(tasks, "tasks.pkl")


# load the tasks list
def load_tasks():
    tmp = load_object("tasks.pkl")
    return tmp if tmp else []


# pickles an object to filename
def save_object(obj, filename):
    with open(filename, 'wb') as output:  # Overwrites any existing file.
        pickle.dump(obj, output, pickle.HIGHEST_PROTOCOL)


# unpickles an object from filename
def load_object(filename):
    try:
        with open(filename, 'rb') as input:
            return pickle.load(input)
    except FileNotFoundError:
        return None
