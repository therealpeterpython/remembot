import os
import sys
import time
from _thread import start_new_thread

# add the top level package to the path to handle imports in subpackages #
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from remembot.bot import frankenbot
from remembot.rememgram import rememgram
from remembot.common.config import checkup_interval


def appointment_checker():
    while True:
        rememgram.check_tasks()  # check the tasks
        time.sleep(checkup_interval)  # sleep


def main():
    start_new_thread(appointment_checker, ())  # start the appointment checker
    frankenbot.main()  # start the bot (blocking)

    print("\n\nCiao, Kakao!")


if __name__ == "__main__":
    main()
