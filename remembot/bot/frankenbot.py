#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
This is the version v2.0 of the rememgram bot written by
therealpeterpython (github.com/therealpeterpython).
You can find the bot and my other work at
github.com/therealpeterpython/remembot.
Feel free to submit issues, requests and feedback via github.

This program is licensed under CC BY-SA 4.0 by therealpeterpython.
"""
import logging
from functools import reduce
from uuid import uuid4
import datetime
import calendar as cal

from telegram import InlineKeyboardMarkup, InlineKeyboardButton, InlineQueryResultArticle, InputTextMessageContent, TelegramError
from telegram.ext import Updater, InlineQueryHandler, CommandHandler, CallbackQueryHandler, MessageHandler, Filters

from remembot.rememgram import rememgram
from remembot.common.config import *
from remembot.common.constants import *
from remembot.common.helper import process_appointment_str
from remembot.bot import telegramcalendar
from remembot.bot import telegramclock


# Enable logging
logging.basicConfig(format='\n%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO, filename=log_path, filemode='a')

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())

# todo verschiedenen nutzer die gleizeitig mit dem bot arbeiten testen
# todo den ausgewählten type mit anzeigen in den vrschiedenen stages

class AppointmentCreator:
    _instances = dict()

    def __str__(self):
        attrs = vars(self)
        return ', '.join("%s: %s" % item for item in attrs.items())

    def __init__(self, chat_id, message_id, bot):
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
        """The 4 different styles for appointment strings (;; = DELIMITER):
        A;;ONCE;;13.09.2019;;14:45;;My text
        A;;EVERY_N_DAYS;;14;;13.09.2019;;14:45;;My text
        A;;NTH_WEEKDAY;;2;;MONDAY;;14:45;;My text
        A;;NUM;;13.09.2019;;14:45;;My text
        """
        print("- create_command")

        if self.type == ONCE:
            command = DELIMITER.join([BLOCK_START, ONCE, self.date.strftime(DATE_FORMAT), self.time.strftime(TIME_FORMAT), self.description])
        elif self.type == EVERY_N_DAYS:
            command = DELIMITER.join([BLOCK_START, EVERY_N_DAYS, str(self.count), self.date.strftime(DATE_FORMAT), self.time.strftime(TIME_FORMAT), self.description])
        elif self.type == NTH_WEEKDAY:
            command = DELIMITER.join([BLOCK_START, NTH_WEEKDAY, str(self.count), str(self.weekday), self.time.strftime(TIME_FORMAT), self.description])
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
        self.command += self.create_command()
        text = self.pprint()
        keyboard = [[InlineKeyboardButton("Create & Switch >", switch_inline_query=self.command)],
                    [InlineKeyboardButton("Create here", callback_data="create_here" + DELIMITER + self.command)]]  # todo "create here" button testen!

        self.bot.edit_message_text(text=text,
                                   chat_id=self.chat_id,
                                   message_id=self.message_id,
                                   reply_markup=InlineKeyboardMarkup(keyboard))
        self.destroy()

    def pprint(self):
        appointment_blocks = process_appointment_str(self.command)
        text = ""
        for block in appointment_blocks:
            if block[1] == ONCE:
                day_name = cal.day_abbr[datetime.datetime.strptime(block[2], DATE_FORMAT).weekday()]
                text += "{} Once at {}. {} {}: \"{}\"\n".format(BULLET, day_name, block[2], block[3], block[4])
            elif block[1] == EVERY_N_DAYS:
                day_name = cal.day_abbr[datetime.datetime.strptime(block[3], DATE_FORMAT).weekday()]
                text += "{} Every {} days at {}, starting on the {}. {}: {}\n".format(BULLET, block[2], block[4], day_name, block[3], block[5])
            elif block[1] == NTH_WEEKDAY:
                text += "{} Every {}. {} at {}: {}\n".format(BULLET, block[2], cal.day_name[int(block[3])], block[4], block[5])
            elif block[1] == NUM:
                text += "{} Every month at {} {}: {}\n".format(BULLET, block[2], block[3], block[4])
            else:
                raise ValueError("'{}' is not a valid type!".format(block[1]))
        return text


    def destroy(self):
        print("- destroy")
        del self.__class__._instances[self.chat_id]

    @classmethod
    def getinstance(cls, chat_id):
        d = cls._instances
        return d[chat_id] if chat_id in d else None


class Eraser:
    _instances = dict()

    def __str__(self):
        attrs = vars(self)
        return ', '.join("%s: %s" % item for item in attrs.items())

    def __init__(self, chat_id, message_id):
        self.chat_id = chat_id
        self.message_id = message_id
        self.deletion_list = []
        self._instances[chat_id] = self

    def destroy(self):
        del self.__class__._instances[self.chat_id]

    @classmethod
    def getinstance(cls, chat_id):
        d = cls._instances
        return d[chat_id] if chat_id in d else None


# Define a few command handlers. These usually take the two arguments update and
# context. Error handlers also receive the raised TelegramError object in error.
def start(update, context):
    """Send a message when the command /start is issued."""
    print("-- start")
    if update.message:  # text message
        chat_id = update.message.chat.id
    else:  # inlinekeyboard
        chat_id = update.callback_query.message.chat_id

    ac = AppointmentCreator.getinstance(chat_id)
    if ac:
        send_expired_message(ac.message_id, ac.chat_id, context.bot)
        ac.destroy()

    #context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
    message = appointment_type(update, context)
    AppointmentCreator(chat_id=update.message.chat.id, message_id=message.message_id, bot=context.bot)


def appointment_type(update, context, text="<b><u>Instructions</u></b>\nPlease select a type: "):
    print("-- appointment_type")
    # add the introduction text #
    with open(type_path, "r") as fp:
        introduction = fp.read()
        text = introduction + text

    # create keyboard markup #
    keyboard = [[InlineKeyboardButton("Unique", callback_data=ONCE), InlineKeyboardButton("Fixed period", callback_data=EVERY_N_DAYS)],
                [InlineKeyboardButton("Weekday", callback_data=NTH_WEEKDAY), InlineKeyboardButton("Day", callback_data=NUM)]]
    markup = InlineKeyboardMarkup(keyboard)

    # write message #
    if update.message:  # if we got here by a new message
        msg = context.bot.send_message(chat_id=update.message.chat.id, text=text, reply_markup=markup, parse_mode="HTML")
    elif update.callback_query:  # if we got here by a back button or as another appointment
        query = update.callback_query
        msg = context.bot.edit_message_text(chat_id=query.message.chat_id, text=text,
                                            message_id=query.message.message_id, reply_markup=markup, parse_mode="HTML")
    return msg


def calendar(update, context, text="<b><u>Instructions</u></b>\nPlease select a date: "):
    print("-- calendar")
    if update.message:  # text message
        chat_id = update.message.chat.id
    else:  # inlinekeyboard
        chat_id = update.callback_query.message.chat_id
    ac = AppointmentCreator.getinstance(chat_id)  # there is not necessary a callback_queue to get the right message id from
    if ac:  # there should(!) be no case where there are no ac when this method is called
        context.bot.edit_message_text(text=text,
                                      chat_id=ac.chat_id,
                                      message_id=ac.message_id,
                                      reply_markup=telegramcalendar.create_calendar(),
                                      parse_mode="HTML")


# todo replace all queries in this methods like in calendar with ac objects
def clock(update, context, text="<b><u>Instructions</u></b>\nPlease select a time: "):
    print("-- clock")
    query = update.callback_query
    context.bot.edit_message_text(text=text,
                                  chat_id=query.message.chat_id,
                                  message_id=query.message.message_id,
                                  reply_markup=telegramclock.create_clock(),
                                  parse_mode="HTML")


def count(update, context, text="<b><u>Instructions</u></b>\nPlease type in the number of days: "):
    print("-- count")
    query = update.callback_query
    context.bot.edit_message_text(text=text,
                                  chat_id=query.message.chat_id,
                                  message_id=query.message.message_id,
                                  parse_mode="HTML")


def weekday(update, context, text="<b><u>Instructions</u></b>\nPlease select the weekday: "):
    print("-- weekday")
    if update.message:  # text message
        chat_id = update.message.chat.id
    else:  # inlinekeyboard
        chat_id = update.callback_query.message.chat_id

    ac = AppointmentCreator.getinstance(chat_id)  # there is no callback_queue to get the right message id from
    if ac:  # there should(!) be no case where there are no ac when this method is called
        context.bot.edit_message_text(text=text,
                                      chat_id=ac.chat_id,
                                      message_id=ac.message_id,
                                      reply_markup=telegramcalendar.create_weekdays(),
                                      parse_mode="HTML")


def description(update, context, text="<b><u>Instructions</u></b>\nPlease type in your description: "):
    print("-- description")
    query = update.callback_query
    context.bot.edit_message_text(text=text,
                                  chat_id=query.message.chat_id,
                                  message_id=query.message.message_id,
                                  parse_mode="HTML")


def text_handler(update, context):
    print("-- text_handler")
    if update.message:  # text message
        chat_id = update.message.chat.id
    else:  # inlinekeyboard
        chat_id = update.callback_query.message.chat_id
    ac = AppointmentCreator.getinstance(chat_id)
    if ac:
        if ac.stage == DESCRIPTION:
            ac.description = sanitize_text(update.message.text)
        elif ac.stage == COUNT:
            ac.count = int(update.message.text.strip())
        else:
            return
        ac.stage = next_stage(ac.type, ac.stage)
        #context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)
        STAGE_FUNCTIONS[ac.stage](update, context, **get_parameters(ac.type, ac.stage))  # call the stage function


def next_appointment(update, context):
    print("-- next_appointment")
    keyboard = [[InlineKeyboardButton("Yes", callback_data=YES),
                 InlineKeyboardButton("No", callback_data=NO)]]
    if update.message:  # text message
        chat_id = update.message.chat.id
    else:  # inlinekeyboard
        chat_id = update.callback_query.message.chat_id
    ac = AppointmentCreator.getinstance(chat_id)  # there is no callback_queue to get the right message id from
    if ac:  # there should(!) be no case where there are no ac when this method is called
        context.bot.edit_message_text(text="Data saved. Create another appointment?",
                                      chat_id=ac.chat_id,
                                      message_id=ac.message_id,
                                      reply_markup=InlineKeyboardMarkup(keyboard))


# todo methode ist ziemlich lang. ggf nochmal in 2-3 kleienre methoden aufteilen
def process_custom_keyboard_reply(update, context):
    """
    Processes the replys of the custom keyboards. Switches,
    depending on the received data, to the next keyboard.

    :param update: Standard telegram update
    :param context: Standard telegram context
    :return: None
    """
    print("-- process_custom_keyboard_reply")
    print("== UPDATE:", update)
    print("d: ", update.callback_query.data)
    chat = update.callback_query.message.chat
    chat_id = chat.id
    message_id = update.callback_query.message.message_id
    data = update.callback_query.data

    ac = AppointmentCreator.getinstance(chat_id)
    eraser = Eraser.getinstance(chat_id)

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

    elif eraser and eraser.message_id == message_id:
        abc = rememgram.get_tasks_by_chat()

        # = Delete or cancel = #
        if data == YES:  # delete
            rememgram.delete_tasks(eraser.deletion_list)
            if chat.type == "group":
                text = "*The following appointments were deleted by {}:\n*".format(chat.reply_to_message.from_user.first_name)
                text += '\n'.join([appointment.pprint() for appointment in abc[chat_id] if appointment.id in eraser.deletion_list])  # todo untersuchen ob das mit mehreren nutzern den richtigen ausgiebt
            elif chat.type == "private":
                text = "*The following appointments were deleted:\n*"
                text += '\n'.join(["*{}* {}".format(CHECK, appointment.pprint()) for appointment in abc[chat_id] if appointment.id in eraser.deletion_list])
            context.bot.edit_message_text(text=text, chat_id=chat_id, message_id=message_id,
                                          parse_mode="Markdown")
            eraser.destroy()
            return
        elif data == NO:  # cancel
            context.bot.edit_message_text(text="*Canceled deletion!*", chat_id=chat_id, message_id=message_id, parse_mode="Markdown")
            eraser.destroy()
            return

        # = Mark or clear appointments = #
        data = int(data)
        # Toggle appointment states #
        if data in eraser.deletion_list:
            eraser.deletion_list.remove(data)
        else:
            eraser.deletion_list.append(data)

        # Create marked buttons #
        # todo kommentare
        num_columns = 3
        keyboard = []
        text = "<b>I remember the following tasks:</b>"
        row = []
        if chat_id in abc:
            for ind, appointment in enumerate(abc[chat_id]):
                if appointment.id in eraser.deletion_list:
                    text += "\n {} <b>{}.</b> {}".format(FIRE, ind, appointment.pprint())
                    row.append(InlineKeyboardButton("{} {}.".format(FIRE, ind), callback_data=str(appointment.id)))
                else:
                    text += "\n <b>{}.</b> {}".format(ind, appointment.pprint())
                    row.append(InlineKeyboardButton("{}.".format(ind), callback_data=str(appointment.id)))
                if not (ind+1) % num_columns:
                    keyboard.append(row)
                    row = []
            if row:
                keyboard.append(row)
            keyboard.append([InlineKeyboardButton(CHECK + " Delete", callback_data=YES),
                             InlineKeyboardButton(CROSS + " Cancel", callback_data=NO)])

        context.bot.edit_message_text(text=text, chat_id=chat_id,
                                      message_id=message_id, parse_mode="HTML", disable_web_page_preview=True,
                                      reply_markup=InlineKeyboardMarkup(keyboard))
    elif data.split(DELIMITER, 1)[0] == "create_here":
        data = data.split(DELIMITER, 1)[1]
        print("create_command")
        print(data)

    else:  # we don't have an AppointmentCreator or Eraser object
        print("DELETE")
        send_expired_message(message_id, chat_id, context.bot)


def inline_query_handler(update, context):
    """
    The InlineQueryHandler for the bot. It shows the switch_pm button
    and the create appointment buttons for the prepared appointments.

    :param update: the telegram.Update object
    :param context: the telegram.ext.CallbackContext object
    """
    print("-- inline_query_handler")
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
    if not context.args:
        start(update, context)
        return

    appointment_str = " ".join(context.args)

    # add the new appointments #
    new_appointments = rememgram.add_appointment(appointment_str, update.message.chat.id, context.bot)

    # reply to user #
    if new_appointments:
        text = "<b>I have added the following appointments:</b>\n"  # todo diese kleinen strings in eine gemeineinsame text datei
        text += '\n'.join(["<b>{}</b> {}".format(BULLET, appointment.pprint()) for appointment in new_appointments])
        update.message.reply_text(text=text, parse_mode="HTML")
    else:
        update.message.reply_text(text="Couldn't understand this appointment! Get help with /help or create a new appointment with /start!",
                                  parse_mode="Markdown")


def help(update, context):
    """Send a message when the command /help is issued."""
    print("-- help")
    with open(help_path, "r") as fp:
        text = fp.read()
    context.bot.send_message(chat_id=update.message.chat.id, text=text, parse_mode="HTML")


def cancel(update, context):
    print("-- cancel")
    if update.message:  # text message
        chat_id = update.message.chat.id
    else:  # inlinekeyboard
        chat_id = update.callback_query.message.chat_id
    ac = AppointmentCreator.getinstance(chat_id)
    eraser = Eraser.getinstance(chat_id)
    #context.bot.delete_message(chat_id=chat_id, message_id=update.message.message_id)

    text = "Nothing to cancel!"
    if ac:
        context.bot.edit_message_text(text="Creation canceled!", chat_id=ac.chat_id, message_id=ac.message_id)
        text = "Canceled creation - create a new appointment with /start or get help with /help"
        ac.destroy()
    if eraser:
        context.bot.edit_message_text(text="Creation canceled!", chat_id=eraser.chat_id, message_id=eraser.message_id)
        text = "Canceled deletion - create a new appointment with /start or get help with /help"

    context.bot.send_message(chat_id=chat_id, text=text)


def send_expired_message(message_id, chat_id, bot):
    print("-- send_expired_message")
    with open(expired_path, "r") as fp:
        text = fp.read()
    bot.edit_message_text(text=text,
                          chat_id=chat_id,
                          message_id=message_id,
                          parse_mode="Markdown")


"""
# generates temporary token to unlock admin features
def generate_token(update, context):
    print("-- generate_token")
    tmp_token = uuid4()
    with open(tmp_token_path, "w") as fp:
        fp.write(str(tmp_token))

    print("Temporary token: ", str(tmp_token))
"""


# todo replace this function with (e.g.) dp.add_handler(CommandHandler('r', restart, filters=Filters.user(username='@jh0ker')))
#  to make the sendall and getsendall methods access save. Create and load a admins.txt for this.
# returns the token and deletes it on the disk if there is one
"""
def get_token():
    try:
        with open(tmp_token_path, "r+") as fp:
            token = fp.read()
            fp.truncate(0)
    except IOError:
        token = None
    return token

"""


# sends the message in sendall_path if the user has teh right tmp token
def send_all(update, context):
    print("-- send_all")
    """
    token = get_token()
    if not token:
        report("Could not get the temporary token in send_all!", update)
        return
    elif len(context.args) not in [1, 2]:
        report("Wrong number of arguments in send_all!", update)
        return
    elif context.args[0] != token:
        report("Wrong token in send_all!", update)
        return
    """
    try:
        with open(sendall_path, "r") as fp:
            text = fp.read()
        if not text:
            raise IOError("Sendall file is empty!")
    except:
        update.message.reply_text(text="Nothing to send!")
        return

    # if the argument is not 'all': send it just back to the admin
    if not (context.args and context.args[0] == "all"):
        update.message.reply_text(text="Just send to you:\n" + text, parse_mode="Markdown")
        return

    # get the chat ids and send the text to the chats
    chat_ids = set([task.chat_id for task in rememgram.load_object(tasks_path)])
    num_send = 0
    for chat_id in chat_ids:
        print("TODO test this function!")
        try:
            #context.bot.send_message(chat_id=int(chat_id), text=text, parse_mode="Markdown")
            num_send += 1
        except TelegramError:
            print("Telegram Error while sending!")
    print(num_send, " messages were send!")


def delete(update, context):
    print("-- delete")
    chat_id = update.message.chat.id
    message_id = update.message.message_id
    eraser = Eraser.getinstance(chat_id)
    if eraser:  # delete old Eraser object
        send_expired_message(eraser.message_id, eraser.chat_id, context.bot)
        eraser.destroy()

    # get apps and create custom keyboard #
    num_columns = 3
    row = []
    keyboard = []
    abc = rememgram.get_tasks_by_chat()
    text = "<b>Choosing a number marks the appointment for deletion:\n</b>"
    if chat_id in abc:  # todo kommentare
        for ind, appointment in enumerate(abc[chat_id]):
            text += "\n <b>{}.</b> {}".format(ind, appointment.pprint())
            row.append(InlineKeyboardButton("{}.".format(ind), callback_data=str(appointment.id)))
            if not (ind+1) % num_columns:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton(CHECK + " Delete", callback_data=YES),
                         InlineKeyboardButton(CROSS + " Cancel", callback_data=NO)])

    # send message with keyboard attached #
    message = context.bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML", disable_web_page_preview=True,
                                       reply_markup=InlineKeyboardMarkup(keyboard))

    # create a new Eraser object #
    Eraser(chat_id, message.message_id)


# shows the appointments as text list
def info(update, context):
    print("-- info")
    chat_id = update.message.chat_id
    abc = rememgram.get_tasks_by_chat()

    text = "<b>I remember the following tasks:\n</b>"
    if chat_id in abc:
        text += '\n'.join(["<b>{}</b> {}".format(BULLET, appointment.pprint()) for appointment in abc[chat_id]])
    context.bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML", disable_web_page_preview=True)


# soll die nächsten Vorkomnisse der (regemäßigen) Termine ausgeben
def next_occurrences():
    print("-- next_occurrences")  # todo


# shows informations about the bot. therealpeterpython and the repo
"""
/about@AtAdminBot:
AtAdminBot v2.1 by @Abfelbaum

This bot is published under AGPLv3<link:https://git.thevillage.chat/Abfelbaum/atadminbot/blob/master/LICENSE> on https://git.thevillage.chat/Abfelbaum/atadminbot

Changelog<link>
"""
def about(update, context):
    with open(about_path, "r") as fp:
        text = fp.read()
    context.bot.send_message(chat_id=update.message.chat.id, text=text, parse_mode="Markdown", disable_web_page_preview=True)


# Remind the right chat of the appointment
def remind(appointment):
    bot = appointment.bot
    bot.send_message(chat_id=appointment.chat_id, text=appointment.description)


"""
# reports illegal attempts or fails to use admin features
def report(text, update=None):
    print("-- report")
    if update:
        text += " -> Update: " + str(update)

    now = datetime.datetime.now()
    result = "{}: {}".format(now, text)
    print(result)
    with open(reports_path, "a") as fp:
        fp.write(result)
"""


def error(update, context):
    """Log Errors caused by Updates."""
    print("-- error")
    logger.warning('Error "%s" caused by update "%s"', context.error, update, exc_info=1)


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


# Helper functions #
def next_stage(type, stage): return ORDERS[type][ORDERS[type].index(stage) + 1]

def previous_stage(type, stage): return ORDERS[type][ORDERS[type].index(stage) - 1]

def get_parameters(type, stage): return PARAMETERS[type].get(stage, {})

def test_handler(update, context):
    print("-- test_handler")

def main():
    print("-- main")
    # Delete temporary auth token #
    #get_token()

    # Get token #
    with open(token_path, "r") as token_file:
        token = token_file.read()

    # Create the Updater and pass it your bot's token #
    updater = Updater(token, use_context=True)

    # Get the dispatcher to register handlers #
    dp = updater.dispatcher

    # setup the admin features #
    with open(admins_path, "r") as fp:
        admins = [Filters.user(user_id=int(id)) for id in fp.readlines()]

    if admins:
        admin_filter = reduce(lambda admin1, admin2: admin1 & admin2, admins)
        dp.add_handler(CommandHandler("_sendall", send_all, filters=admin_filter))

    # Add the handlers #
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("add", add))
    dp.add_handler(CommandHandler("cancel", cancel))
    dp.add_handler(CommandHandler("delete", delete))
    dp.add_handler(CommandHandler("info", info))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("about", about))
    #dp.add_handler(CommandHandler("_gentoken", generate_token))
    dp.add_handler(CallbackQueryHandler(process_custom_keyboard_reply))
    dp.add_handler(MessageHandler(Filters.text, text_handler))
    dp.add_handler(InlineQueryHandler(inline_query_handler))

    # Log all errors #
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
