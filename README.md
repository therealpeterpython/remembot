# remembot
## Conclusion
remembot is a telegram bot which reminds you of your important dates.
You have to create a bot instance with the telegram [bot father](https://core.telegram.org/bots#6-botfather),
then you have to add your access token to the 'token.txt'.

## Usage
Once you've created a bot instance and added your access token to the 'token.txt' you can add your 
bot to your group or start a privat conversation with him.
That's all!

## Commands
The most important command is `/add`.
You can add 4 different types of dates:  
1) Just once at the nth occurence of the given weekday, 
i.e.: 1x 1. Monday 3.2019 13:37 "Important meeting!"
2) Just once at the given date,     
i.e.: 20.4.2019 4:20 "Don't miss me!"
3) A regular monthly appointment at the nth occurence of the given weekday,
i.e.: 2. Friday 6:66 "This is an important date."
4)  A regular monthly appointment at the given date,    
i.e.: 3. 17:42 "Clean your mess!"

## Roadmap
Some of this code is really ugly, i will rewrite parts of it.  
There are big pieces of german in it, which i will translate.