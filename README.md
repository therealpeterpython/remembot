# Dokumentation Rememgram v2


## Use the bot
### Introduction
Welcome to the Remembot introduction page. Remembot is a light-weight but versatile Telegram bot which helps you to remember your appointments in time. You can add unique reminders for instance for meetings and even regular reminders for repetitive dates.
In the following you find an explanation on how to use the bot and instructions on how to setup your own instance. It's quite easy!
Trivia: The name is inspired by the Remembrall from Harry Potter.

### Features
#### Types of appointments
To enable a wide range of use cases there are four different types of appointments.

| Name | Description | Use case |
| ---- | ----------- | -------- |
| Unique | An unique appointment which happens just once | Meet a friend at the pub |
| Fixed period | A repetitive appointment with a fixed number of days in beetween | Remind me doing the laundry every sunday evening |
| Weekday | A repetitive appointment once at each month at the nth-occurrence of the chosen weekday | Every third monday in the month it's my turn to clean |
| Day | A repetitive appointment, always at the same date each month | Visit grandma each month on 17. |

#### Tips
- If you need a reminder for the same weekday every week, use ```Fixed period``` starting at this weekday with a period of seven days.
- Be carefull to set a reminder for a birthday with a fixed period of 365 days. This would work if there wouldn't be such things as leapyears. The only way to set a precise birthday reminder at the moment is to use unique appointments.

#### Commands
#### /new
Starts the creation of a new appointment.
The first step is to choose an appointment type.
Depending on your choice you have multiple steps in which you set the parameters of your appointment. After this you can decide to which chat the appointments belongs. If you are in the right chat already you can choose "Create appointment". 
![](documentation/images/new_appointment.gif)

#### /cancel
Cancels the current create or delete action.

#### /delete
Lets you select the appointments you want to delete. After you have selected them you can click on "delete".
![](documentation/images/delete_appointments.gif)

#### /info
Shows the saved appointments for this chat.

#### /help
Shows the help with all commands available.

#### /about
Shows information about the repository, the bot and its maker.

### Create appointments for other chats
If you need to create appointments in group chats but you don't want to spam to much, you can create the appointment in a private chat with the bot first. When you finished the appointment you can choose to switch to the group chat and activate the appointment there. If you are currently in the group chat you can switch even faster by typing "@remembot " (with the space) and click on "Create new date for this group!".
![](documentation/images/create_for_other_chat.gif)

## Setup your own bot
### Getting started
#### Talk to botfather
To create your own bot on telegram, you need to talk to bothfather first to get your access token. For more information read the official introduction [here](https://core.telegram.org/bots).
If you got your secret access token, you have to put it in the `remembot/bot/administration/token.txt` file.

#### Systemd service unit
You can use the systemd service unit for this bot. This unit helps you to automatically start and restart the bot. On [digitalocean.com](https://www.digitalocean.com/community/tutorials/understanding-systemd-units-and-unit-files) is a service unit described as follows:
> "A service unit describes how to manage a service or application on the server. This will include how to start or stop the service, under which circumstances it should be automatically started, and the dependency and ordering information for related software."

If you want more information about systemd units you can read the [full article](https://www.digitalocean.com/community/tutorials/understanding-systemd-units-and-unit-files).

#### Install requirements and setup the service unit
To setup the bot you should use the ./init script. It will guide you through the installation of the required python packages via pip and handels the installation of the service unit as well.
It will also offer you to activate the lingering. Lingering just means that an independent user manager is spawned at boot. This is needed to run long-running services without being logged in.

There is a single requirements file, if you need to install the packages manually.
Be aware that if you setup the service unit manually you have to replace the placeholders in the remembot.service file.

#### Start the bot
If you have installed the systemd unit with the setup script, the bot should automatically (re-)start. If you have any problems you may find
```
systemctl --user status remembot.service
```
helpfull.

To manually start the bot navigate to `remembot/remembot/` and call
```
python3 __main__.py
```
Now enter `/help` in a chat with your bot to see if the bot responds.
>![](documentation/images/help.gif)

### Administrative features
To become an admin you have to write your user id in the admin file `remembot/remembot/bot/administration/admins.txt`. Each id must be in a new line.

#### /_myid
To get your id you can use the `/_myid` command in a private chat with the bot.

#### /_sendall
If you want to send a message to all chats which have active appointments you can use this command.  
If you enter `/_sendall help` you get the help for this command. If you enter `/_sendall view` you get the currently saved message. With `/_sendall all` you can send the saved message to everyone. Every other argument after the `/_sendall` gets saved as a new message. 

### Licence 
This program is published under the CC BY-SA 4.0 license.
