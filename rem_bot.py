import telegram
from telegram.ext import Updater, Filters, CommandHandler, MessageHandler
import logging

import rememgram


def start(bot, update):
    help(bot, update)


def add_task(bot, update, args):
    try:
        rememgram.add_task(args, update.message.chat_id)
    except:
        err_msg = "The task could not be parsed!"
        bot.send_message(chat_id=update.message.chat_id, text=err_msg)


def remind_task(task):
    bot.send_message(chat_id=task.chat_id, text=task.description)


def check(bot, update):
    rememgram.check_tasks()


def all(bot, update):
    id = update.message.chat_id
    tbc = rememgram.get_tasks_by_chat()

    if id in tbc:
        msg = "Aktuelle habe ich mir folgende Aufgaben gemerkt:\n"
        msg += "==========================================\n"
        msg += '\n'.join(['"'+task.description+'"' for task in tbc[id]])
        bot.send_message(id, text=msg)


def all_id(bot, update):
    id = update.message.chat_id
    tbc = rememgram.get_tasks_by_chat()

    if id in tbc:
        msg = "Aktuelle habe ich mir folgende Aufgaben gemerkt:\n"
        msg += "==========================================\n"
        msg += '\n'.join([str(task.id)+':\t\t"'+task.description+'"' for task in tbc[id]])
        bot.send_message(id, text=msg)


def delete(bot, update, args):
    if not args:
        not_msg = "Nothing to delete!"
        bot.send_message(chat_id=update.message.chat_id, text=not_msg)
        return

    ids = [int(s) for s in args]
    rememgram.delete_tasks(ids)
    ids_str = ", ".join(str(ids))
    del_msg = "The tasks with the ids "+ids_str+" were removed!"
    bot.send_message(chat_id=update.message.chat_id, text=del_msg)


def delete_all(bot, update):
    rememgram.delete_all_tasks(update.message.chat_id)


def help(bot, update):
    help_msg = 'Mit /add können neue Termine hinzugefügt werden. Es gibt dabei 4 Arten von Terminen:\n'
    help_msg += '1) Ein einmaliger Termin nach Wochentag, \nz.b.: 1x 1. Montag 3.2019 13:37 "Dies ist ein wichtiger Termin"\n'
    help_msg += '2) Ein einmaliger Termin nach Datum,     \nz.b.: 20.4.2019 4:20 "Das solltest du nicht vergessen"\n'
    help_msg += '3) Ein monatlicher Termin nach Wochentag,\nz.b.: 2. Freitag 6:66 "Das Datum ist wichtig"\n'
    help_msg += '4) Ein monatlicher Termin nach Datum,    \nz.b.: 3. 17:42 "Hier war doch was!"\n\n'
    help_msg += 'Mit /all können alle Termine eingesehen werden, mit /allid können die ids der Termine angezeigt werden sodass diese mit /del <id> gelöscht werden können.\n'
    help_msg += '/help zeigt dir wieder diese Hilfe an.'
    bot.send_message(chat_id=update.message.chat_id, text=help_msg)


def main(token):
    global bot  # ugly workaround for the remind_task()
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    updater = Updater(token=token)
    bot = updater.bot   # ugly workaround for the remind_task()
    dispatcher = updater.dispatcher

    start_handler = CommandHandler('start', start)

    add_task_handler = CommandHandler('add', add_task, pass_args=True)
    check_handler = CommandHandler('check', check)
    all_handler = CommandHandler('all', all)
    all_id_handler = CommandHandler('allid', all_id)
    delete_handler = CommandHandler('del', delete, pass_args=True)
    delete_all_handler = CommandHandler('forcedeleteall', delete_all)
    help_handler = CommandHandler('help', help)

    dispatcher.add_handler(start_handler)

    dispatcher.add_handler(add_task_handler)
    dispatcher.add_handler(check_handler)
    dispatcher.add_handler(all_handler)
    dispatcher.add_handler(all_id_handler)
    dispatcher.add_handler(delete_handler)
    dispatcher.add_handler(delete_all_handler)
    dispatcher.add_handler(help_handler)

    updater.start_polling()
    updater.idle()

