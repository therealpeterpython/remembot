todo ggf ein requirements file
todo /types command. Detaillierte erklärung zu den Termin arten
todo gifs erstellen https://www.ubuntupit.com/15-best-linux-screen-recorder-and-how-to-install-those-on-ubuntu/
https://askubuntu.com/questions/648603/how-to-create-an-animated-gif-from-mp4-video-via-command-line
todo /_myid implementieren um seine eigene user id herrauszufinden. der bot schreibt dir deine uid zurück

# Dokumentation Rememgram v2


## toc

## Use the bot

### Introduction
- einführung wie der bot heißt(mit link) und was er kann

### Features
#### Types of appointments
- Um alle nötigen Arten von einmaligen und sich wiederholenden Terminen abzudecken gibt es vier verschiedene Arten von Terminen.

Unique:  happens just once
Fixed period:  periodic with a fixed number of days in between
Weekday:  every nth-occurrence of the chosen weekday in each month
Day:  always at the same day in each month


| Name | Description | Usage |
| ---- | ----------- | ------- |
| Unique | An unique appointment which happens just once | Meet a friend at the pub |
| Fixed period | A repetitive appointment with a fixed number of days in beetween | Remind me doing the laundry every sunday evening |
| Weekday | A repetetive appointment once at each month at the nth-occurrence of the chosen weekday  | Every third monday in the month it's my turn to clean |
| Day | A repetetive appointment, always at the same date each month | Visit grandma each month on 17. |

#### Tips
- If you need a reminder for the same weekday every week, use ```Fixed period``` starting at this weekday with a period of seven days.
- Be carefull setting a reminder for a birthday with a fixed period of 365 days. This would work if there wouldn't be such things as leapyears. The only way to set a birthday reminder at the moment is to use unique appointments.



#### Commands
#### /new
Starts the creation of a new appointment.
The first step is to choose an appointment type.
Depending on your choice you have multiple steps in which you set the parameters of your appointment. After this you can choose to which chat the appointments belongs. If you are in the right chat you have to click on "Create appointment". 
> gif einer termin erstellung einfügen

#### /cancel
Cancels the current create or delete action.

#### /delete
Lets you select the appointments you want to delete. If you selected all of them you can click on "delete".
> gif einfügen

#### /info
Shows the saved appointments for this chat.

#### /help
Shows the help with all commands available.

#### /about
Shows information about the repository, the bot and its maker.

### Create appointments for other chats
If you need to create appointments in group chats but you don't want to spam to much, you can create the appointment in a privat chat with the bot first. When you finished the appointment you can choose to switch to the group chat and activate the appointment there. If you are currently in the group chat you can do this switching even faster by typing "@remembot " and click on "Create new date for this group!".
> inline function gif einfügen


----


## Setup your own bot
### Getting started
#### Talk to botfather
To create your own bot on telegram, you need to talk to bothfather first to get your access token. For more information read the official introduction [here](https://core.telegram.org/bots).
If you got your secret access token, you have to put it in the `remembot/bot/administration/token.txt` file.

#### Installing requirements
You can install the needed packages with the requirements file. Just type in 
```
pip install -r requirements.txt
```
To test if the bot is fully functioning navigate to `remembot/remembot`and call
```
python3 __main__.py
```
If there are no error messages you can enter `/help` in a chat with your bot to see if the bot responds.
> gif starting the bot, calling /help

#### Activate systemd service unit
You can use the systemd service unit for this bot. This unit helps you to automatically start and restart the bot. On [digitalocean.com](https://www.digitalocean.com/community/tutorials/understanding-systemd-units-and-unit-files) is a service unit described as follows:
> "A service unit describes how to manage a service or application on the server. This will include how to start or stop the service, under which circumstances it should be automatically started, and the dependency and ordering information for related software."

If you need more information about systemd units you can read the full [article](https://www.digitalocean.com/community/tutorials/understanding-systemd-units-and-unit-files).

TODO(Diesen Absatz überarbeiten. Das neue bash script erklären):
You have to move the unit to `~/.config/systemd/user` and activate it to use the service. You can activate the unit 
- erklären was eine systemd unit ist und was sie leisten kann. weiterführenden link mit angeben
- die aktivierung der unit als user oder root erklären
- wenn als user die aktivierung der lingering funktion des loginctl erklären

#### Start the bot

- MIT SYSTEMD unit: die unit erledigt die gesamte arbeit. manueller start der unit mit TODO COMMAND möglich
- OHNE SYSTEMD unit: direkt per python __main__.py. Der bot wird dann aber nicht automatisch neugestartet.


### admin features
- features erklären (_myid, _sendall)
- aktivieren indem man sich in die Admin datei einträgt


