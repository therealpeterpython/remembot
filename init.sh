#!/bin/bash
#
# This is the init script of the rememgram bot written by
# therealpeterpython (github.com/therealpeterpython).
# You can find the bot and my other work at
# github.com/therealpeterpython/remembot.
# Feel free to submit issues, requests and feedback via github.
#
# This program is licensed under CC BY-SA 4.0 by therealpeterpython.
#


DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
UNITNAME="remembot.service"
PYTHON="$( which python3 )"

# ================================== #
# ======= Defining functions ======= #
# ================================== #

welcome () {
    clear
    echo -e "$(<logo.txt)\n"
    echo "Welcome to the INIT script of the remembot repository!"
    echo "This script will guide you through the initialisation of the bot."
    echo -e "You have to initialise the bot just once to activate all features.\n\n"
}

# ================================== #

use_requirements () {
    echo -en "\033[s"
    read -r -e -p "Do you want me to install the python3 requirements via pip? [Y/n]  " inp
    inp=$(echo "$inp" | tr '[:upper:]' '[:lower:]')  # to lower case
    while true
    do
        case "$inp" in
            y|yes)
                requirements=true
                break
                ;;
            n|no)
                requirements=false
                break
                ;;
            *)
                read -r -p "Please enter 'yes' or 'no'  " inp
                inp=$(echo "$inp" | tr '[:upper:]' '[:lower:]')  # to lower case
                ;;
        esac
    done
    #echo -en "\r\033[1A\033[K"
}

# ================================== #

install_requirements () {
     echo "== python3 -m pip install -r requirements.txt"
     python3 -m pip install -r requirements.txt
}

# ================================== #

use_systemd () {
    read -r -e -p "Do you want me to setup the systemd service unit to auto-(re)start the bot? [Y/n]  " inp
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
    #echo -en "\r\033[1A\033[K"
}

# ================================== #

copy_unit () {
    # make sure the directory exists
    echo "== mkdir -p $HOME/.config/systemd/user"
    mkdir -p "$HOME"/.config/systemd/user

    # copy the unit
    echo "== cp $UNITNAME $HOME/.config/systemd/user"
    cp "$UNITNAME" "$HOME"/.config/systemd/user

    # replace the placeholder for the python path
    PYTHONESC="${PYTHON//\//\\/}"
    echo "== sed -i -e 's/{INSERT-ABS-PATH-TO-PYTHON3}/$PYTHONESC/g' $HOME/.config/systemd/user/$UNITNAME"
    sed -i -e "s/{INSERT-ABS-PATH-TO-PYTHON3}/$PYTHONESC/g" "$HOME"/.config/systemd/user/"$UNITNAME"

    # replace the placeholder for the rememgram path
    DIRESC="${DIR//\//\\/}"
    echo "== sed -i -e 's/{INSERT-ABS-PATH-TO-REMEMBOT}/$DIRESC\/remembot/g' $HOME/.config/systemd/user/$UNITNAME"
    sed -i -e "s/{INSERT-ABS-PATH-TO-REMEMBOT}/$DIRESC\/remembot/g" "$HOME"/.config/systemd/user/"$UNITNAME"
}

# ================================== #

activate_unit () {
    echo "== systemctl --user enable $UNITNAME"
    systemctl --user enable "$UNITNAME"
}

# ================================== #

activate_lingering () {
    echo "== loginctl enable-linger $USER"
    loginctl enable-linger "$USER"
}

# ================================== #

start_unit () {
    echo "== systemctl --user start remembot.service"
    systemctl --user start remembot.service
}

# ================================== #


goodbye () {
    echo "The initialisation of the systemd unit is done (if you didn't get any error messages)."
    echo "Maybe you want to check the status of the unit with 'systemctl --user status $UNITNAME'"
    echo "Have fun!"
}


# ================================== #
# =========== Execution ============ #
# ================================== #

welcome
use_requirements
use_systemd
echo -e "\n*********************  Executed commands:  *********************"
if [ "$requirements" == true ]
then
    install_requirements
fi

if [ "$systemd" == true ]
then
    copy_unit
    activate_unit
    activate_lingering
    start_unit
fi
echo -e "****************************************************************\n\n"
goodbye
