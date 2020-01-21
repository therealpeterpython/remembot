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
from remembot.common.helper import parse_appointment_str
from remembot.bot import telegramcalendar
from remembot.bot import telegramclock


# Enable logging
logging.basicConfig(format='\n%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    level=logging.INFO, filename=log_path, filemode='a')

logger = logging.getLogger(__name__)
logger.addHandler(logging.StreamHandler())

# todo verschiedenen nutzer die gleizeitig mit dem bot arbeiten testen


# ==== Class definitions ==== #

class AppointmentCreator:
    """
    Stores the necessary information while the user creates
    appointments. Only one AppointmentCreator object per chat. The
    objects were saved at creation time in the _instances dict with
    their respective chat id as key.
    """
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
        """
        Creates command string which can be used in a
        switch_inline_query button. The command can be parsed with
        the parse_appointment_str function in helper. The specific
        order and the information in the string depends on the type
        of the appointment.
        The 4 different styles for appointment strings, if  DELIMITER = ;; and BLOCK_START = A, are:
        A;;ONCE;;13.09.2019;;14:45;;My text
        A;;EVERY_N_DAYS;;14;;13.09.2019;;14:45;;My text
        A;;NTH_WEEKDAY;;2;;MONDAY;;14:45;;My text
        A;;NUM;;13.09.2019;;14:45;;My text

        :return: Command string with all of the information about all created appointments.
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

    def new_appointment(self):
        print("- new_appointment")
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
        """
        Creates the final command string and an inline keyboard
        markup with buttons to create the appointments in another
        chat or in this chat. After this, the object destroys itself.

        :return: None
        """
        print("- finalize")
        self.command += self.create_command()
        text = self.pprint()
        keyboard = [[InlineKeyboardButton("Create in another chat >>", switch_inline_query=self.command)],
                    [InlineKeyboardButton("Create here", switch_inline_query_current_chat=self.command)]]

        self.bot.edit_message_text(text=text,
                                   chat_id=self.chat_id,
                                   message_id=self.message_id,
                                   reply_markup=InlineKeyboardMarkup(keyboard),
                                   disable_web_page_preview=True)
        self.destroy()

    def pprint(self):
        """
        Creates a pretty print string of the stored appointments.

        :return: Pretty string which can be printed without regrets.
        """
        print("- pprint")
        appointment_blocks = parse_appointment_str(self.command)
        text = ""
        for block in appointment_blocks:
            if block[1] == ONCE:
                day_name = cal.day_abbr[datetime.datetime.strptime(block[2], DATE_FORMAT).weekday()]
                text += "{} Once at {}. {} {}: \"{}\"\n".format(BULLET, day_name, block[2], block[3], block[4])
            elif block[1] == EVERY_N_DAYS:
                day_name = cal.day_abbr[datetime.datetime.strptime(block[3], DATE_FORMAT).weekday()]
                text += "{} Every {} days at {}, starting on the {}. {}: \"{}\"\n".format(BULLET, block[2], block[4], day_name, block[3], block[5])
            elif block[1] == NTH_WEEKDAY:
                text += "{} Every {}. {} at {}: \"{}\"\n".format(BULLET, block[2], cal.day_name[int(block[3])], block[4], block[5])
            elif block[1] == NUM:
                text += "{} Every month at {} {}: \"{}\"\n".format(BULLET, block[2], block[3], block[4])
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
    """
    Stores the necessary information while the user deletes
    appointments. Only one Eraser object per chat. The objects were
    saved at creation time in the _instances dict with their
    respective chat id as key.
    """
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


# ==== Command handlers ==== #

def start(update, context):
    """
    Start command handler. Calls the appointment_type function and
    creates a new AppointmentCreator object with the right message id.
    If there is already an ApointmentCreator for the given chat id,
    the old object will be destroyed and an expired message gets send.

    :param update: Standard telegram.Update object
    :param context: Standard telegram.ext.CallbackContext object
    :return: None
    """
    print("-- start")
    if update.message:  # text message
        chat_id = update.message.chat.id
    else:  # inlinekeyboard
        chat_id = update.callback_query.message.chat_id

    ac = AppointmentCreator.getinstance(chat_id)
    if ac:
        send_expired_message(ac.message_id, ac.chat_id, context.bot)
        ac.destroy()

    message = appointment_type(update, context)
    AppointmentCreator(chat_id=update.message.chat.id, message_id=message.message_id, bot=context.bot)


def add(update, context):
    """
    Add command handler. Checks if the given argument is valid and if
    so adds the appointments. If no argument was given, calls the
    start function.

    :param update: Standard telegram.Update object
    :param context: Standard telegram.ext.CallbackContext object
    :return: None
    """
    print("-- add")
    if not context.args:
        start(update, context)
        return

    appointment_str = " ".join(context.args)

    # add the new appointments #
    new_appointments = rememgram.add_appointment(appointment_str, update.message.chat.id, context.bot)

    # reply to user #
    if new_appointments:
        text = "<b>I have added the following appointments:</b>\n"
        text += '\n'.join(["<b>{}</b> {}".format(BULLET, appointment.pprint()) for appointment in new_appointments])
        update.message.reply_text(text=text, parse_mode="HTML")
    else:
        update.message.reply_text(text="Couldn't understand this appointment! Get help with /help or create a new appointment with /new!")


def help(update, context):
    """
    Help command handler. Loads the help text and sends it back to
    the user.

    :param update: Standard telegram.Update object
    :param context: Standard telegram.ext.CallbackContext object
    :return: None
    """
    print("-- help")
    with open(help_path, "r") as fp:
        text = fp.read()
    context.bot.send_message(chat_id=update.message.chat.id, text=text, parse_mode="HTML")


def cancel(update, context):
    """
    Cancel command handler. Cancels appointment creations and
    deletions.

    :param update: Standard telegram.Update object
    :param context: Standard telegram.ext.CallbackContext object
    :return: None
    """
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
        text = "Canceled creation - create a new appointment with /new or get help with /help"
        ac.destroy()
    if eraser:
        context.bot.edit_message_text(text="Creation canceled!", chat_id=eraser.chat_id, message_id=eraser.message_id)
        text = "Canceled deletion - create a new appointment with /new or get help with /help"
        eraser.destroy()

    context.bot.send_message(chat_id=chat_id, text=text)


def send_all(update, context):
    """
    _sendall command handler. This is an admin only feature. Loads
    the sendall message and sends them to the admin who requested
    this. If the argument is 'all' the message is send to ALL chats
    with active appointments.

    :param update: Standard telegram.Update object
    :param context: Standard telegram.ext.CallbackContext object
    :return: None
    """
    print("-- send_all")

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
        update.message.reply_text(text="Just send to you:\n" + text, parse_mode="HTML")
        return

    # get the chat ids and send the text to the chats
    chat_ids = set([task.chat_id for task in rememgram.load_object(tasks_path)])
    num_send = 0
    for chat_id in chat_ids:
        try:
            context.bot.send_message(chat_id=int(chat_id), text=text, parse_mode="HTML")
            num_send += 1
        except TelegramError:
            print("Telegram Error while sending!")
    print(num_send, " messages were send!")


def delete(update, context):
    """
    Delete command handler. Shows the initial delete options in an
    inline keyboard. If there is already an Eraser object for this
    chat: the old object gets deleted and an expired message is send.

    :param update: Standard telegram.Update object
    :param context: Standard telegram.ext.CallbackContext object
    :return: None
    """
    print("-- delete")
    chat_id = update.message.chat.id
    eraser = Eraser.getinstance(chat_id)
    if eraser:  # delete old Eraser object
        send_expired_message(eraser.message_id, eraser.chat_id, context.bot)
        eraser.destroy()

    # get apps and create custom keyboard #
    num_columns = 3
    row = []
    keyboard = []
    abc = rememgram.get_tasks_by_chat()  #
    text = "<b>Clicking on a number marks the appointment for deletion:\n</b>"
    if chat_id in abc:
        for ind, appointment in enumerate(abc[chat_id]):
            # create the appointment list #
            text += "\n <b>{}.</b> {}".format(ind, appointment.pprint())
            # create the keyboard with num_columns columns "
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


def info(update, context):
    """
    Info command handler. Sends the appointments as readable list
    back.

    :param update: Standard telegram.Update object
    :param context: Standard telegram.ext.CallbackContext object
    :return: None
    """
    print("-- info")
    chat_id = update.message.chat_id
    abc = rememgram.get_tasks_by_chat()

    text = "<b>I remember the following tasks:\n</b>"
    if chat_id in abc:
        text += '\n'.join(["<b>{}</b> {}".format(BULLET, appointment.pprint()) for appointment in abc[chat_id]])
    context.bot.send_message(chat_id=chat_id, text=text, parse_mode="HTML", disable_web_page_preview=True)


# soll die nächsten Vorkomnisse der (regemäßigen) Termine ausgeben
def next_occurrences():
    print("-- next_occurrences")  # todo function implementieren


def about(update, context):
    """
    About command handler. Loads the about text file and sends it
    back. The file contains informations about the bot and the
    repository.

    :param update: Standard telegram.Update object
    :param context: Standard telegram.ext.CallbackContext object
    :return: None
    """
    with open(about_path, "r") as fp:
        text = fp.read()
    context.bot.send_message(chat_id=update.message.chat.id, text=text, parse_mode="HTML", disable_web_page_preview=True)


# ==== Stage functions ==== #

def appointment_type(update, context, text="Please select a type: "):
    """
    Stage of the appointment type. Shows an inline keyboard for the
    user to choose one of the possible types. The keyboard result
    gets caught by the inline_keyboard_handler function.

    :param update: Standard telegram.Update object
    :param context: Standard telegram.ext.CallbackContext object
    :param text: The message text which is shown to the user
    :return: The send message
    """
    print("-- appointment_type")
    # create the instruction header #
    instruction = "<b><u>Instructions</u></b>\n"

    # add the introduction text #
    with open(type_path, "r") as fp:
        introduction = fp.read()
        text = introduction + instruction + text

    # create keyboard markup #
    keyboard = [[InlineKeyboardButton(APPOINTMENT_NAMES[ONCE], callback_data=ONCE),
                 InlineKeyboardButton(APPOINTMENT_NAMES[EVERY_N_DAYS], callback_data=EVERY_N_DAYS)],
                [InlineKeyboardButton(APPOINTMENT_NAMES[NTH_WEEKDAY], callback_data=NTH_WEEKDAY),
                 InlineKeyboardButton(APPOINTMENT_NAMES[NUM], callback_data=NUM)]]
    markup = InlineKeyboardMarkup(keyboard)

    # write message #
    if update.message:  # if we got here by a new message
        msg = context.bot.send_message(chat_id=update.message.chat.id, text=text, reply_markup=markup, parse_mode="HTML")
    elif update.callback_query:  # if we got here by a back button or as another appointment
        query = update.callback_query
        msg = context.bot.edit_message_text(chat_id=query.message.chat_id, text=text,
                                            message_id=query.message.message_id, reply_markup=markup, parse_mode="HTML")
    return msg


def calendar(update, context, text="Please select a date: "):
    """
    Stage of the date. Shows an inline keyboard calendar for the user
    to choose a date from. The keyboard result gets caught by
    the inline_keyboard_handler function.

    :param update: Standard telegram.Update object
    :param context: Standard telegram.ext.CallbackContext object
    :param text: The message text which is shown to the user
    :return: None
    """
    print("-- calendar")
    if update.message:  # text message
        chat_id = update.message.chat.id
    else:  # inlinekeyboard
        chat_id = update.callback_query.message.chat_id

    ac = AppointmentCreator.getinstance(chat_id)  # there is not necessary a callback_queue to get the right message id from
    if ac:  # there should(!) be no case where there are no ac when this function is called
        # create the instruction header #
        instruction = "<b><u>Instructions - {} ({}/{})</u></b>\n".format(APPOINTMENT_NAMES[ac.type],
                                                                         ORDERS[ac.type].index(ac.stage),
                                                                         len(ORDERS[ac.type])-2)

        context.bot.edit_message_text(text=instruction + text,
                                      chat_id=ac.chat_id,
                                      message_id=ac.message_id,
                                      reply_markup=telegramcalendar.create_calendar(),
                                      parse_mode="HTML")


def clock(update, context, text="Please select a time: "):
    """
    Stage of the time. Shows an inline keyboard with hours and
    minutes for the user to choose a time from. The keyboard result
    gets caught by the inline_keyboard_handler function.

    :param update: Standard telegram.Update object
    :param context: Standard telegram.ext.CallbackContext object
    :param text: The message text which is shown to the user
    :return: None
    """
    print("-- clock")
    if update.message:  # text message
        chat_id = update.message.chat.id
    else:  # inlinekeyboard
        chat_id = update.callback_query.message.chat_id

    ac = AppointmentCreator.getinstance(chat_id)  # there is not necessary a callback_queue to get the right message id from
    if ac:  # there should(!) be no case where there are no ac when this function is called
        # create the instruction header #
        instruction = "<b><u>Instructions - {} ({}/{})</u></b>\n".format(APPOINTMENT_NAMES[ac.type],
                                                                         ORDERS[ac.type].index(ac.stage),
                                                                         len(ORDERS[ac.type]) - 2)
        context.bot.edit_message_text(text=instruction + text,
                                      chat_id=ac.chat_id,
                                      message_id=ac.message_id,
                                      reply_markup=telegramclock.create_clock(),
                                      parse_mode="HTML")


def weekday(update, context, text="Please select the weekday: "):
    """
    Stage of the weekday. Shows an inline keyboard with the weekdays
    for the user to choose one from. The keyboard result gets caught
    by the inline_keyboard_handler function.

    :param update: Standard telegram.Update object
    :param context: Standard telegram.ext.CallbackContext object
    :param text: The message text which is shown to the user
    :return: None
    """
    print("-- weekday")
    if update.message:  # text message
        chat_id = update.message.chat.id
    else:  # inlinekeyboard
        chat_id = update.callback_query.message.chat_id

    ac = AppointmentCreator.getinstance(chat_id)  # there is no callback_queue to get the right message id from
    if ac:  # there should(!) be no case where there are no ac when this function is called
        # create the instruction header #
        instruction = "<b><u>Instructions - {} ({}/{})</u></b>\n".format(APPOINTMENT_NAMES[ac.type],
                                                                         ORDERS[ac.type].index(ac.stage),
                                                                         len(ORDERS[ac.type]) - 2)
        context.bot.edit_message_text(text=instruction + text,
                                      chat_id=ac.chat_id,
                                      message_id=ac.message_id,
                                      reply_markup=telegramcalendar.create_weekdays(),
                                      parse_mode="HTML")


def next(update, context, text="Data saved. Create another appointment?"):
    """
    Stage of the next appointment. Shows an inline keyboard with
    'Yes' and 'No'. The user can decide if he want to create another
    appointment. The keyboard result gets caught by the
    inline_keyboard_handler function.

    :param update: Standard telegram.Update object
    :param context: Standard telegram.ext.CallbackContext object
    :param text: The message text which is shown to the user
    :return: None
    """
    print("-- next")
    keyboard = [[InlineKeyboardButton("Yes", callback_data=YES),
                 InlineKeyboardButton("No", callback_data=NO)]]
    if update.message:  # text message
        chat_id = update.message.chat.id
    else:  # inlinekeyboard
        chat_id = update.callback_query.message.chat_id

    ac = AppointmentCreator.getinstance(chat_id)  # there is no callback_queue to get the right message id from
    if ac:  # there should(!) be no case where there are no ac when this function is called
        context.bot.edit_message_text(text=text,
                                      chat_id=ac.chat_id,
                                      message_id=ac.message_id,
                                      reply_markup=InlineKeyboardMarkup(keyboard))


def count(update, context, text="Please type in the number of days: "):
    """
    Stage of the number. Sends a text message to the user that he
    needs to type in a number. This can be any needed number and can
    be specified with the text parameter. The user response gets
    caught by the text_handler function.

    :param update: Standard telegram.Update object
    :param context: Standard telegram.ext.CallbackContext object
    :param text: The message text which is shown to the user
    :return: None
    """
    print("-- count")
    if update.message:  # text message
        chat_id = update.message.chat.id
    else:  # inlinekeyboard
        chat_id = update.callback_query.message.chat_id
    ac = AppointmentCreator.getinstance(chat_id)  # there is not necessary a callback_queue to get the right message id from

    if ac:  # there should(!) be no case where there are no ac when this function is called
        # create the instruction header #
        instruction = "<b><u>Instructions - {} ({}/{})</u></b>\n".format(APPOINTMENT_NAMES[ac.type],
                                                                         ORDERS[ac.type].index(ac.stage),
                                                                         len(ORDERS[ac.type]) - 2)

        context.bot.edit_message_text(text=instruction + text,
                                      chat_id=ac.chat_id,
                                      message_id=ac.message_id,
                                      parse_mode="HTML")


def description(update, context, text="Please type in your description: "):
    """
    Stage of the appointment description. Sends a text message to the
    user that he needs to type in a description. The user response
    gets caught by the text_handler function.

    :param update: Standard telegram.Update object
    :param context: Standard telegram.ext.CallbackContext object
    :param text: The message text which is shown to the user
    :return: None
    """
    print("-- description")
    if update.message:  # text message
        chat_id = update.message.chat.id
    else:  # inlinekeyboard
        chat_id = update.callback_query.message.chat_id
    ac = AppointmentCreator.getinstance(chat_id)  # there is not necessary a callback_queue to get the right message id from

    if ac:  # there should(!) be no case where there are no ac when this function is called
        # create the instruction header #
        instruction = "<b><u>Instructions - {} ({}/{})</u></b>\n".format(APPOINTMENT_NAMES[ac.type],
                                                                         ORDERS[ac.type].index(ac.stage),
                                                                         len(ORDERS[ac.type]) - 2)
        context.bot.edit_message_text(text=instruction + text,
                                      chat_id=ac.chat_id,
                                      message_id=ac.message_id,
                                      parse_mode="HTML")


# ==== Text handler ==== #

def text_handler(update, context):
    """
    Catches all text messages. If there is an AppointmentCreator
    object in the right stage the message is interpreted as the
    wanted input. After this the AppointmentCreator is set to the
    next stage and the function of the next stage is called.

    :param update: Standard telegram.Update object
    :param context: Standard telegram.ext.CallbackContext object
    :return: None
    """
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


# ==== Inline keyboard handler ==== #

def inline_keyboard_handler(update, context):
    """
    Catches all replies of inline keyboards. If there is an
    AppointmentCreator or Eraser object with the right chat and
    message id the keyboard data is passed to the respective
    processing function. If there isn't such an object, the inline
    keyboard gets replaced with an expired message.

    :param update: Standard telegram.Update object
    :param context: Standard telegram.ext.CallbackContext object
    :return: None
    """
    print("-- inline_keyboard_handler")
    print("== UPDATE:", update)
    print("d: ", update.callback_query.data)
    chat_id = update.callback_query.message.chat.id
    message_id = update.callback_query.message.message_id

    ac = AppointmentCreator.getinstance(chat_id)
    eraser = Eraser.getinstance(chat_id)

    if ac and ac.message_id == message_id:  # we have an AppointmentCreator object for this chat and this message
        process_ac_input(update, context, ac)

    elif eraser and eraser.message_id == message_id:  # we have an Eraser object for this chat and this message
        process_eraser_input(update, context, eraser)

    else:  # we have neither an AppointmentCreator nor Eraser object
        send_expired_message(message_id, chat_id, context.bot)


def process_ac_input(update, context, ac):
    """
    Processes the input of a keyboard of an AppointmentCreator
    object. The data is saved in the ac object if necessary, the
    object is set to the next stage and the function of the next
    stage is called.

    :param update: Standard telegram.Update object
    :param context: Standard telegram.ext.CallbackContext object
    :param ac: AppointmentCreator object related to the received data
    :return: None
    """
    data = update.callback_query.data

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
            ac.new_appointment()
            appointment_type(update, context)
        elif data == NO:
            ac.finalize()
        return  # we can return cause we moved on 'by hand'

    # If we didn't encounter a return we can move on to the next stage
    ac.stage = next_stage(ac.type, ac.stage)
    STAGE_FUNCTIONS[ac.stage](update, context, **get_parameters(ac.type, ac.stage))  # call the stage function


def process_eraser_input(update, context, eraser):
    """
    Processes the input of a keyboard of an Eraser object. The data
    is saved in the eraser objects deletion_list if necessary.

    :param update: Standard telegram.Update object
    :param context: Standard telegram.ext.CallbackContext object
    :param eraser: Eraser object related to the received data
    :return: None
    """
    data = update.callback_query.data
    chat = update.callback_query.message.chat
    chat_id = chat.id
    message_id = update.callback_query.message.message_id

    abc = rememgram.get_tasks_by_chat()

    # == Delete the marked appointments or cancel the deletion if the data is YES or NO == #
    if data == YES:  # delete
        rememgram.delete_tasks(eraser.deletion_list)
        # reply #
        if chat.type == "group":  # "group"
            text = "<b>The following appointments were deleted by {}:\n</b>".format(chat.reply_to_message.from_user.first_name)  # todo testen ob das mit mehreren nutzern den richtigen ausgiebt
        else:  # "private"
            text = "<b>The following appointments were deleted:\n</b>"

        text += '\n'.join(["<b>{}</b> {}".format(CHECK, appointment.pprint()) for appointment in abc[chat_id] if appointment.id in eraser.deletion_list])
        context.bot.edit_message_text(text=text, chat_id=chat_id, message_id=message_id, parse_mode="HTML")
        eraser.destroy()
        return  # nothing else matters  ;)
    elif data == NO:  # cancel
        context.bot.edit_message_text(text="<b>Canceled deletion!</b>", chat_id=chat_id, message_id=message_id, parse_mode="HTML")
        eraser.destroy()
        return  # nothing else matters  ;)

    # == Mark or clear appointments == #
    data = int(data)  # appointment identifier

    # Toggle appointment states if needed #
    if data in eraser.deletion_list:
        eraser.deletion_list.remove(data)
    else:
        eraser.deletion_list.append(data)

    # Create keyboard and message text #
    num_columns = 3
    keyboard = []
    text = "<b>I remember the following tasks:</b>"
    row = []
    if chat_id in abc:
        for ind, appointment in enumerate(abc[chat_id]):
            # create the appointment list (with or without the FIRE emoji) #
            if appointment.id in eraser.deletion_list:
                text += "\n {} <b>{}.</b> {}".format(FIRE, ind, appointment.pprint())
                row.append(InlineKeyboardButton("{} {}.".format(FIRE, ind), callback_data=str(appointment.id)))
            else:
                text += "\n <b>{}.</b> {}".format(ind, appointment.pprint())
                row.append(InlineKeyboardButton("{}.".format(ind), callback_data=str(appointment.id)))

            # create the keyboard with num_columns columns "
            if not (ind + 1) % num_columns:
                keyboard.append(row)
                row = []
        if row:
            keyboard.append(row)
        keyboard.append([InlineKeyboardButton(CHECK + " Delete", callback_data=YES),
                         InlineKeyboardButton(CROSS + " Cancel", callback_data=NO)])

    # send message with keyboard attached #
    context.bot.edit_message_text(text=text, chat_id=chat_id,
                                  message_id=message_id, parse_mode="HTML", disable_web_page_preview=True,
                                  reply_markup=InlineKeyboardMarkup(keyboard))


# ==== Inline query handler ==== #

def inline_query_handler(update, context):
    """
    The InlineQueryHandler for the bot. It shows the switch_pm button
    and the create appointment button for the prepared appointments.

    :param update: Standard telegram.Update object
    :param context: Standard telegram.ext.CallbackContext object
    :return: None
    """
    print("-- inline_query_handler")
    appointment_blocks = parse_appointment_str(update.inline_query.query)
    r = [InlineQueryResultArticle(id=uuid4(),
                                  title="None",
                                  input_message_content=InputTextMessageContent("/add@{} {}".format(context.bot.username, update.inline_query.query)))]
    if not appointment_blocks:
        r = []
    elif len(appointment_blocks) > 1:
        r[0].title = "Create appointments"
    else:
        r[0].title = "Create appointment"

    update.inline_query.answer(r, switch_pm_text="Create new date for this group!",
                               switch_pm_parameter="unused_but_necessary_parameter",
                               is_personal=True)


# ==== Helper functions ==== #

def send_expired_message(message_id, chat_id, bot):
    """
    Edit the given message to the expired text. This is useful for
    old inline keyboards.

    :param message_id: Message id of the expired message
    :param chat_id: Chat id of the affected chat
    :param bot: Bot which send the old message
    :return: None
    """
    print("-- send_expired_message")
    with open(expired_path, "r") as fp:
        text = fp.read()
    bot.edit_message_text(text=text,
                          chat_id=chat_id,
                          message_id=message_id,
                          parse_mode="HTML")


def remind(appointment):
    """
    Takes an Appointment object and sends its description to its chat
    id.

    :param appointment: Appointment object from the rememgram package
    :return: None
    """
    bot = appointment.bot
    bot.send_message(chat_id=appointment.chat_id, text=appointment.description)


def error(update, context):
    """
    Log errors

    :param update: Standard telegram.Update object
    :param context: Standard telegram.ext.CallbackContext object
    :return: None
    """
    print("-- error")
    logger.warning('Error "%s" caused by update "%s"', context.error, update, exc_info=1)


def sanitize_text(text):
    """
    Sanitizes the given text. DELIMITER may not appear anywhere in
    the text and the text may not consists only of BLOCK_START. To
    prevent this, all appearances of DELIMITER get replaced by
    SEPARATOR and text = BLOCK_START gets changed to
    text = BLOCK_START + " ".

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


def next_stage(type, stage): return ORDERS[type][ORDERS[type].index(stage) + 1]

def previous_stage(type, stage): return ORDERS[type][ORDERS[type].index(stage) - 1]

def get_parameters(type, stage): return PARAMETERS[type].get(stage, {})


# ==== Main function ==== #

def check_handler(update, context):  # todo just for debug
    rememgram.check_tasks()


def main():
    """
    Main function. Creates the updater and all the handlers. Starts
    also the bot.

    :return: None
    """
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
    dp.add_handler(CommandHandler("c", check_handler))  # todo just for debug

    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("new", start))
    dp.add_handler(CommandHandler("add", add))
    dp.add_handler(CommandHandler("cancel", cancel))
    dp.add_handler(CommandHandler("delete", delete))
    dp.add_handler(CommandHandler("info", info))
    dp.add_handler(CommandHandler("help", help))
    dp.add_handler(CommandHandler("about", about))
    dp.add_handler(CallbackQueryHandler(inline_keyboard_handler))
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
                       DESCRIPTION: description, NEXT: next}
    # if i made a mistake and don't have STAGE_FUNCTIONS and the stages synced
    if len(STAGE_FUNCTIONS) != NUM_STAGES:
        raise Exception("Wrong number of stages or functions!")

    main()
