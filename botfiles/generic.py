import discord
import asyncio
import random
import urllib.request
import re
import os, io
import threading
import datetime, time

class BotCommand:
    # method must accept `message` and `params`, and return a string or None
    # permissionFunction expects a User/Member as an argument, and returns a bool
    def __init__(self, name, method, permissionFunction, helpMessage="", paramsHint=None):
        self.name = name
        self.method = method
        self.permission = permissionFunction
        self.paramsHint = paramsHint
        self.helpMessage = helpMessage

    def execute(self, params, message):
        if self.permission(message.author):
            return self.method(message=message, params=params)
        else:
            raise PermissionError("{}#{}:({})".format(message.author.name, message.author.discriminator, message.author.id))

class DiscordBot:
    WISH_USER_ID = 199401793032028160

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

    CAPTAIN_WEIGHT_RESET_COOLDOWN = datetime.timedelta(minutes=240)
    CAPTAIN_WEIGHT_SEVERITY = 1.0

    ###################
    # Command Helpers #
    ###################

    def addCommand(self, commandName, methodFunction, permissionFunction, helpMessage="", paramsHint=None):
        self.commandMap[commandName] = BotCommand(commandName, methodFunction, permissionFunction, helpMessage, paramsHint)

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

    def buildCommandHint(self, command):
        commandHint = self.prefix + command.name
        if command.paramsHint is not None:
            commandHint += " " + command.paramsHint

        return commandHint

    ###################
    #  Event Helpers  #
    ###################

    def addEventListener(self, eventName, eventId, func):
        if eventName not in self.eventListeners:
            self.eventListeners[eventName] = {}

        self.eventListeners[eventName][eventId] = func


    ###################
    #    Commands     #
    ###################

    async def getHelp(self, message, params):
        foundCommand = False
        for name, cmd in sorted(self.commandMap.items()):
            if params == name:
                foundCommand = True
                if not cmd.permission(message.author):
                    helpMessage = "You do not have permission for that command! try just `!help`."
                else:
                    helpMessage = "    `{}` - {}\n".format(self.buildCommandHint(cmd), cmd.helpMessage)
                break

        if not foundCommand:
            helpMessage = "*{}*\n\n**Available Commands:**\n".format(self.greeting)
            for name, cmd in sorted(self.commandMap.items()):
                if cmd.permission(message.author) and len(cmd.helpMessage) > 0:
                    helpMessage += "    `{}` - {}\n".format(self.buildCommandHint(cmd), cmd.helpMessage)

            helpMessage += "\nHit up Wish#6215 for feature requests/bugs, or visit my repository at https://github.com/AnimaWish/discord-bots"

        await message.channel.send(helpMessage)

    async def ping(self, message, params):
        await message.channel.send("pong")

    async def echo(self, message, params):
        await message.channel.send(params)

    async def getDieRoll(self, message, params):
            params = params.split("d")
            if len(params) != 2 or not (params[0].isdigit() and params[1].isdigit()):
                await message.channel.send("Required syntax: `!roll XdY`")
            elif int(params[0]) > DiscordBot.MAX_DICE:
                await message.channel.send("I can't possibly hold {} dice!".format(params[0]))
            else:
                result = 0
                for x in range(0, int(params[0])):
                    result = result + random.randint(1, int(params[1]))

            await message.channel.send("You rolled {}!".format(result))

    async def chooseRand(self, message, params):
        theList = re.split('[;|,]',params)
        if len(theList) == 1:
            theList = re.split('\s',params)
            
        await message.channel.send(random.choice(DiscordBot.CHOICE_STRINGS).format(random.choice(theList).strip()))

    captainData = {
        'lastUpdate': datetime.datetime.fromordinal(1),
        'captains': {}
    }

    async def chooseCaptain(self, message, params):
        if message.author.voice == None or message.author.voice.channel == None:
            await message.channel.send("You are not in a voice channel!")
            return

        candidates = message.author.voice.channel.members

        # Reset weights after time passes
        if datetime.datetime.now() - self.captainData['lastUpdate'] > DiscordBot.CAPTAIN_WEIGHT_RESET_COOLDOWN:
            self.captainData['captains'] = {}

        class CandidateWeight:
            def __init__(self, name, weight):
                self.name = name
                self.weight = weight

        # array of CandidateWeights
        candidateWeights = []

        # construct weights
        totalWeight = 0.0
        for candidate in candidates:
            if candidate.name in self.captainData['captains']:
                weight = 1.0/(DiscordBot.CAPTAIN_WEIGHT_SEVERITY * self.captainData['captains'][candidate.name])
            else:
                weight = 1.0

            totalWeight = totalWeight + weight
            candidateWeights.append(CandidateWeight(candidate.name, weight))

        choice = random.uniform(0.0, totalWeight)

        # search for winner
        currentPos = 0.0
        for candidateWeight in candidateWeights:
            currentPos = currentPos + candidateWeight.weight
            selectedCaptainName = candidateWeight.name
            if currentPos >= choice:
                break

        # increment weight
        if selectedCaptainName in self.captainData['captains']:
            self.captainData['captains'][selectedCaptainName] = self.captainData['captains'][selectedCaptainName] + 1.0
        else:
            self.captainData['captains'][selectedCaptainName] = 2.0

        self.captainData['lastUpdate'] = datetime.datetime.now()

        stats = ""
        if message.content == "!captain stats":
            for candidateWeight in candidateWeights:
                stats = "{}\n{} : {}".format(stats, candidateWeight.name, candidateWeight.weight)

        await message.channel.send(random.choice(DiscordBot.CHOICE_STRINGS).format(selectedCaptainName) + stats)

    ###################
    #  Event Methods  #
    ###################
    async def on_ready(self):
        print('Logged in as {} ({})'.format(self.client.user.name, self.client.user.id))
        print('------')
        for listenerID in self.eventListeners["on_ready"].keys():
            await self.eventListeners["on_ready"][listenerID]()

    async def on_message(self, message):
        commandPattern = "^{}\S+\s*".format(self.prefix)
        commandMatch = re.match(commandPattern, message.content)
        if commandMatch:
            commandString = message.content[commandMatch.start() + len(self.prefix) : commandMatch.end()].strip()
            if commandString in self.commandMap:
                command = self.commandMap[commandString]
                params  = message.content[commandMatch.end():].strip()
                try: 
                    await command.execute(params, message)
                except PermissionError as err:
                    print("Insufficient permissions for user {}".format(err))

    async def on_reaction_add(self, reaction, user):
        for listenerID in self.eventListeners["on_reaction_add"].keys():
            await self.eventListeners["on_reaction_add"][listenerID](reaction, user)
    #     if user.id != self.client.user.id and reaction.message.author.id == self.client.user.id:
    #         if reaction.message.id in self.currentReferendums:
    #             self.currentReferendums[reaction.message.id].addVote(user.id, reaction.emoji)

    async def on_reaction_remove(self, reaction, user):
        for listenerID in self.eventListeners["on_reaction_remove"].keys():
            await self.eventListeners["on_reaction_remove"][listenerID](reaction, user)
    #     if user.id != self.client.user.id and reaction.message.author.id == self.client.user.id:
    #         if reaction.message.id in self.currentReferendums:
    #             self.currentReferendums[reaction.message.id].removeVote(user.id, reaction.emoji)


    ###################
    #     Startup     #
    ###################

    # @asyncio.coroutine
    # def checkForStopEvent(self):
    #     while True:
    #         if self._stop_event.is_set():
    #             print("Stop signal received")
    #             yield from self.client.logout()
    #             break
    #         try:
    #             yield from asyncio.sleep(3)
    #         except asyncio.CancelledError:
    #             break

    # @asyncio.coroutine
    # def canaryLog(self):
    #     while True:
    #         try:
    #             yield from self.logToChannel(str(datetime.datetime.now()))
    #             yield from asyncio.sleep(300)
    #         except asyncio.CancelledError:
    #             break

    # def stop(self):
    #     self._stop_event.set()

    def __init__(self, prefix="!", greeting="Hello", farewell="Goodbye"):
        self.loop = asyncio.get_event_loop()
        #asyncio.set_event_loop(self.loop)
        self.client = discord.Client(loop=self.loop)

        self.prefix = prefix
        self.greeting = greeting
        self.farewell = farewell

        self.commandMap = {}
        self.eventListeners = {}

        self.addCommand('help',     self.getHelp,    lambda x: True)
        self.addCommand('ping',     self.ping,       lambda x: True)
        self.addCommand('echo',     self.echo,       lambda x: True)

        self.addCommand('roll',     self.getDieRoll, lambda x: True, "Roll X Y-sided dice",                  "XdY")
        self.addCommand('choose',   self.chooseRand, lambda x: True, "Choose a random member from the list", "a,list,of,things")

        self.addCommand('callvote', self.callVote,    lambda x: True, "Call a vote", "Kirk or Picard? \"Sheridan\", \"Adama\", \"Skywalker\"")
        self.addCommand('elect',    self.resolveVote, lambda x: True, "Count votes and decide a winner!")

        self.addCommand('captain', self.chooseCaptain, lambda x: True, "Choose a random user from the current voice channel")
        
        self.client.event(self.on_ready)
        self.client.event(self.on_message)
        self.client.event(self.on_reaction_add)
        self.client.event(self.on_reaction_remove)

        #self._stop_event = threading.Event()


    # def run(self, token):      
    #     print(self.greeting)

    #     checkForStopTask = self.loop.create_task(self.checkForStopEvent())
    #     startTask = self.client.start(token)
    #     wait_tasks = asyncio.wait([startTask])

    #     try:
    #         self.loop.run_until_complete(wait_tasks)
    #     except KeyboardInterrupt:
    #         checkForStopTask.cancel()
    #     except Exception as e:
    #         print("Exception: {}".format(e))
    #     finally:
    #         self.loop.run_until_complete(self.client.logout())
    #         self.loop.close()

    #     print(self.farewell)
