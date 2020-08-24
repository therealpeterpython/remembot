import os

# Variables #
checkup_interval = 30  # time between appointment remind checks (in seconds)

# Paths #
dirname = os.path.dirname(__file__)

appointments_path = dirname + "/../rememgram/appointments.pkl"  # appointments file
old_appointments_path = dirname + "/../rememgram/appointments.pkl.old"  # old appointments file

log_path = dirname + "/../bot/log.txt"  # log file
token_path = dirname + "/../bot/administration/token.txt"    # secret bot token
admins_path = dirname + "/../bot/administration/admins.txt"  # list of admin user ids (not chat ids!), use /_myid to get your id
sendall_path = dirname + "/../bot/administration/sendall.txt"  # text for the _sendall command

help_sendall_path = dirname + "/help_sendall.txt"  # help text for the sendall command
help_path = dirname + "/help.txt"    # help text
type_path = dirname + "/type.txt"    # types descriptions
about_path = dirname + "/about.txt"  # about text
expired_path = dirname + "/expired.txt"  # expired text
