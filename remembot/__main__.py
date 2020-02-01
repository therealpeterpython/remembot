import os
import sys
# add the top level package to the path #
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from remembot.bot import frankenbot

def main():
    frankenbot.main()

if __name__ == "__main__":
    main()
