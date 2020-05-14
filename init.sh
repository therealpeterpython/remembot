#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
UNITNAME="remembot.service"
PYTHON="$( which python3 )"

# ================================== #
# ======= Defining functions ======= #
# ================================== #

welcome () {
    echo "TODO ASCII LOGO"
    echo "Welcome to the INIT script of the remembot repository!"
    echo "This script will guide you through the initialisation of the bot."
    echo -e "You have to initialise the bot just once to activate all features.\n\n"
}

# ================================== #

use_systemd () {
    read -r -e -p "Do you want to use the systemd service unit to auto-(re)start the bot? [y/n]  " inp
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
    echo -en "\r\033[1A\033[K"
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
    echo "The initialisation of the systemd unit is done (if you don't get an error message)."
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
    echo "********************  Executed commands:  ********************"
    copy_unit
    activate_unit
    activate_lingering
    start_unit
    echo -e "****************************************************************\n\n"
fi
goodbye
