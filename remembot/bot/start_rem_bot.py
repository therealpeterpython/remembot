# Starts the bot threads and the task checker
# Keeps running until it gets canceled by the user
# with ctrl+c.
#


import rem_bot
import rememgram
import threading
import time
import os
import getpass


class rem_bot_starter(threading.Thread):
    def __init__(self, name, token):
        """ constructor, setting initial variables """
        self.token = token
        threading.Thread.__init__(self, name=name)

    def run(self):
        rem_bot.main(self.token)


class task_checker(threading.Thread):
    def __init__(self, name='task_checker'):
        """ constructor, setting initial variables """
        self._stopevent = threading.Event()
        threading.Thread.__init__(self, name=name)

    def run(self):
        # make them stoppable
        while not self._stopevent.isSet():
            rememgram.check_tasks()
            self._stopevent.wait(60)

    def join(self, timeout=None):
        """ Stop the thread. """
        self._stopevent.set()
        threading.Thread.join(self, timeout)





# Path/name to/of the files 
token_path = "tokens.txt"
process_path = "process.info"

# Save the process data to make it easier to automatically check if its still running
with open(process_path, "w") as process_file:
        process_file.write(str(getpass.getuser())+"\n")
        process_file.write(str(os.path.basename(__file__))+"\n")
        process_file.write(str(os.getpid()))

# load token list
with open(token_path, "r") as token_file:
    token_list = [line.strip('\n') for line in token_file]

# Start all bots as daemons
# If their are daemon threads, they stop when every other non daemon thread has stopped
for num, token in enumerate(token_list):
    tmp_rbs = rem_bot_starter(name="rbs_bot["+str(num)+"]", token=token)
    tmp_rbs.daemon = True
    tmp_rbs.start()

# start the task checker
tc = task_checker(name = "tc")
tc.start()

# Dont let the main program just ends (with this you can end the threads with ctrl+c)
while True:
    try:
        time.sleep(120)
    except KeyboardInterrupt: # let the main and with this the threads end
        print("\n\nCiao, kakao!")
        break

