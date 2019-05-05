#!/bin/bash

# This script checks if the process defined by the process.info file
# is still running and if not it starts it again in an detached tmux session
# with the 'start_command' command.
#
# The process.info file has to be in the format:
# process_owner
# process_name
# pid



now="$(date)"
user="$(whoami)"
tmux_name="rembot"
scriptpath="$( cd "$(dirname "$0")" ; pwd -P )"
start_command="cd ${scriptpath}; python3 ./start_rem_bot.py"

cd "${scriptpath}"

# log the date
touch log.txt
echo -e "${now}\n" >> log.txt

# if file process.info doesn't exist or the process doesn't run anymore start it again
if [ -f "process.info" ]; then
    # get the process infos
    process_owner=$(head -n 1 process.info)
    process_name=$(head -n 2 process.info | tail -n 1)
    pid=$(tail -n 1 process.info)

    # check if the process is running
    ps_out=$(ps -u "${user}")
    process_line=$(ps -q "${pid}" -u | grep "${process_owner}" | grep "${process_name}")    # checks if the process still runs

    # if the process is running do nothing
    if [ -n "${process_line}" ]; then
        echo -e "Nothing to do!\n\n" >> log.txt
        exit 0
    fi
fi

# log the action and start the process
echo -e "Start ${tmux_name} as '${user}'\n\n" >> log.txt

# stay save and try to kill the old session
tmux kill-session -t "${tmux_name}"

# create the new session
tmux new-session -d -s "${tmux_name}"
tmux send-keys -t "${tmux_name}" "${start_command}" C-m   #C-m is enter
