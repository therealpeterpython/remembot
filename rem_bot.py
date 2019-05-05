# The bot and with this the "first backend".
# It gets the commands from the chats and process them.
#

import telegram
from telegram.ext import Updater, Filters, CommandHandler, MessageHandler
import logging

import rememgram


# Start the bot
def start(bot, update):
    help(bot, update)


# Add a task
def add_task(bot, update, args):
    try:
        rememgram.add_task(args, update.message.chat_id)
    except:
        err_msg = "The task could not be parsed!"
        bot.send_message(chat_id=update.message.chat_id, text=err_msg)


# Remind the appropriate chat of the task
def remind_task(task):
    bot.send_message(chat_id=task.chat_id, text=task.description)


# Check if there are task which need a reminder
def check(bot, update):
    rememgram.check_tasks()


# Write the memorised tasks in the appropriate chat
def all(bot, update):
    id = update.message.chat_id
    tbc = rememgram.get_tasks_by_chat()

    if id in tbc:
        msg = "I remember the following tasks:\n\n"
        #msg += "==========================================\n"
        msg += '\n'.join(['"'+task.description+'"' for task in tbc[id]])
        bot.send_message(id, text=msg)

# Write the memorised tasks with their id in the appropriate chat
def all_id(bot, update):
    id = update.message.chat_id
    tbc = rememgram.get_tasks_by_chat()

    if id in tbc:
        msg = "I remember the following tasks:\n\n"
        #msg += "==========================================\n"
        msg += '\n\n'.join([str(task.id)+'\n"'+task.description+'"' for task in tbc[id]])
        bot.send_message(id, text=msg)


# Deletes the given tasks (given by their id)
def delete(bot, update, args):
    if not args:
        not_msg = "Nothing to delete!"
        bot.send_message(chat_id=update.message.chat_id, text=not_msg)
        return

    ids = [int(s) for s in args]
    rememgram.delete_tasks(ids)
    ids_str = ", ".join(ids)
    del_msg = "The tasks with the ids "+ids_str+" were removed!"
    bot.send_message(chat_id=update.message.chat_id, text=del_msg)


# Delete all task of a specific chat
def delete_all(bot, update):
    rememgram.delete_all_tasks(update.message.chat_id)
    msg = "All tasks were removed!"
    bot.send_message(chat_id=update.message.chat_id, text=msg)


# Writes the help
def help(bot, update):
    help_msg = 'The most important command is /add.\n'
    help_msg += 'You can add 4 different types of dates:\n\n'

    help_msg += '1) Just once at the nth occurence of the given weekday,\n'
    help_msg += 'i.e.: /add 1x 1. Monday 3.2019 13:37 "Important meeting!"\n\n'

    help_msg += '2) Just once at the given date,\n'
    help_msg += 'i.e.: /add 20.4.2019 4:20 "Don\'t miss me!`\n\n'

    help_msg += '3) A regular monthly appointment at the nth occurence of the given weekday,\n'
    help_msg += 'i.e.: /add 2. Friday 6:42 "This is an important date."\n\n'

    help_msg += '4)  A regular monthly appointment at the given date,\n'
    help_msg += 'i.e.: /add 3. 17:42 "Clean your mess!"\n\n\n'


    help_msg += 'To get all of your tasks just write /all.\n'
    help_msg += 'If you want to delete a task you need it\'s id. To get the id\'s of your tasks type in your chat /allid.\n'
    help_msg += 'With /del <id> you can delete the task with the id <id>.\n'
    bot.send_message(chat_id=update.message.chat_id, text=help_msg)


# Main, register all the handels and the important variables
def main(token):
    global bot  # ugly workaround for the remind_task()

    # Logging the warnings and errors
    logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

    # Get the updater, dispatcher and bot
    updater = Updater(token=token)
    dispatcher = updater.dispatcher
    bot = updater.bot   # ugly workaround for the remind_task(), mayber i can pickle it(?)

    # Define handler
    start_handler = CommandHandler('start', start)
    add_task_handler = CommandHandler('add', add_task, pass_args=True)
    check_handler = CommandHandler('check', check)
    all_handler = CommandHandler('all', all)
    all_id_handler = CommandHandler('allid', all_id)
    delete_handler = CommandHandler('del', delete, pass_args=True)
    delete_all_handler = CommandHandler('forcedeleteall', delete_all)
    help_handler = CommandHandler('help', help)

    # Add handler
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(add_task_handler)
    dispatcher.add_handler(check_handler)
    dispatcher.add_handler(all_handler)
    dispatcher.add_handler(all_id_handler)
    dispatcher.add_handler(delete_handler)
    dispatcher.add_handler(delete_all_handler)
    dispatcher.add_handler(help_handler)

    # Get the updates
    updater.start_polling()
    updater.idle()

