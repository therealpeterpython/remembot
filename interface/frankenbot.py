#!/usr/bin/env python
# -*- coding: utf-8 -*-
# This program is dedicated to the public domain under the CC0 license.

"""
todo texte
First, a few handler functions are defined. Then, those functions are passed to
the Dispatcher and registered at their respective places.
Then, the bot is started and runs until we press Ctrl-C on the command line.
Usage:
Basic inline bot example. Applies different text transformations.
Press Ctrl-C on the command line or send a signal to the process to stop the
bot.
"""
import logging
from uuid import uuid4
import datetime
import calendar

from telegram import InlineKeyboardMarkup, InlineKeyboardButton, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Updater, InlineQueryHandler, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

from interface.config import *
from interface.constants import *
import interface.telegramcalendar as telegramcalendar
import interface.telegramclock as telegramclock

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


class AppointmentCreator:
    _instances = dict()

    def __str__(self):
        print("- __str__")
        attrs = vars(self)
        return ', '.join("%s: %s" % item for item in attrs.items())

    def __init__(self, chat_id, message_id, bot):
        print("- __init__")
        self.chat_id = chat_id
        self.message_id = message_id
        self.bot = bot

        self.stage = TYPE
        self.type = None
        self.count = None
        self.weekday = None
        self.date = None
        self.time = datetime.time()
        self.set_hour = False
        self.set_minute = False
        self.description = None
        self.command = ""
        self._instances[chat_id] = self

    def create_command(self):
        print("- create_command")
        # todo "format of the switch to inline argument(;; = 2xSEPARATOR):
        #  A;;ONCE;;13.09.2019;;14:45;;My text
        #  A;;EVERY_N_DAYS;;14;;13.09.2019;;14:45;;My text
        #  A;;NTH_WEEKDAY;;2;;<MONDAY>;;14:45;;My text
        #  A;;NUM;;13.09.2019;;14:45;;My text

        if self.type == ONCE:
            command = DELIMITER.join([BLOCK_START, ONCE, self.date.strftime(DATE_FORMAT), self.time.strftime(TIME_FORMAT), self.description])
        elif self.type == EVERY_N_DAYS:
            command = DELIMITER.join([BLOCK_START, EVERY_N_DAYS, self.count, self.date.strftime(DATE_FORMAT), self.time.strftime(TIME_FORMAT), self.description])
        elif self.type == NTH_WEEKDAY:
            command = DELIMITER.join([BLOCK_START, NTH_WEEKDAY, self.count, self.weekday, self.time.strftime(TIME_FORMAT), self.description])
        elif self.type == NUM:
            command = DELIMITER.join([BLOCK_START, NUM, self.date.strftime(DATE_FORMAT), self.time.strftime(TIME_FORMAT), self.description])
        else:
            raise ValueError("'{}' is not a valid type!".format(self.type))

        return command

    def next_command(self):
        print("- next_command")
        self.command += self.create_command() + DELIMITER
        self.reset()

    def reset(self):
        print("- reset")
        self.stage = TYPE
        self.type = None
        self.date = None
        self.time = datetime.time()
        self.set_hour = False
        self.set_minute = False
        self.description = None

    def finalize(self):
        print("- finalize")
        # todo self.datetime in self.date und self.time aufsplitten
        # todo die verschiedenen fälle unterschieden und dann vernünftig die erstellten Termine anzeigen
        # todo "format of the switch to inline argument(;; = 2xSEPARATOR):
        #  A;;ONCE;;13.09.2019;;14:45;;My text
        #  A;;EVERY_N_DAYS;;14;;13.09.2019;;14:45;;My text
        #  A;;NTH_WEEKDAY;;2;;<MONDAY>;;14:45;;My text
        #  A;;NUM;;13.09.2019;;14:45;;My text
        self.command += self.create_command()
        keyboard = [[InlineKeyboardButton("Create & Back >", switch_inline_query=self.command)]]
        appointment_blocks = process_appointment_str(self.command)
        text = ""
        for block in appointment_blocks:
            if block[1] == ONCE:
                text += "= Once at {} {}: \"{}\"\n".format(*block[2:])
            elif block[1] == EVERY_N_DAYS:
                text += "= Every {} days at {}, starting with the {}: {}\n".format(block[2], block[4], block[3], block[5])
            elif block[1] == NTH_WEEKDAY:
                text += "= Every {}. {} at {}: {}\n".format(block[2], calendar.day_name[int(block[3])], block[4], block[5])
            elif block[1] == NUM:
                text += "= Every month at {} {}: {}\n".format(*block[2:])
            else:
                raise ValueError("'{}' is not a valid type!".format(block[1]))

        self.bot.edit_message_text(text=text,
                                   chat_id=self.chat_id,
                                   message_id=self.message_id,
                                   reply_markup=InlineKeyboardMarkup(keyboard))
        self.destroy()

    def destroy(self):
        print("- destroy")
        del self.__class__._instances[self.chat_id]

    @classmethod
    def getinstance(cls, key):
        print("- getinstance")
        d = cls._instances
        return d[key] if key in d else None


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    """Send a message when the command /start is issued."""
    print("-- start")
    chat_id = update.message.chat.id
    ac = AppointmentCreator.getinstance(chat_id)
    if ac:
        send_expired_message(ac.message_id, ac.chat_id, context.bot)
        ac.destroy()

    context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
    message = appointment_type(update, context)
    AppointmentCreator(chat_id=update.message.chat.id, message_id=message.message_id, bot=context.bot)


def appointment_type(update, context, text="Please select a type: "):
    print("-- appointment_type")
    keyboard = [[InlineKeyboardButton("Once", callback_data=ONCE), InlineKeyboardButton("N-Days distance", callback_data=EVERY_N_DAYS)],
                [InlineKeyboardButton("NTH-Weekday", callback_data=NTH_WEEKDAY), InlineKeyboardButton("Num", callback_data=NUM)]]
    markup = InlineKeyboardMarkup(keyboard)

    if update.message:  # if we got here by a new message
        msg = update.message.reply_text(text, reply_markup=markup)
    elif update.callback_query:  # if we got here by a back button or as another appointment
        query = update.callback_query
        msg = context.bot.edit_message_text(text=text,
                                            chat_id=query.message.chat_id,
                                            message_id=query.message.message_id,
                                            reply_markup=markup)
    return msg


def calendar(update, context, text="Please select a date: "):
    print("-- calendar")
    query = update.callback_query
    context.bot.edit_message_text(text=text,
                                  chat_id=query.message.chat_id,
                                  message_id=query.message.message_id,
                                  reply_markup=telegramcalendar.create_calendar())


def clock(update, context, text="Please select a time: "):
    print("-- clock")
    query = update.callback_query
    context.bot.edit_message_text(text=text,
                                  chat_id=query.message.chat_id,
                                  message_id=query.message.message_id,
                                  reply_markup=telegramclock.create_clock())


def count(update, context, text="Please type in the number of days: "):
    print("-- count")  # todo


def weekday(update, context, text="Please select the weekday: "):
    print("-- weekday")
    query = update.callback_query
    context.bot.edit_message_text(text=text,
                                  chat_id=query.message.chat_id,
                                  message_id=query.message.message_id,
                                  reply_markup=telegramcalendar.create_weekdays())


def description(update, context, text="Please type in your description: "):
    print("-- description")
    query = update.callback_query
    context.bot.edit_message_text(text=text,
                                  chat_id=query.message.chat_id,
                                  message_id=query.message.message_id)


def description_handler(update, context):
    print("-- description_handler")
    chat_id = update.message.chat.id
    ac = AppointmentCreator.getinstance(chat_id)
    if ac and ac.stage == DESCRIPTION:
        ac.description = sanitize_text(update.message.text)
        ac.stage = next_stage(ac.type, ac.stage)
        context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
        STAGE_FUNCTIONS[ac.stage](update, context, **get_parameters(ac.type, ac.stage))  # call the stage function


def next_appointment(update, context):
    print("-- next_appointment")
    keyboard = [[InlineKeyboardButton("Yes", callback_data=YES),
                 InlineKeyboardButton("No", callback_data=NO)]]
    chat_id = update.message.chat.id
    ac = AppointmentCreator.getinstance(chat_id)  # there is no callback_queue to get the right message id
    if ac:  # there should(!) be no case where there are no ac when this method is called
        context.bot.edit_message_text(text="Data saved. Create another appointment?",
                                      chat_id=ac.chat_id,
                                      message_id=ac.message_id,
                                      reply_markup=InlineKeyboardMarkup(keyboard))


def process_custom_keyboard_reply(update, context):
    """
    Processes the replys of the custom keyboards. Switches,
    depending on the received data, to the next keyboard.

    :param update: Standard telegram update
    :param context: Standard telegram context
    :return: None
    """
    print("-- process_custom_keyboard_reply")
    print("d: ", update.callback_query.data)
    chat_id = update.callback_query.message.chat.id
    message_id = update.callback_query.message.message_id
    data = update.callback_query.data

    ac = AppointmentCreator.getinstance(chat_id)
    if ac and ac.message_id == message_id:  # we have an AppointmentCreator object for this chat and this message
        if data == BACK:  # go back to the previous stage
            ac.set_hour = False
            ac.set_minute = False
            ac.stage = previous_stage(ac.type, ac.stage)
            STAGE_FUNCTIONS[ac.stage](update, context, **get_parameters(ac.type, ac.stage))  # call the stage function
            return
        elif data == IGNORE:  # ignore the pressed button
            return

        if ac.stage == TYPE:
            ac.type = data
        elif ac.stage == COUNT:
            ac.count = data
        elif ac.stage == DATE:
            mode, date = telegramcalendar.process_calendar_selection(context.bot, update)
            if mode != "DAY":
                return  # can't move on to the next stage
            ac.date = date
        elif ac.stage == WEEKDAY:
            ac.weekday = data
        elif ac.stage == TIME:
            mode, value = telegramclock.process_clock_selections(update, context)
            if mode == "HOUR":
                ac.time = ac.time.replace(hour=value)
                ac.set_hour = True
            elif mode == "MINUTE":
                ac.time = ac.time.replace(minute=value)
                ac.set_minute = True

            if not (ac.set_minute and ac.set_hour):
                return  # can't move on to the next stage
        elif ac.stage == NEXT:
            if data == YES:
                ac.next_command()
                appointment_type(update, context)
            elif data == NO:
                ac.finalize()
            return  # we move on 'by hand'

        # If we didn't encounter a return we can move on to the next stage
        ac.stage = next_stage(ac.type, ac.stage)
        STAGE_FUNCTIONS[ac.stage](update, context, **get_parameters(ac.type, ac.stage))  # call the stage function

    else:  # we don't have an AppointmentCreator object
        send_expired_message(message_id, chat_id, context.bot)


def switch_to_pm(update, context):
    """
    The InlineQueryHandler for the bot. It shows the switch_pm button
    and the create appointment buttons for the prepared appointments.
    todo
    :param update:
    :param context:
    :return:
    """
    print("-- switch_to_pm")
    appointment_blocks = process_appointment_str(update.inline_query.query)
    r = [InlineQueryResultArticle(id=uuid4(),
                                  title="None",
                                  input_message_content=InputTextMessageContent("/add@{} {}".format(context.bot.username, update.inline_query.query)))]
    if not appointment_blocks:
        r = []
    elif len(appointment_blocks) > 1:
        r[0].title = "Create appointments"
    else:
        r[0].title = "Create appointment"

    update.inline_query.answer(r, switch_pm_text="Create new date for this group!", switch_pm_parameter="unused_but_necessary_parameter")


def add(update, context):
    print("-- add")
    # todo wenn keine args mit übergeben wurden direkt an /start weiterleiten
    appointment_str = " ".join(context.args)
    appointment_blocks = process_appointment_str(appointment_str)
    print(appointment_blocks)

    for block in appointment_blocks:
        # todo create appointment for block
        # todo write to chat.id which appointment was added (better: write a single message at the end)
        pass


# todo
def help(update, context):
    """Send a message when the command /help is issued."""
    print("-- help")
    update.message.reply_text('Help!')


def cancel(update, context):
    print("-- cancel")
    chat_id = update.message.chat.id
    ac = AppointmentCreator.getinstance(chat_id)
    context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
    if ac:
        context.bot.edit_message_text(text="Creation canceled!",
                                      chat_id=ac.chat_id,
                                      message_id=ac.message_id)
        update.message.reply_text("Canceled creation - create a new appointment with /start or get help with /help")
        ac.destroy()


def send_expired_message(message_id, chat_id, bot):
    print("-- send_expired_message")
    bot.edit_message_text(text="*Session expired* \nPlease try again with /start or get some support with /help",
                          chat_id=chat_id,
                          message_id=message_id,
                          parse_mode="Markdown")


# todo takes /delete command and returns a list of appointments as customreplykeyboard. Click one of them returns a yes or
# todo no crk and then deletes the appointment or cancels
def delete_handler(update, context):
    print("-- delete_handler")  # todo


def error(update, context):
    """Log Errors caused by Updates."""
    print("-- error")
    logger.warning('Error "%s" caused by update "%s"', context.error, update)


def sanitize_text(text):
    """
    DELIMITER is used as delimiter for the final inline command and BLOCK_START is used to split the appointment block
    so they may not appear in the appointment description.

    :param text: String to sanitize
    :return: Sanitized string unequal BLOCK_START and without DELIMITER
    """
    print("-- sanitize_text")
    while True:
        if DELIMITER in text:
            text = text.replace(DELIMITER, SEPARATOR)
        elif text == BLOCK_START:
            text += " "
        else:
            break
    return text


# splits the appointment string in blocks for the (maybe) multiple appointments
# return none if its not a valid appointments string
def process_appointment_str(app_str):
    # todo die appointment typen abfangen und entsprechend behandeln
    print("-- process_appointment_str")
    parameter = app_str.split(DELIMITER)
    index = [i for i, p in enumerate(parameter) if p == BLOCK_START]
    index.append(len(parameter))
    parameter_blocks = [parameter[index[i]: index[i+1]] for i in range(len(index)-1)]
    for block in parameter_blocks:  # check that each block has the right length (from this we conclude that the block is correct)
        if len(block) not in [5, 6]:
            return

    print("parameter_blocks: ", parameter_blocks)
    return parameter_blocks


def next_stage(type, stage):
    return ORDERS[type][ORDERS[type].index(stage) + 1]


def previous_stage(type, stage):
    return ORDERS[type][ORDERS[type].index(stage) - 1]


def get_parameters(type, stage):
    return PARAMETERS[type].get(stage, {})


def main():
    print("-- main")
    # Get token #
    with open(token_path, "r") as token_file:
        token = token_file.read()

    # Create the Updater and pass it your bot's token #
    updater = Updater(token, use_context=True)

    # Get the dispatcher to register handlers #
    dp = updater.dispatcher

    # on different commands - answer in Telegram #
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("add", add))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("cancel", cancel))
    dp.add_handler(CallbackQueryHandler(process_custom_keyboard_reply))

    dp.add_handler(MessageHandler(Filters.text, description_handler))

    dp.add_handler(InlineQueryHandler(switch_to_pm))

    # log all errors #
    dp.add_error_handler(error)

    # Start the Bot #
    updater.start_polling()

    # Block until the user presses Ctrl-C or the process receives SIGINT, SIGTERM or SIGABRT #
    updater.idle()


if __name__ == '__main__':
    # Mapping of the stages to their functions #
    STAGE_FUNCTIONS = {TYPE: appointment_type, DATE: calendar, TIME: clock, COUNT: count, WEEKDAY: weekday,
                       DESCRIPTION: description, NEXT: next_appointment}  # :'<
    # if i made a mistake and don't have STAGE_FUNCTIONS and the stages synced
    if len(STAGE_FUNCTIONS) != NUM_STAGES:
        raise Exception("Wrong number of stages or functions!")

    main()
