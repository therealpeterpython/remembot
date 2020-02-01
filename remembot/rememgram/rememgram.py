"""
This is the version v2.0 of the rememgram backend written by
therealpeterpython (github.com/therealpeterpython).
You can find the bot, this code and my other work at
github.com/therealpeterpython/remembot.
Feel free to submit issues, requests and feedback via github.

This program is licensed under CC BY-SA 4.0 by therealpeterpython.
"""


# todo replace # with \""" in descriptions
# todo rename: task -> appointment

from remembot.common.helper import parse_appointment_str
from remembot.common.constants import *
from remembot.common.config import tasks_path, old_tasks_path
from remembot.bot import frankenbot as bot

from uuid import uuid4
import datetime as dt
import calendar as cal
import calendar
import pickle
import sys


class Appointment:
    def __str__(self):
        attrs = vars(self)
        return ', '.join("%s: %s" % item for item in attrs.items())

    def __init__(self, id, chat_id, bot, type, description, time, date=None, count=None, weekday=None):
        self.id = id
        self.chat_id = chat_id
        self.bot = bot
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
            # gets the last time the task should have been executed #
            last_occurrence = appointment_datetime + dt.timedelta(days=(((now - appointment_datetime).days // self.count) * self.count))
            return self.last_execution < last_occurrence < now and appointment_datetime < now
        elif self.type == NTH_WEEKDAY:
            # gets the occurrence this month #
            occurrence_current_month = get_nth_weekday(dt.datetime.combine(now.date(), self.time), self.count, self.weekday)
            return self.last_execution < occurrence_current_month < now
        elif self.type == NUM:
            # get the valid day for this month #
            occ_day = get_valid_day(now.year, now.month, self.date.day)
            # create the valid occurrence date for this month #
            occ = dt.datetime(now.year, now.month, occ_day, self.time.hour, self.time.minute)
            return self.last_execution < occ < now

    # todo testen
    def pprint(self):
        """
        Creates a pretty print string of the stored appointment data.

        :return: Pretty string which can be printed without regrets.
        """
        text = ""
        if self.type == ONCE:
            text += "Once at {}. {} {}: \"{}\"".format(calendar.day_abbr[self.date.weekday()], self.get_date(), self.get_time(), self.description)
        elif self.type == EVERY_N_DAYS:
            text += "Every {} days at {}, starting with the {}. {}: \"{}\"".format(self.count, self.get_time(), calendar.day_abbr[self.date.weekday()], self.get_date(), self.description)
        elif self.type == NTH_WEEKDAY:
            text += "Every {}. {} at {}: \"{}\"".format(self.count, calendar.day_name[self.weekday], self.get_time(), self.description)
        elif self.type == NUM:
            text += "Every month at {} {}: \"{}\"".format(self.date.strftime("%d."), self.get_time(), self.description)
        return text

    def get_date(self): return self.date.strftime(DATE_FORMAT)

    def get_time(self): return self.time.strftime(TIME_FORMAT)


def get_valid_day(year, month, day):
    """
    Caps the day at the biggest day for the given month and at 1 if
    necessary. Useful for transitions (e.g.) 30.1 -> 28.2.
    """
    num_days = cal.monthrange(year, month)[1]
    day = max(1, day)
    day = min(num_days, day)
    return day


def subtract_one_month(t):
    """
    Return a `datetime.date` or `datetime.datetime` (as given) that
    is one month later.
    Note that the resultant day of the month might change if the
    following month has fewer days:
        subtract_one_month(datetime.date(2010, 3, 31))
        == datetime.date(2010, 2, 28)
    """
    one_day = dt.timedelta(days=1)
    one_month_earlier = t
    while one_month_earlier.month == t.month or one_month_earlier.day > t.day:
        one_month_earlier -= one_day
    return one_month_earlier


def get_nth_weekday(date, nth_week, week_day):
    """
    Return the nth occurrence of week_day in the month in the year
    given by date. If there are not enough occurrences of the
    week_day in the month then the nth_week parameter gets decreased
    by 1.
    """
    temp = date.replace(day=1)
    diff = (week_day - temp.weekday()) % 7
    temp += dt.timedelta(days=diff)  # temp is now the first occurrence of the weekday in the given month
    temp += dt.timedelta(weeks=nth_week-1)
    while temp.month != date.month:
        temp.month -= dt.timedelta(weeks=1)
    return temp


'''
def expand_year(year):
    """
    A quick way to expand years after 2000 takes None, str and int as
    input type (e.g.) 19 -> 2019    
    """
    if not year:
        year = None
    else:
        year = int(year)
        year += 2000 if year < 2000 else 0
    return year
'''


# todo testen
# todo doc
def add_appointment(app_str, chat_id, bot):
    # get all appointments #
    appointments = load_tasks()

    # split the appointment blocks #
    appointment_blocks = parse_appointment_str(app_str)
    new_appointments = []

    # if app_str was not valid #
    if not appointment_blocks:
        return []

    # process the blocks #
    for block in appointment_blocks:
        if block[1] == ONCE:
            data = process_once(block)
        elif block[1] == EVERY_N_DAYS:
            data = process_every_n_days(block)
        elif block[1] == NTH_WEEKDAY:
            data = process_nth_weekday(block)
        elif block[1] == NUM:
            data = process_num(block)
        else:
            continue

        uid = str(uuid4())  # hash(tuple(block + [chat_id, bot]))
        appointment = Appointment(id=uid, chat_id=chat_id, bot=bot, **data)
        new_appointments.append(appointment)
        print("New Appointment: ", appointment)

    appointments.extend(new_appointments)

    # save and check all appointments #
    save_tasks(appointments)
    check_tasks()

    return new_appointments


def process_once(parameters):
    date = dt.datetime.strptime(parameters[2], DATE_FORMAT).date()  # todo test dis shit i'm out ahh
    time = dt.datetime.strptime(parameters[3], TIME_FORMAT).time()
    return {"type": ONCE, "date": date, "time": time, "description": parameters[4]}


def process_every_n_days(parameters):
    date = dt.datetime.strptime(parameters[3], DATE_FORMAT).date()
    time = dt.datetime.strptime(parameters[4], TIME_FORMAT).time()
    return {"type": EVERY_N_DAYS, "count": int(parameters[2]), "date": date, "time": time, "description": parameters[5]}


def process_nth_weekday(parameters):
    time = dt.datetime.strptime(parameters[4], TIME_FORMAT).time()
    return {"type": NTH_WEEKDAY, "count": int(parameters[2]), "weekday": int(parameters[3]), "time": time, "description": parameters[5]}


def process_num(parameters):
    date = dt.datetime.strptime(parameters[2], DATE_FORMAT).date()
    time = dt.datetime.strptime(parameters[3], TIME_FORMAT).time()
    return {"type": NUM, "date": date, "time": time, "description": parameters[4]}


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


# saves the tasks with a consistent name
def save_tasks(tasks):
    old_tasks = load_tasks()
    save_object(old_tasks, old_tasks_path)
    save_object(tasks, tasks_path)


# load the tasks list
def load_tasks():
    tmp = load_object(tasks_path)
    return tmp if tmp else []


# todo ggf. diese methode in save_tasks mergen
# pickles an object to filename
def save_object(obj, filename):
    with open(filename, 'wb') as output:  # Overwrites any existing file.
        pickle.dump(obj, output)


# todo ggf. diese methode in load_tasks mergen
# unpickles an object from filename
def load_object(filename):
    try:
        with open(filename, 'rb') as input:
            return pickle.load(input)
    except FileNotFoundError:
        return None
