import os

# Variables #
checkup_interval = 30  # time between appointment remind checks (in seconds)

# Paths #
dirname = os.path.dirname(__file__)

tasks_path = dirname + "/../rememgram/tasks.pkl"  # tasks file
old_tasks_path = dirname + "/../rememgram/tasks.pkl.old"  # old tasks file

log_path = dirname + "/../bot/log.txt"  # log file
token_path = dirname + "/../bot/administration/token.txt"    # file with the secret bot token
admins_path = dirname + "/../bot/administration/admins.txt"  # list of admin user ids (not chat ids!)
sendall_path = dirname + "/../bot/administration/sendall.txt"  # file with the text for the _send_all command

type_path = dirname + "/type.txt"    # file with the help text
help_path = dirname + "/help.txt"    # file with the help text
about_path = dirname + "/about.txt"  # file with the about text
expired_path = dirname + "/expired.txt"  # file with the expired text

print(tasks_path)
