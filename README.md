# discord-bots
A repo for Caius' Discord Bots

## Running The Thing:
* Define your bot in the Discord Developer Portal https://discordapp.com/developers/applications/
* Install the discord library https://discordpy.readthedocs.io/en/latest/intro.html#installing
* Create your bot in the `/botfiles` directory 
	* add a corresponding entry to `__init__.py`
	* Add your bot to the `bots` Dictionary object in `main.py`
* Create `secrets.txt` in root project directory, with entries formatted like `filename.py:BOT_CLIENT_SECRET` 
	* You can find your bot's Client Secret in the "Bot" tab for your bot in the Developer Portal
	* `filename.py` should be a file inside the `botfiles` directory, e.g. `discord-bots/botfiles/generic.py`
* Add your bot to a channel by visiting `https://discordapp.com/oauth2/authorize?&client_id=YOUR_CLIENT_ID_HERE&scope=bot&permissions=0`
* run `python3 main.py`

discord.py API documentation: https://discordpy.readthedocs.io/

## To Do
* Generic
  * Need a better pattern for persisting data
  * Regular expressions for command matching
  * pass message to permissions checking function
  	* i can't remember why this is to do but this might still be a good idea
  * command pattern needs sub-commands
  * better help message structure
  * botCommands are mapped to lists of callbacks, not just one
  * better namespacing for state in bot modules
* Event
  * Plus Ones
* Logging
  * Full logs saved to disk (?)
  * Bots should self identify in print statements
* Unit testing :scream:
