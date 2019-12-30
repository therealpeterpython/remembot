"""
todo
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from interface.constants import *


def create_callback_data(action, time):
    """ Create the callback data associated to each button"""
    return SEPARATOR.join([action, str(time)])


def separate_callback_data(data):
    """ Separate the callback data"""
    return data.split(SEPARATOR)


def create_clock():
    hour_columns = 4
    minute_blocks = [0, 15, 30, 45]

    data_ignore = create_callback_data("IGNORE", 0)
    keyboard = list()

    # --- First row - Hours string --- #
    keyboard.append([InlineKeyboardButton("Hours", callback_data=data_ignore)])

    # --- Next rows - All hours --- #
    row = list()
    for i in range(HOURS//hour_columns):
        keyboard.append([InlineKeyboardButton(str(j), callback_data=create_callback_data("HOUR", j))
                         for j in range(i*hour_columns, (i+1)*hour_columns)])

    # --- Next row - Minutes string --- #
    keyboard.append([InlineKeyboardButton("Minutes", callback_data=data_ignore)])

    # --- Next rows - Minute blocks --- #
    keyboard.append([InlineKeyboardButton(str(i), callback_data=create_callback_data("MINUTE", i))
                     for i in minute_blocks])

    # --- Last row - Back --- #
    keyboard.append([InlineKeyboardButton("< Back to calendar", callback_data=create_callback_data("BACK", 0), switch_inline_query="aaaaa")])

    return InlineKeyboardMarkup(keyboard)


def process_clock_selections(update, context):
    """
    todo

    :param update:
    :param context:
    :return:
    """
    mode, value = separate_callback_data(update.callback_query.data)
    return mode, int(value)