#!/usr/bin/env python3
#
# A library that allows to create an inline calendar keyboard.
# grcanosa https://github.com/grcanosa
#
# Modified by therealpeterpython github.com/therealpeterpython/remembot (2019)
"""
Base methods for calendar keyboard creation and processing.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardRemove
import datetime
import calendar
from remembot.common.constants import *


def create_callback_data(action, year, month, day):
    """ Create the callback data associated to each button"""
    return SEPARATOR.join([action, str(year), str(month), str(day)])


def separate_callback_data(data):
    """ Separate the callback data"""
    return data.split(SEPARATOR)


def create_calendar(year=None, month=None):
    """
    Create an inline keyboard with the provided year and month
    :param int year: Year to use in the calendar, if None the current year is used.
    :param int month: Month to use in the calendar, if None the current month is used.
    :return: Returns the InlineKeyboardMarkup object with the calendar.
    """

    now = datetime.datetime.now()
    if year == None: year = now.year
    if month == None: month = now.month
    keyboard = []

    # First row - Month and Year
    row = []
    row.append(InlineKeyboardButton(calendar.month_name[month] + " " + str(year), callback_data=IGNORE))
    keyboard.append(row)

    # Second row - Week Days
    row = []
    for day in ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]:
        row.append(InlineKeyboardButton(day, callback_data=IGNORE))
    keyboard.append(row)

    my_calendar = calendar.monthcalendar(year, month)
    for week in my_calendar:
        row = []
        for day in week:
            if (day == 0):
                row.append(InlineKeyboardButton(" ", callback_data=IGNORE))
            else:
                row.append(InlineKeyboardButton(str(day), callback_data=create_callback_data("DAY", year, month, day)))
        keyboard.append(row)

    # Last row - Buttons
    row = []
    row.append(InlineKeyboardButton("<", callback_data=create_callback_data("PREV-MONTH", year, month, day)))
    row.append(InlineKeyboardButton(" ", callback_data=IGNORE))
    row.append(InlineKeyboardButton(">", callback_data=create_callback_data("NEXT-MONTH", year, month, day)))
    keyboard.append(row)
    keyboard.append([InlineKeyboardButton("<  Back", callback_data=BACK)])

    return InlineKeyboardMarkup(keyboard)


def process_calendar_selection(bot, update):
    """
    Process the callback_query for the calendar. This method generates a new calendar if
    forward or backward is pressed. This method should be called inside a CallbackQueryHandler.
    :param telegram.Bot bot: The bot, as provided by the CallbackQueryHandler
    :param telegram.Update update: The update, as provided by the CallbackQueryHandler
    :return: Returns a tuple (String, datetime.datetime), indicating which action is chosen
                and returning the date if so.
    """

    ret_data = ("", None)
    query = update.callback_query
    (action, year, month, day) = separate_callback_data(query.data)
    curr = datetime.datetime(int(year), int(month), 1)
    if action == IGNORE:
        raise Exception("Unreachable IGNORE in telegramcalendar")
        bot.answer_callback_query(callback_query_id=query.id)
    elif action == "DAY":
        ret_data = "DAY", datetime.datetime(int(year), int(month), int(day))
    elif action == "PREV-MONTH":
        pre = curr - datetime.timedelta(days=1)
        bot.edit_message_text(text=query.message.text,
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              reply_markup=create_calendar(int(pre.year), int(pre.month)))
    elif action == "NEXT-MONTH":
        ne = curr + datetime.timedelta(days=31)
        bot.edit_message_text(text=query.message.text,
                              chat_id=query.message.chat_id,
                              message_id=query.message.message_id,
                              reply_markup=create_calendar(int(ne.year), int(ne.month)))
    elif action == "BACK":
        raise Exception("Unreachable BACK in telegramcalendar")
        ret_data = "BACK", None
    else:
        bot.answer_callback_query(callback_query_id=query.id, text="Something went wrong!")
        # UNKNOWN
    return ret_data


def create_weekdays():
    """
    Creates an inline keyboard for the seven weekdays.

    :return: Returns the InlineKeyboardMarkup object
    """

    row = list()
    keyboard = list()

    keyboard.append([InlineKeyboardButton("Weekdays", callback_data=IGNORE)])

    for day in WEEKDAYS_ABBR:
        row.append(InlineKeyboardButton(day, callback_data=day))
    keyboard.append(row)

    keyboard.append([InlineKeyboardButton("<  Back", callback_data=BACK)])
    return InlineKeyboardMarkup(keyboard)


'''
not needed
def process_weekdays_selection(update):
    """
    Process the callback_query for the weekdays.
    :param telegram.Update update: The update, as provided by the CallbackQueryHandler
    :return: Returns the weekday if one was chosen.
    """

    data = update.callback_query.data
    if data in WEEKDAYS_ABBR:
        return data
'''



