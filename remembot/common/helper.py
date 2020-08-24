"""
Helper functions
"""

from remembot.common.constants import *


def parse_appointment_str(app_str):
    """
    Splits the appointment string in blocks for each appointment and
    does a simpel checkup if they are valid.

    The 4 different styles for appointment strings, if  DELIMITER = ;; and BLOCK_START = A, are:
    A;;ONCE;;13.09.2019;;14:45;;My text
    A;;EVERY_N_DAYS;;14;;13.09.2019;;14:45;;My text
    A;;NTH_WEEKDAY;;2;;MONDAY;;14:45;;My text
    A;;NUM;;13.09.2019;;14:45;;My text

    :param app_str: String with all the information about the appointments
    :return: List of appointment blocks if all of them are valid
    """
    print("-- parse_appointment_str")
    parameter = app_str.split(DELIMITER)
    index = [i for i, p in enumerate(parameter) if p == BLOCK_START]  # get the indices of the start token
    index.append(len(parameter))
    parameter_blocks = [parameter[index[i]: index[i+1]] for i in range(len(index)-1)]  # split into blocks

    # check that each block has the correct length (from this we conclude that the blocks are valid)
    for block in parameter_blocks:
        if block[1] not in BLOCK_LENGTH or BLOCK_LENGTH[block[1]] != len(block):
            return

    return parameter_blocks
