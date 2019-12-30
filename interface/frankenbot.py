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

from telegram import InlineKeyboardMarkup, InlineKeyboardButton, InlineQueryResultArticle, InputTextMessageContent
from telegram.ext import Updater, InlineQueryHandler, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

from interface.config import *
from interface.constants import *
import telegramcalendar
import telegramclock

# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO)

logger = logging.getLogger(__name__)


class AppointmentCreator:
    _instances = dict()

    def __str__(self):
        attrs = vars(self)
        return ', '.join("%s: %s" % item for item in attrs.items())

    def __init__(self, chat_id, message_id, bot, from_chat_id=None, from_chat_name=None):
        self.chat_id = chat_id
        self.message_id = message_id
        self.bot = bot

        self.stage = TYPE
        self.type = None
        self.datetime = None
        self.set_hour = False
        self.set_minute = False
        self.description = None
        self.command = ""
        self._instances[chat_id] = self

    def create_command(self):
        # todo "format of the switch to inline argument(;; = 2xSEPARATOR): A;;ONCE;;13.09.2019-14:45;;My text;;A;;NTHDAY;;3x0;;14:45;;My text;;A;;NUM;;13;;14:45;;My text"
        return DELIMITER.join([BLOCK_START, self.type, self.datetime.strftime(TIME_FORMAT), self.description])

    def next_command(self):
        self.command += self.create_command() + DELIMITER
        self.reset()

    def reset(self):
        self.stage = TYPE
        self.type = None
        self.datetime = None
        self.set_hour = False
        self.set_minute = False
        self.description = None

    def finalize(self):
        self.command += self.create_command()
        keyboard = [[InlineKeyboardButton("Create & Back >", switch_inline_query=self.command)]]

        if self.command.count(DELIMITER) > 3:  # more than one appointment
            text = self.command  # todo schöner machen
        else:  # just one appointment
            text = "{} {}: {}".format(self.type.capitalize(), self.datetime.strftime(TIME_FORMAT), self.description)

        self.bot.edit_message_text(text=text,
                                   chat_id=self.chat_id,
                                   message_id=self.message_id,
                                   reply_markup=InlineKeyboardMarkup(keyboard))
        self.destroy()

    def destroy(self):
        del self.__class__._instances[self.chat_id]

    @classmethod
    def getinstance(cls, key):
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
    elif update.callback_query:  # if we got here by a back button
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


def count(update, context, text="TODO"):
    print("-- count")  # todo


def weekday(update, context, text="TODO"):
    # todo use telegramcalendar.create_weekdays()
    print("-- weekday")  # todo


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
        ac.stage = ORDERS[ac.type][ORDERS[ac.type].index(ac.stage) + 1]
        context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
        ORDERS_FUNC[ac.stage](update, context, **PARAMETERS[ac.type].get(ac.stage, {}))


def next_appointment(update, context):
    keyboard = [[InlineKeyboardButton("Yes", callback_data=YES),
                 InlineKeyboardButton("No", callback_data=NO)]]
    chat_id = update.message.chat.id
    ac = AppointmentCreator.getinstance(chat_id)
    if ac:
        ac.description = sanitize_text(update.message.text)
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
    if ac and ac.message_id == message_id:
        print("s: ", ac.stage)
        if ac.stage == TYPE:
            ac.type = data
            ac.stage = ORDERS[ac.type][ORDERS[ac.type].index(ac.stage) + 1]
            ORDERS_FUNC[ac.stage](update, context, **PARAMETERS[ac.type].get(ac.stage, {}))
        elif ac.stage == DATE:
            mode, date = telegramcalendar.process_calendar_selection(context.bot, update)
            if mode == "BACK":  # todo back, day, hour and minute mit konstanten ersetzen
                ac.stage = ORDERS[ac.type][ORDERS[ac.type].index(ac.stage) - 1]
            elif mode == "DAY":
                ac.datetime = date
                ac.stage = ORDERS[ac.type][ORDERS[ac.type].index(ac.stage) + 1]
            ORDERS_FUNC[ac.stage](update, context, **PARAMETERS[ac.type].get(ac.stage, {}))

        elif ac.stage == TIME:
            mode, value = telegramclock.process_clock_selections(update, context)
            if mode == "BACK":
                ac.stage = ORDERS[ac.type][ORDERS[ac.type].index(ac.stage) - 1]
                ORDERS_FUNC[ac.stage](update, context, **PARAMETERS[ac.type].get(ac.stage, {}))
                return
            elif mode == "HOUR":
                ac.datetime = ac.datetime.replace(hour=value)
                ac.set_hour = True
            elif mode == "MINUTE":
                ac.datetime = ac.datetime.replace(minute=value)
                ac.set_minute = True

            if ac.set_minute and ac.set_hour:
                ac.stage = ORDERS[ac.type][ORDERS[ac.type].index(ac.stage) + 1]
                ORDERS_FUNC[ac.stage](update, context, **PARAMETERS[ac.type].get(ac.stage, {}))
        elif ac.stage == NEXT:
            if data == YES:
                ac.next_command()
                appointment_type(update, context)
            elif data == NO:
                ac.finalize()
    else:
        send_expired_message(message_id, chat_id, context.bot)


def switch_to_pm(update, context):
    """
    The InlineQueryHandler for the bot. It shows the switch_pm button
    and the create appointment buttons for the prepared appointments.

    :param update:
    :param context:
    :return:
    """
    # todo
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
        if appointment_blocks[0][1] == ONCE:
            print("once")
            title = "{}\n{}".format(appointment_blocks[0][2], appointment_blocks[0][3])
        elif appointment_blocks[0][1] == EVERY_N_DAYS:
            title = "TODO"
        elif appointment_blocks[0][1] == NTH_WEEKDAY:
            title = "TODO"
        elif appointment_blocks[0][1] == NUM:
            title = "TODO"
        r[0].title = title

    update.inline_query.answer(r, switch_pm_text="Create new date for this group!", switch_pm_parameter="unused_but_necessary_parameter")


def add(update, context):
    print("-- add")
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
    update.message.reply_text('Help!')


def cancel(update, context):
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
    bot.edit_message_text(text="*Session expired* \nPlease try again with /start or get some support with /help",
                          chat_id=chat_id,
                          message_id=message_id,
                          parse_mode="Markdown")


# todo takes /delete command and returns a list of appointments as customreplykeyboard. Click one of them returns a yes or
# todo no crk and then deletes the appointment or cancels
def delete_handler(update, context):
    pass  # todo


def error(update, context):
    """Log Errors caused by Updates."""
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def sanitize_text(text):
    """
    2*SEPARATOR is used as delimiter for the final inline command so it may not
    be in the appointment description.

    :param text: String to sanitize
    :return: Sanitized string
    """
    while True:
        if DELIMITER in text:
            text = text.replace(DELIMITER, SEPARATOR)
        else:
            break
    return text


# splits the appointment string in blocks for the (maybe) multiple appointments and removes the BLOCK_START symbol
# return none if its not a valid appointments string
def process_appointment_str(app_str):
    print("-- process_appointment_str")
    parameter = app_str.split(DELIMITER)
    parameter_blocks = [parameter[i:i+4] for i in range(0, len(parameter), 4)]
    ret = parameter_blocks

    if len(parameter) % 4 != 0 or not app_str.strip():  # todo magic number 4 (ist 4 mit den anderen datentypen noch korrekt??)
        ret = None
    else:
        for block in parameter_blocks:  # check if every block has the right start token (hence we conclude the block is correct)
            if block[0] != BLOCK_START:
                ret = None

    return ret


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
    ORDERS_FUNC = {TYPE: appointment_type, DATE: calendar, TIME: clock, COUNT: count, WEEKDAY: weekday,
                   DESCRIPTION: description, NEXT: next_appointment}  # :'<
    # if i made a mistake and don't have ORDERS_FUNC and the stages synced
    if len(ORDERS_FUNC) != NUM_STAGES:
        raise Exception("Wrong number of stages or functions!")
    main()
