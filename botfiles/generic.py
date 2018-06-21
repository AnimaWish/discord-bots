import discord
import asyncio
import random
import urllib.request
import re
import os, io
import threading
import datetime

class BotCommand:
    # method must accept `message` and `params`, and return a string or None
    # permissionFunction expects a User/Member as an argument, and returns a bool
    def __init__(self, method, permissionFunction, helpMessage="", helpParams=None):
        self.method = method
        self.permission = permissionFunction
        self.helpParams = helpParams
        self.helpMessage = helpMessage

    def execute(self, params, message):
        if self.permission(message.author):
            return self.method(message=message, params=params)
        else:
            raise PermissionError("{}#{}:({})".format(message.author.name, message.author.discriminator, message.author.id))

class DiscordBot:
    WISH_USER_ID = '199401793032028160'
    LOGS_CHANNEL_ID = '450171692954943488'

    MAX_DICE = 1000000

    CHOICE_STRINGS = [
        "I choose... {}!",
        "How about {}?",
        "Result hazy, try again later (jk do {})",
        "{}, obviously!",
        "Choose {}.",
        "Whatever you do, DON'T pick {} (wink)",
        "Signs point to {}",
        "*cracks open fortune cookie, finds message that says \"{}\"*",
        "My lawyers advise {}",
        "I'm a {} guy myself."
    ]

    ###################
    #     Helpers     #
    ###################

    def addCommand(self, commandName, methodFunction, permissionFunction, helpMessage="", helpParams=None):
        self.commandMap[commandName] = BotCommand(methodFunction, permissionFunction, helpMessage, helpParams)

    def removeCommand(self, commandName):
        return self.commandMap.pop(commandName)

    def hideCommand(self, commandName):
        self.commandMap[commandName].helpMessage = ""

    @staticmethod
    def memberHasRole(member, roleId):
        for role in member.roles:
            if role.id == roleId:
                return True

        return False

    @staticmethod
    def memberIsWish(member):
        return member.id == DiscordBot.WISH_USER_ID

    ###################
    #    Commands     #
    ###################

    def getHelp(self, message, params):
        helpMessage = "*{}*\n\n**Available Commands:**\n".format(self.greeting)
        for commandName, botCommand in sorted(self.commandMap.items()):
            if botCommand.permission(message.author) and len(botCommand.helpMessage) > 0:
                commandField = self.prefix + commandName
                if botCommand.helpParams is not None:
                    commandField += " " + botCommand.helpParams
                helpMessage += "    `{}` - {}\n".format(commandField, botCommand.helpMessage)

        helpMessage += "\nHit up Wish#6215 for feature requests/bugs, or visit my repository at https://github.com/AnimaWish/discord-bots"

        return helpMessage

    def ping(self, message, params):
        return "pong"

    def echo(self, message, params):
        return params

    def getDieRoll(self, message, params):
            params = params.split("d")
            if len(params) != 2 or not (params[0].isdigit() and params[1].isdigit()):
                return "Required syntax: `!roll XdY`"
            elif int(params[0]) > DiscordBot.MAX_DICE:
                return "I can't possibly hold {} dice!".format(params[0])
            else:
                result = 0
                for x in range(0, int(params[0])):
                    result = result + random.randint(1, int(params[1]))

            return "You rolled {}!".format(result)

    def chooseRand(self, message, params):
        theList = re.split('[;|,\s]',params)
        return random.choice(DiscordBot.CHOICE_STRINGS).format(random.choice(theList.strip()))

    def chooseCaptain(self, message, params):
        if message.author.voice.voice_channel == None:
            return "You are not in a voice channel!"
        captain = random.choice(message.author.voice.voice_channel.voice_members)
        return random.choice(DiscordBot.CHOICE_STRINGS).format(captain.name)

    ###################
    #  Event Methods  #
    ###################

    async def logToChannel(self, message):
        #await self.client.send_message(self.client.get_server(DiscordBot.LOGS_SERVER_ID).get_channel(DiscordBot.LOGS_CHANNEL_ID), message)
        print("{}: {}".format(self.client.user.name, message))

    async def on_ready(self):
        print('Logged in as {} ({})'.format(self.client.user.name, self.client.user.id))
        print('------')
        self.loop.create_task(self.canaryLog())

    async def on_message(self, message):
        commandPattern = "^{}\S+\s*".format(self.prefix)
        commandMatch = re.match(commandPattern, message.content)
        if commandMatch:
            commandString = message.content[commandMatch.start() + len(self.prefix) : commandMatch.end()].strip()
            if commandString in self.commandMap:
                command = self.commandMap[commandString]
                params  = message.content[commandMatch.end():].strip()
                try: 
                    result = command.execute(params, message)
                    if isinstance(result, io.IOBase):
                        await self.client.send_file(message.channel, result)
                    elif result is not None and len(result) > 0:
                        await self.client.send_message(message.channel, result)

                except PermissionError as err:
                    print("Insufficient permissions for user {}".format(err))

    ###################
    #     Startup     #
    ###################

    @asyncio.coroutine
    def checkForStopEvent(self):
        while True:
            if self._stop_event.is_set():
                print("Stop signal received")
                yield from self.client.logout()
                break
            try:
                yield from asyncio.sleep(3)
            except asyncio.CancelledError:
                break

    @asyncio.coroutine
    def canaryLog(self):
        while True:
            try:
                yield from self.logToChannel(str(datetime.datetime.now()))
                yield from asyncio.sleep(300)
            except asyncio.CancelledError:
                break

    def stop(self):
        self._stop_event.set()

    def __init__(self, prefix="!", greeting="Hello", farewell="Goodbye"):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.client = discord.Client(loop=self.loop)

        self.prefix = prefix
        self.greeting = greeting
        self.farewell = farewell

        self.commandMap = {}

        self.addCommand('help',   self.getHelp,    lambda x: True)
        self.addCommand('echo',   self.echo,       lambda x: True)
        self.addCommand('roll',   self.getDieRoll, lambda x: True, "Roll X Y-sided dice",                  "XdY")
        self.addCommand('choose', self.chooseRand, lambda x: True, "Choose a random member from the list", "a,list,of,things")
        self.addCommand('ping',   self.ping,       lambda x: True)

        
        self.client.event(self.on_ready)
        self.client.event(self.on_message)

        self._stop_event = threading.Event()


    def run(self, token):      
        print(self.greeting)

        checkForStopTask = self.loop.create_task(self.checkForStopEvent())
        startTask = self.client.start(token)
        wait_tasks = asyncio.wait([startTask])

        try:
            self.loop.run_until_complete(wait_tasks)
        except KeyboardInterrupt:
            checkForStopTask.cancel()
        except Exception as e:
            print("Exception: {}".format(e))
        finally:
            self.loop.run_until_complete(self.client.logout())
            self.loop.close()

        print(self.farewell)
