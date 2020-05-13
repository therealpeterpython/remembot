#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"


# ================================== #
# ======= Defining functions ======= #
# ================================== #

welcome () {
    echo "TODO ASCII LOGO"
    echo "Welcome to the INIT script of the remembot repository!"
    echo "This script will guide you through the initialisation of the bot"
    echo "You have to initialise the bot just once to activate all features"
    echo -e "\n---\n"
}

# ================================== #

use_systemd () {
    read -r -p "Do you want to use the systemd service unit to auto-(re)start the bot? [y/n]  " inp
    inp=$(echo "$inp" | tr '[:upper:]' '[:lower:]')  # to lower case

    while true
    do
        case "$inp" in
            y|yes)
                systemd=true
                break
                ;;
            n|no)
                systemd=false
                break
                ;;
            *)
                read -r -p "Please enter 'yes' or 'no'  " inp
                inp=$(echo "$inp" | tr '[:upper:]' '[:lower:]')  # to lower case
                ;;
        esac
    done
    echo -e "\n---\n"
}

# ================================== #

root_systemd () {
    echo "You should use this unit with user privileges, however you can run it as root."
    echo -e "It is highly recommended to use it with user priviliges unless you know exactly what you do!\n"

    read -r -p "Do you want to run the unit with user priviliges only (recommended)? [Y/n]  " inp
    inp=$(echo "$inp" | tr '[:upper:]' '[:lower:]')  # to lower case

    while true
    do
        case "$inp" in
            ""|y|yes)
                root=false
                break
                ;;
            n|no)
                echo "You want to run the unit as root!"
                root=true
                break
                ;;
            *)
                read -r -p "Please enter 'yes' or 'no'  " inp
                inp=$(echo "$inp" | tr '[:upper:]' '[:lower:]')  # to lower case
                ;;
        esac
    done
    echo -e "\n---\n"
}

# ================================== #

# Todo: Dont forget to change the owner of the file if necessary!
copy_unit () {
    if [ "$root" == true ]
    then
        echo "TODO cp root" # /etc/systemd/system
    else
        echo "TODO cp user" # ~/.config/systemd/user
    fi
}

# ================================== #

activate_unit () {
    if [ "$root" == true ]
    then
        echo "TODO activate root" # sudo systemctl enable meine_unit.service
    else
        echo "TODO activate user" # systemctl --user enable meine_unit.service
    fi
}

# ================================== #

activate_lingering () {
    echo "TODO activate lingering"
}

# ================================== #

start_unit () {
    if [ "$root" == true ]
    then
        echo "TODO start root"
    else
        echo "TODO start user"
    fi
}

# ================================== #


goodbye () {
    echo "The initialisation of the systemd unit is done."
    echo "You may need to install some python packages. To do this you can enter 'pip install -r requirements.txt'."
    echo "Have fun!"
}


# ================================== #
# =========== Execution ============ #
# ================================== #

welcome
use_systemd
if [ "$systemd" == true ]
then
    root_systemd
    copy_unit
    activate_unit
    if [ "$root" == false ]
    then
        activate_lingering  #TODO: Warum habe ich das hier nicht für root gemacht?? <- root kann die nach "/etc/systemd/system/" legen, dort wird sie bei boot ausgeführt
    fi
    start_unit
fi
goodbye
