#!/bin/bash

# This script checks if the process defined by the process.info file
# is still running and if not it starts it again in an detached tmux session
# with the 'start_command' command.
#
#

now="$(date)"
user="$(whoami)"
tmux_name="rembot"
start_command="python3 start_rem_bot.py"


# if file process.info doesnt exist
# if process of procces.info doesnent run anymore do 1
if [ -f "process.info" ]; then
    process_owner=$(head -n 1 process.info)
    process_name=$(head -n 2 process.info | tail -n 1)
    pid=$(tail -n 1 process.info)

    ps_out=$(ps -u "${user}")
    process_line=$(ps -q "${pid}" -u | grep "${process_owner}" | grep "${process_name}")
    if [ -n "${process_line}" ]; then
        echo "Nothing to do!"
        exit 0
    fi
fi


touch log.txt
echo -e "Start ${tmux_name} at '${now}' as '${user}'\n" >> log.txt

tmux kill-session -t "${tmux_name}"

tmux new-session -d -s "${tmux_name}"
tmux send-keys -t "${tmux_name}" "${start_command}" C-m   #C-m is enter
