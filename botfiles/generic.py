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

    CAPTAIN_WEIGHT_RESET_COOLDOWN = datetime.timedelta(minutes=240)
    CAPTAIN_WEIGHT_SEVERITY = 1.0

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

    async def getHelp(self, message, params):
        helpMessage = "*{}*\n\n**Available Commands:**\n".format(self.greeting)
        for commandName, botCommand in sorted(self.commandMap.items()):
            if botCommand.permission(message.author) and len(botCommand.helpMessage) > 0:
                commandField = self.prefix + commandName
                if botCommand.helpParams is not None:
                    commandField += " " + botCommand.helpParams
                helpMessage += "    `{}` - {}\n".format(commandField, botCommand.helpMessage)

        helpMessage += "\nHit up Wish#6215 for feature requests/bugs, or visit my repository at https://github.com/AnimaWish/discord-bots"

        await self.client.send_message(message.channel, helpMessage)

    async def ping(self, message, params):
        await self.client.send_message(message.channel, "pong")

    async def echo(self, message, params):
        await self.client.send_message(message.channel, params)

    async def getDieRoll(self, message, params):
            params = params.split("d")
            if len(params) != 2 or not (params[0].isdigit() and params[1].isdigit()):
                await self.client.send_message(message.channel, "Required syntax: `!roll XdY`")
            elif int(params[0]) > DiscordBot.MAX_DICE:
                await self.client.send_message(message.channel, "I can't possibly hold {} dice!".format(params[0]))
            else:
                result = 0
                for x in range(0, int(params[0])):
                    result = result + random.randint(1, int(params[1]))

            await self.client.send_message(message.channel, "You rolled {}!".format(result))

    async def chooseRand(self, message, params):
        theList = re.split('[;|,]',params)
        if len(theList) == 1:
            theList = re.split('\s',params)
            
        await self.client.send_message(message.channel, random.choice(DiscordBot.CHOICE_STRINGS).format(random.choice(theList).strip()))

    captainData = {
        'lastUpdate': datetime.datetime.fromordinal(1),
        'captains': {}
    }

    async def chooseCaptain(self, message, params):
        if message.author.voice.voice_channel == None:
            await self.client.send_message(message.channel, "You are not in a voice channel!")
            return

        candidates = message.author.voice.voice_channel.voice_members

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

        await self.client.send_message(message.channel, random.choice(DiscordBot.CHOICE_STRINGS).format(selectedCaptainName) + stats)

    class Referendum:
        def __init__(self, initiatorID, text, choices, voteCount):
            self.initiatorID = initiatorID
            self.text = text
            self.choices = []
            self.emojiMap = {} # emojiMap[choiceID] = ":regional_indicator_LETTER:"
            self.voteCount = voteCount

            emojiCode = 127462 # :regional_identifier_a:
            for i, choice in enumerate(choices):
                if i > 19:
                    break
                self.choices.append(choice)
                self.emojiMap[i] = chr(emojiCode)
                emojiCode = emojiCode + 1

            self.votes = {} #votes[userID] = [choiceIndex1, choiceIndex2, ...]

    currentReferendums = {} #currentReferendums[message.ID] = Referendum
    # !callvote Send a manned mission to mars. [yes, no, give money to the rich]
    async def callVote(self, message, params):
        for messageID in self.currentReferendums:
            if self.currentReferendums[messageID].initiatorID == message.author.id:
                await self.client.send_message("You already have a ballot on the floor! Type `!elect` to resolve the ballot!")
                return

        params = re.match("([^\[]+)\s*\[([^\]]+)\]\s*(\d+)?", params) # !callvote Elect a letter [a, b, c] numvotes
        ballotText = params[1]
        choices = re.split('[;|,]', params[2])
        try:
            voteCount = int(params[3])
            if voteCount < 1:
                voteCount = 1
        except:
            voteCount = 1

        referendum = self.Referendum(message.author.id, ballotText, choices, voteCount)

        def constructBallotMessage(referendum):
            ballotMessage = "__**Referendum:**__ {}\n\n__**Choices**__".format(referendum.text)
            for i, choice in enumerate(referendum.choices):
                ballotMessage = "{}\n{} {}".format(ballotMessage, referendum.emojiMap[i], choice)

            helpMessage = "You have one vote: your MOST RECENT vote will be the one that is counted."
            if voteCount > 1:
                helpMessage = "You have {} votes: your MOST RECENT {} votes will be the ones that are counted.".format(referendum.voteCount, referendum.voteCount)

            ballotMessage = ballotMessage + "\n\n*Click an emoji to vote! " + helpMessage + "*"

            return ballotMessage

        postedMessage = await self.client.send_message(message.channel, constructBallotMessage(referendum))

        self.currentReferendums[postedMessage.id] = referendum        

        for i, choice in enumerate(referendum.choices):
            try:
                await self.client.add_reaction(postedMessage, referendum.emojiMap[i])
            except discord.errors.Forbidden:
                pass

        updatedPostedMessage = await self.client.get_message(message.channel, postedMessage.id)

        injectedReaction = False
        for i, reaction in enumerate(updatedPostedMessage.reactions):
            if not reaction.me:
                injectedReaction = True

            referendum.emojiMap[i] = reaction.emoji

        if injectedReaction:
            await self.client.edit_message(postedMessage, constructBallotMessage(referendum))

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
                    await command.execute(params, message)
                    # if isinstance(result, io.IOBase):
                    #     await self.client.send_file(message.channel, result)
                    # elif result is not None and len(result) > 0:
                    #     await self.client.send_message(message.channel, result)

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

        self.addCommand('help',     self.getHelp,    lambda x: True)
        self.addCommand('echo',     self.echo,       lambda x: True)
        self.addCommand('roll',     self.getDieRoll, lambda x: True, "Roll X Y-sided dice",                  "XdY")
        self.addCommand('choose',   self.chooseRand, lambda x: True, "Choose a random member from the list", "a,list,of,things")
        self.addCommand('ping',     self.ping,       lambda x: True)

        self.addCommand('callvote', self.callVote,    lambda x: True, "Call a vote", "referendum text [choice a, choice b, choice c, ...]")
        #self.addCommand('elect',    self.resolveVote, lambda x: True, "Count votes and decide a winner!")

        
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
