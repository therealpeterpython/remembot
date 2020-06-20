"""
This is the version v2.0 of the rememgram backend written by
therealpeterpython (github.com/therealpeterpython).
You can find the bot, this code and my other work at
github.com/therealpeterpython/remembot.
Feel free to submit issues, requests and feedback via github.

This program is licensed under CC BY-SA 4.0 by therealpeterpython.
"""


# todo replace # with \"\"\" in descriptions

from remembot.common.helper import parse_appointment_str
from remembot.common.constants import *
from remembot.common.config import appointments_path, old_appointments_path
from remembot.bot import frankenbot as bot

from uuid import uuid4
import datetime as dt
import calendar as cal
import calendar
import pickle


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
            # gets the last time the appointment should have been executed #
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


# todo testen
# todo doc
def add_appointment(app_str, chat_id, bot):
    # get all appointments #
    appointments = load_appointments()

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
    save_appointments(appointments)
    check_appointments()

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


# deletes all appointments with ids in 'remove_ids'
def delete_appointments(remove_ids):
    appointments = load_appointments()
    tmp = list(appointments)  # don't iterate over a changing list
    for appointment in tmp:
        if appointment.id in remove_ids:
            appointments.remove(appointment)
    save_appointments(appointments)


# returns the appointments sorted in dict by chat_ids: {id1:[appointment1.1,appointment1.2],...}
def get_appointments_by_chat():
    appointments = load_appointments()
    appointments_by_chat = {}

    for appointment in appointments:
        if appointment.chat_id in appointments_by_chat:
            appointments_by_chat[appointment.chat_id].append(appointment)
        else:
            appointments_by_chat[appointment.chat_id] = [appointment]

    return appointments_by_chat


# check if a appointment needs to be executed
def check_appointments():
    now = dt.datetime.now()
    appointments = load_appointments()
    tmp = list(appointments)

    for appointment in tmp:
        if appointment.needs_execution():
            execute(appointment)
            appointment.last_execution = now  # save actual execution
            if appointment.type == ONCE:  # execute it just once
                appointments.remove(appointment)

    save_appointments(appointments)


# executes an appointment
def execute(appointment):
    bot.remind(appointment)


# saves the appointments with a consistent name
def save_appointments(appointments):
    old_appointments = load_appointments()
    with open(old_appointments_path, 'wb') as out:  # Overwrites any existing file.
        pickle.dump(old_appointments, out)
    with open(appointments_path, 'wb') as out:  # Overwrites any existing file.
        pickle.dump(appointments, out)


# load the appointments list
def load_appointments():
    try:
        with open(appointments_path, 'rb') as inp:
            return pickle.load(inp)
    except FileNotFoundError:
        return []
