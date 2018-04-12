import discord
import asyncio
import random
import urllib.request
import re
import os

class BotCommand:
		# permissionFunction expects a User as an argument, and returns a
	    def __init__(self, method, permissionFunction):
	        self.method = method
	        self.permission = permissionFunction

class DiscordBot:
	def __init__(self, token):
		self.client = discord.Client()
		self.token = token
		self.commandMap = {}

	###################
	#     Helpers     #
	###################

	def memberHasRole(member, roleId):
	    for role in member.roles:
	        if role.id == roleId:
	            return True

	    return False

	###################
	#    Commands     #
	###################

	# TODO generate this programmatically
	def getHelp():
	    return """
	Hit up Wish#6215 for feature requests/bugs, or visit my repository at https://github.com/AnimaWish/discord-bots
	"""

	def chooseRand(list):
	    theList = re.split('[; |,\s]',list)
	    return random.choice(CHOICE_STRINGS).format(random.choice(theList))

	###################
	#  Event Methods  #
	###################

	@client.event
	async def on_ready():
	    print('Logged in as')
	    print(client.user.name)
	    print(client.user.id)
	    print('------')

	@client.event
	async def on_message(message):
	    commandPattern = "^!\S+\s"
	    commandMatch = re.match(commandPattern, message.content)
	    if commandMatch:
	        commandString = message.content[commandMatch.start() + 1 : commandMatch.end()].strip()
	        if commandString in commandMap:
	            command = commandMap[commandString]
	            if command.permission(message.author):
	                await client.send_message(message.channel, command.method(message.contents[commandMatch.end() + 1:]))

	###################
	#     Startup     #
	###################

	def fetchToken():
	    rootdirname = os.path.dirname(os.path.dirname(__file__))
	    secrets = open(os.path.join(rootdirname, "secrets.txt"), 'r')
	    for line in secrets:
	        parsed = line.split(":")
	        if parsed[0] == os.path.basename(__file__):
	            token = parsed[1].strip()
	            secrets.close()
	            return token

    def run(self):
		client.run(self.token)
