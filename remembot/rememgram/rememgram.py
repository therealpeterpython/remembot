# The "second backend" of the remembot
# todo put more infos here
#
#

from remembot.common.helper import process_appointment_str
from remembot.common.constants import *

import datetime as dt
import calendar as cal
import remembot.bot.rem_bot as rb
import remembot.bot.frankenbot as bot
import pickle
#import sys

# todo wtf
days_lookup = {'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3, 'friday': 4, 'saturday': 5, 'sunday': 6, 'montag': 0, 'dienstag': 1, 'mittwoch': 2, 'donnerstag': 3, 'freitag': 4, 'samstag': 5, 'sonntag': 6}

#today = dt.datetime.today()

# todo rename: task -> appointment


class Appointment:
    def __str__(self):
        attrs = vars(self)
        return ', '.join("%s: %s" % item for item in attrs.items())

    def __init__(self, id, chat_id, type, description, time, date=None, count=None, weekday=None):
        self.id = id
        self.chat_id = chat_id
        self.last_execution = dt.datetime(1, 1, 1, 0, 0)
        self.type = type
        self.date = date
        self.time = time
        self.description = description
        self.count = count
        self.weekday = weekday

    # todo testen
    def needs_execution(self):
        now = dt.datetime.now()
        if self.type == ONCE:
            return dt.datetime.combine(self.date, self.time) < now
        elif self.type == EVERY_N_DAYS:
            appointment_datetime = dt.datetime.combine(self.date, self.time)
            # gets the last time the task should have been executed
            last_occurrence = appointment_datetime + dt.timedelta(
                days=(((now - appointment_datetime).days // self.count) * self.count))
            return self.last_execution < last_occurrence < now and appointment_datetime < now
        elif self.type == NTH_WEEKDAY:
            # gets the occurrence this month
            occurrence_current_month = get_nth_weekday(dt.datetime.combine(now.date(), self.time), self.count,
                                                       self.weekday)
            return self.last_execution < occurrence_current_month < now
        elif self.type == NUM:
            # get the valid day for this month
            occ_day = get_valid_day(now.year, now.month, self.date.day)
            # create the valid occurrence date for this month
            occ = dt.datetime(now.year, now.month, occ_day, self.time.hour, self.time.minute)
            return self.last_execution < occ < now

    # returns a pretty string version of the appointment
    def pprint(self):
        pass  # todo


# todo OLD
# Saves the time informations of a task
#
class schedule:
    def __init__(self, format, day, hour, minute, week_number=None, year=None, month=None):
        self.format = format
        self.day = day
        self.hour = hour
        self.minute = minute
        self.week_number = week_number
        self.year = year
        self.month = month

    # gets invoked with str(a_schedule), usefull for debugging
    def __str__(self):
        lst = [self.format, self.day, self.hour, self.minute, self.week_number, self.year, self.month]
        s = "schedule(" + ', '.join([str(e) for e in lst]) + ")"
        return s


# todo OLD
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
        if format == "wd":  # (weekday) regular at every nth (e.g.) monday
            occ = get_nth_weekday(dt.datetime(now.year, now.month, 1, schedule.hour, schedule.minute), schedule.week_number, schedule.day)
            prev = get_nth_weekday(subtract_one_month(dt.datetime(now.year, now.month, 1, schedule.hour, schedule.minute)), schedule.week_number, schedule.day)

            # If there wasnt a first execution now, then there wasnt a last execution also
            prev = prev if self.last_execution else None
            return occ if (occ - now).days < 0 else prev

        elif format == "d":  # (date) regular every (e.g.) 13.
            # get the valid day for this month
            occ_day = get_valid_day(now.year, now.month, schedule.day)
            # create the valid occurrence date for this month
            occ = dt.datetime(now.year, now.month, occ_day, schedule.hour, schedule.minute)

            # create the valid occurence date for the prev month(except the day)
            # we cant change the order of this since we have to ensure that now.month-1 is a valid month
            prev = subtract_one_month(dt.datetime(now.year, now.month, 1, schedule.hour, schedule.minute))
            # now can we be sure that prev.year and prev.month are valid and we change to the right day
            prev.replace(day=get_valid_day(prev.year, prev.month, schedule.day))

            # If there wasnt a first execution now, then there wasnt a last execution also
            prev = prev if self.last_execution else None

            # if the right date had already been this month it gets returned
            # otherwise the prev last month was the last one and gets returned
            return occ if (occ - now).days < 0 else prev

        elif format == "swd":   # (single weekday) just once at the nth (e.g.) monday
            occ = get_nth_weekday(dt.datetime(schedule.year, schedule.month, 1, schedule.hour, schedule.minute), schedule.week_number, schedule.day)
            return schedule if (occ - now).days < 0 else None

        elif format == "sd":    # (single date) just once some date
            print("SD")
            occ = dt.datetime(schedule.year, schedule.month, schedule.day, schedule.hour, schedule.minute)
            print("OCC: "+str(occ))
            print("NOW: "+str(now))
            return schedule if (occ - now).days < 0 else None


# Caps the day at the max or min if necessary
# Useful for transitions (e.g.) 30.1 -> 28.2
def get_valid_day(year, month, day):
    num_days = cal.monthrange(year, month)[1]
    day = max(1, day)
    day = min(num_days, day)
    return day


def subtract_one_month(t):
    """Return a `datetime.date` or `datetime.datetime` (as given) that is
    one month later.
    Note that the resultant day of the month might change if the following
    month has fewer days:
        subtract_one_month(datetime.date(2010, 3, 31))
        == datetime.date(2010, 2, 28)
    """
    one_day = dt.timedelta(days=1)
    one_month_earlier = t
    while one_month_earlier.month == t.month or one_month_earlier.day > t.day:
        one_month_earlier -= one_day
    return one_month_earlier

# todo garbage
"""
# Creates a valid date
# If a parameter is out of range it will be trimmed at max or min
def create_valid_date(year, month, day, hour, minute):
    if month > 12:
        year += 1
        month -= 12
    if month < 1:
        year -= 1
        month += 12

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
"""


# Return the nth occurrence of week_day
# in the month in the year given by date
# If there are not enough occurences of the week_day in the month
# then the nth_week parameter gets decresed by 1
def get_nth_weekday(date, nth_week, week_day):
    temp = date.replace(day=1)
    diff = (week_day - temp.weekday()) % 7
    temp += dt.timedelta(days=diff)  # temp is now the first occurrence of the weekday in the given month
    temp += dt.timedelta(weeks=nth_week-1)
    while temp.month != date.month:
        temp.month -= dt.timedelta(weeks=1)
    return temp


# a quick way to expand years after 2000
# takes None, str and int as input type
# (e.g.) 19 -> 2019
def expand_year(year):
    if not year:
        year = None
    else:
        year = int(year)
        year += 2000 if year < 2000 else 0
    return year


# todo testen
def add_appointment(app_str, chat_id):
    # get all appointments #
    appointments = load_tasks()

    # split the appointment blocks #
    appointment_blocks = process_appointment_str(app_str)

    # process the blocks #
    for block in appointment_blocks:
        if block[1] == ONCE:
            args = process_once(block)
        elif block[1] == EVERY_N_DAYS:
            args = process_every_n_days(block)
        elif block[1] == NTH_WEEKDAY:
            args = process_nth_weekday(block)
        elif block[1] == NUM:
            args = process_num(block)

        id = hash(tuple(block + [chat_id]))
        appointment = Appointment(id=id, **args)
        appointments.append(appointment)

    # save and check all appointments #
    save_tasks(appointments)
    check_tasks()


# todo OLD
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


def process_once(parameters):
    return {"type": ONCE, "date": parameters[2], "time": parameters[3], "description": parameters[4]}

def process_every_n_days(parameters):
    return {"type": EVERY_N_DAYS, "count": parameters[2], "date": parameters[3], "time": parameters[4], "description": parameters[5]}

def process_nth_weekday(parameters):
    return {"type": NTH_WEEKDAY, "count": parameters[2], "weekday": parameters[3], "time": parameters[4], "description": parameters[5]}

def process_num(parameters):
    return {"type": NUM, "date": parameters[2], "time": parameters[3], "description": parameters[4]}


# deletes all tasks with ids in 'remove_ids'
def delete_tasks(remove_ids):
    tasks = load_tasks()
    tmp = list(tasks)  # dont iterate over a changing list
    for task in tmp:
        if task.id in remove_ids:
            tasks.remove(task)
    save_tasks(tasks)


# delete all tasks of given chat
def delete_all_tasks(chat_id):
    tasks = load_tasks()
    tmp = list(tasks)  # dont iterate over a changing list
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


# todo test
# check if a task needs to be executed
def check_tasks():
    now = dt.datetime.now()
    appointments = load_tasks()
    tmp = list(appointments)

    for appointment in tmp:
        if appointment.needs_execution():
            execute(appointment)
            appointment.last_execution = now  # save actual execution
            if appointment.type == ONCE:  # execute it just once
                appointments.remove(appointment)

    save_tasks(appointments)


# executes a task
def execute(appointment):
    bot.remind(appointment)


# todo remove
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
        if len(args[1]) < 4:    # (e.g.) 'once 12. Monday 3.2019 8:30'
            format = "swd"
            week_number = int(args[1].split(".")[0])
            weekday = args[2]
            day = days_lookup[weekday.lower()]
            month = int(args[3].split(".")[0])
            year = args[3].split(".")[1]
            hour = args[4].split(":")[0]
            minute = args[4].split(":")[1]

        else:   # (e.g.) 'once 7.3.2019 9:30'
            format = "sd"
            tmp = args[1].split(".")
            day = tmp[0]
            month = int(tmp[1])
            year = tmp[2]
            hour = args[2].split(":")[0]
            minute = args[2].split(":")[1]

    else:
        if len(args) == 3:  # (e.g.) '3. Friday 3:14'
            format = "wd"
            week_number = int(args[0].split(".")[0])
            weekday = args[1]
            day = days_lookup[weekday.lower()]
            hour = args[2].split(":")[0]
            minute = args[2].split(":")[1]
        else:   # (e.g.) '2. 3:33'
            if args[0].split(".")[1]:   # (e.g.) '2.12 3:33'
                print("Wrong format!")
                print(args, description)
                raise ValueError
            format = "d"
            day = args[0].split(".")[0]
            hour = args[1].split(":")[0]
            minute = args[1].split(":")[1]

    return str(description), str(format), int(day), int(hour), int(minute), week_number, expand_year(year), month


# todo cp to tasks.pkl.old and write to file
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
