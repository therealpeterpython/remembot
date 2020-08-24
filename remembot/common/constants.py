# -*- coding: utf-8 -*-

# Special characters #
BULLET = "•"
FIRE = "🔥"
CHECK = "✅"
CROSS = "❌"

# Clock constants #
HOURS = 24
MINUTES = 60

# Callback data constants #
SEPARATOR = ";"  # separates callback data
#WEEKDAYS_ABBR = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]
IGNORE = "IGNORE"
BACK = "BACK"
NO = "0"
YES = "1"

# Appointment string constants #
DELIMITER = 2 * SEPARATOR  # separates data fields in the appointment string
BLOCK_START = "A"  # appointment string blocks start with this char

# Time and date formats #
DATE_FORMAT = "%d.%m.%Y"
TIME_FORMAT = "%H:%M"

# Appointment types #
ONCE, EVERY_N_DAYS, NTH_WEEKDAY, NUM = [str(i) for i in range(4)]   # str (not int) for the inline buttons
APPOINTMENT_NAMES = {ONCE: "Unique", EVERY_N_DAYS: "Fixed period", NTH_WEEKDAY: "Weekday", NUM: "Day"}

# Stages #
NUM_STAGES = 8
TYPE, DATE, TIME, COUNT, WEEKDAY, DESCRIPTION, NEXT, FINAL = range(NUM_STAGES)

# Process orders for the different appointment types #
# The order is used to determine the next function from the STAGE_FUNCTIONS list #
ORDER_ONCE = [TYPE, DATE, TIME, DESCRIPTION, NEXT]
ORDER_EVERY_N_DAYS = [TYPE, COUNT, DATE, TIME, DESCRIPTION, NEXT]
ORDER_NTH_WEEKDAY = [TYPE, COUNT, WEEKDAY, TIME, DESCRIPTION, NEXT]
ORDER_NUM = [TYPE, DATE, TIME, DESCRIPTION, NEXT]
ORDERS = {ONCE: ORDER_ONCE, EVERY_N_DAYS: ORDER_EVERY_N_DAYS, NTH_WEEKDAY: ORDER_NTH_WEEKDAY, NUM: ORDER_NUM}

# Length of the appointment blocks generated from the appointments string
BLOCK_LENGTH = {ONCE: 5, EVERY_N_DAYS: 6, NTH_WEEKDAY: 6, NUM: 5}

# Parameters for the different appointment types #
PARAMETERS_ONCE = {}
PARAMETERS_EVERY_N_DAYS = {COUNT: {"text": "Please type in the <b>number of days</b> between the appointments (1 day = every day): "},
                           DATE: {"text": "Please select the <b>first occurrence</b>: "}}
PARAMETERS_NTH_WEEKDAY = {COUNT: {"text": "Please type in the <b>number of the occurrence</b> (>=1): "}}
PARAMETERS_NUM = {DATE: {"text": "Please select the <b>day</b>: "}}
PARAMETERS = {ONCE: PARAMETERS_ONCE, EVERY_N_DAYS: PARAMETERS_EVERY_N_DAYS,
              NTH_WEEKDAY: PARAMETERS_NTH_WEEKDAY, NUM: PARAMETERS_NUM}