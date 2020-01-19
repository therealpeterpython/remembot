"""
Helper functions
"""

from remembot.common.constants import *


# splits the appointment string in blocks for the (maybe) multiple appointments
# return none if its not a valid appointments string
# Block formats:
#  A;;ONCE;;13.09.2019;;14:45;;My text
#  A;;EVERY_N_DAYS;;14;;13.09.2019;;14:45;;My text
#  A;;NTH_WEEKDAY;;2;;MONDAY;;14:45;;My text
#  A;;NUM;;13.09.2019;;14:45;;My text
def parse_appointment_str(app_str):
    print("-- parse_appointment_str")
    parameter = app_str.split(DELIMITER)
    index = [i for i, p in enumerate(parameter) if p == BLOCK_START]  # get the indices of the start token
    index.append(len(parameter))
    parameter_blocks = [parameter[index[i]: index[i+1]] for i in range(len(index)-1)]  # split into blocks

    # check that each block has the right length (from this we conclude that the block is correct)
    block_length = {ONCE: 5, EVERY_N_DAYS: 6, NTH_WEEKDAY: 6, NUM: 5}
    for block in parameter_blocks:
        if block[1] not in ORDERS or block_length[block[1]] != len(block):
            return

    print("parameter_blocks: ", parameter_blocks)
    return parameter_blocks
