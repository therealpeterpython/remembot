import os
import sys
import time
from _thread import start_new_thread
from telegram.error import NetworkError

# add the top level package to the path to handle imports in subpackages #
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from remembot.bot import frankenbot
from remembot.rememgram import rememgram
from remembot.common.config import checkup_interval


def appointment_checker():
    while True:
        try:  # try to check the appointments
            rememgram.check_appointments()
        except NetworkError:  # ignore network errors
            pass
        time.sleep(checkup_interval)


def main():
    start_new_thread(appointment_checker, ())  # start the appointment checker

    try:
        frankenbot.main()  # start the bot (blocking)
        print("\n\nCiao, Kakao!")
    except NetworkError as e:
        warning = str(e).split("/bot")  # split at /bot to censor private information about the bot
        warning = warning[0] + "[...]" if len(warning) > 1 else warning[0]  # if there were such information replace them with [...]
        print("Warning: ", warning)


if __name__ == "__main__":
    main()
