import rem_bot
import rememgram
import threading
import time

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
        while not self._stopevent.isSet():
            rememgram.check_tasks()
            self._stopevent.wait(30)
            
    def join(self, timeout=None):
        """ Stop the thread. """
        self._stopevent.set()
        threading.Thread.join(self, timeout)



        
        
        
token_path = "./token.txt"

with open(token_path, "r") as token_file:
    token_list = [line.strip('\n') for line in token_file]
        
for num, token in enumerate(token_list):
    tmp_rbs = rem_bot_starter(name="rbs_bot["+str(num)+"]", token=token)
    # If tmp_rbs is a daemon thread it stops when every other non daemon thread has stopped 
    tmp_rbs.daemon = True  
    tmp_rbs.start()

tc = task_checker(name = "tc") 
tc.start()

# Dont let the main programm just ends
while True:
    try:
        time.sleep(120)
    except KeyboardInterrupt: # let the main and with this the rbs thread end
        print("\n\nCiao, kakao!")
        break

