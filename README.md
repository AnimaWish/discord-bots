# discord-bots
A repo for Caius' Discord Bots

These bots require a file `secrets.txt` to reside in the same directory, which contains Caius' discord app tokens, so don't try nothin funny. 

discord.py API documentation: http://discordpy.readthedocs.io/en/latest/api.html
`python3 -m pip install discord.py`
https://stackoverflow.com/questions/51196568/create-task-asyncio-async-syntaxerror-invalid-syntax

To add a bot to a channel: https://discordapp.com/oauth2/authorize?&client_id=YOUR_CLIENT_ID_HERE&scope=bot&permissions=0

## To Do
* Generic
  * Need a better pattern for persisting data
  * Regular expressions for command matching
  * pass message to permissions checking function
* Logging
* Daemon/Cronjob
