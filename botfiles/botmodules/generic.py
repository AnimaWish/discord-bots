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
        "Result hazy, try again later. (jk do {})",
        "{}, obviously!",
        "Choose {}.",
        "Whatever you do, DON'T pick {} (wink)",
        "Signs point to {}.",
        "*cracks open fortune cookie, finds message that says \"{}\"*",
        "My lawyers advise {}.",
        "I'm a(n) {} kind of bot myself.",
        "The choice was always going to be {}.",
        "{}!",
        "The voices tell me to choose {}.",
        "As if it were a choice! {} is the only way to move forward!",
        "Pick {}, just this once.",
        "If I had a nickel for every time it was {}...",
        ":sparkle:{}:sparkle:",
        "Given the relative positions of Mercury and Capricorn, {} is the answer.",
        "Gonna have to go with {}.",
        "It's about time we chose {}.",
        "I bought some time on the IBM quantum computer for this and it output {}.",
        "{}.",
        "{0}? Yeah, {0}",
        "Thousands of years of decisions from millions of people have culminated in this choice: {}.",
        "The mountain sage spoke in riddles: \"{}\". What could it mean?",
        "I asked a chatbot about your problem and it said to choose {}.",
        "I was going to say {} before you even asked.",
        "{} :+1:",
        "I performed a Tarot reading last night and I drew {}, which I believe signifies good fortune.",
        "{}, final answer.",
        "I've been saying {} for years.",
        "Winners choose {}.",
        "If I *must* choose, I'd go with {}.",
        ":clap: {} :clap:",
        "It's disappointing that you didn't immediately realize the answer is {}."
    ]

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

    # async def getDieRoll(self, message, params):
    #         params = params.split("d")
    #         if len(params) != 2 or not (params[0].isdigit() and params[1].isdigit()):
    #             await message.channel.send("Required syntax: `!roll XdY`")
    #         elif int(params[0]) > DiscordBot.MAX_DICE:
    #             await message.channel.send("I can't possibly hold {} dice!".format(params[0]))
    #         else:
    #             result = 0
    #             for x in range(0, int(params[0])):
    #                 result = result + random.randint(1, int(params[1]))

    #         await message.channel.send("You rolled {}!".format(result))

    #!roll 4 - 1d4 + 24 - 3 + 23d100
    async def rollDice(self, message, params):
        statements = re.sub('\s+', "", params).split(",") # remove whitespace and split on commas
        output = "🎲 " + message.author.mention + " rolled:\n"
        for statement in statements[:5]: # max of 5 rolls at once
            if statement[0] != "-":
                statement = "+"+statement

            tokens = re.findall('[\+-]\d+(?:d\d+)?', statement) # => ["+4", "-1d4", "+24", "-3", "+23d100"]

            tokenResults = [] # [[-3],[99, 3, 42, ...]]
            total = 0 # 4 - 3 + 24 - 3 + 99 + 3 + 42 + ...
            constantSubtotal = 0 # 4 + 24 - 3

            output += "**"+ statement[1:] + "** : `"
            if len(tokens) == 0:
                output += "Could not parse roll`\n"
                continue

            for token in tokens:
                sign = 1 if token[0] == "+" else -1
                token = token[1:] # remove sign
                diceParams = token.split("d")
                numDice = int(diceParams[0])
                if len(diceParams) == 1:
                    subtotal = sign * numDice
                    constantSubtotal += subtotal
                    total += subtotal
                else:
                    rolls = []
                    diceRange = int(diceParams[1])
                    for x in range(0, numDice):
                        subtotal = sign * random.randint(1, diceRange)
                        rolls.append(subtotal)
                        total += subtotal
                    tokenResults.append(rolls)

            rollResultsString = ""
            for res in tokenResults:
                rollResultsString += "+ ("
                for diceRes in res[:-1]:
                    rollResultsString += str(diceRes) + ", "
                rollResultsString += str(res[-1]) + ") "
            rollResultsString = rollResultsString[2:-1] # take off the starting plus and ending space

            constStr = ""
            if constantSubtotal != 0:
                if len(tokenResults) > 0:
                    constSignStr = "+" if constantSubtotal >= 0 else "-"
                    constStr = " " + constSignStr + " " + str(abs(constantSubtotal))
                else:
                    constStr = str(constantSubtotal)
            output += "{}{}` = **{}**\n".format(rollResultsString, constStr, str(total))

        await message.channel.send(output)
        if self.getDeleteDelay(message.channel.guild.id) > 0:
            await message.delete(delay=self.getDeleteDelay(message.channel.guild.id))

    async def chooseRand(self, message, params):
        a = re.match('^\d+', params)

        chooseNum = 1
        if a is not None:
            chooseNum = int(a.group(0))
            theList = re.split('[;|,]',params[len(a.group(0)) + 1:])
        else:
            theList = re.split('[;|,]',params)

        if chooseNum > len(theList):
            chooseNum = len(theList)

        choices = []
        for i in range(chooseNum):
            choices.append(theList.pop(random.randint(0, len(theList) - 1)).strip())

        resultString = choices[0]
        if len(choices) > 1:
            resultString = ", ".join(choices[0:-1])
            if len(choices) > 2:
                resultString = resultString + ","
            resultString = resultString + " and " + choices[-1]

        await message.channel.send(random.choice(DiscordBot.CHOICE_STRINGS).format(resultString))

    def constructReadyMessage(self, readyUsers):
        mentions = []
        for userID in readyUsers:
            if not readyUsers[userID]["isReady"]:
                mentions.append(readyUsers[userID]["mention"])
        if len(mentions) == 0:
            return "Everyone is ready!"

        return "The following people are not ready:\n{}".format("\n".join(mentions))

    async def readyCheck(self, message, params):
        if message.author.voice == None or message.author.voice.channel == None:
            await message.channel.send("You are not in a voice channel!")
            return

        voice_states = message.author.voice.channel.voice_states
        candidates = []
        for memberID in voice_states.keys():
            candidates.append(message.channel.guild.get_member(memberID))
        
        readyUsers = {}

        for candidate in candidates:
            readyUsers[candidate.id] = {"mention": candidate.mention, "isReady": False}

        message = await message.channel.send(self.constructReadyMessage(readyUsers))

        await message.add_reaction("👍")
        self.readyChecks[message.id] = {"message": message, "users": readyUsers}

    async def updateReadyCheck(self, message, reactPayload, isAddReactionEvent):
        if reactPayload.emoji.name != "👍":
            print(reactPayload.emoji)
            return

        if reactPayload.user_id not in self.readyChecks[message.id]["users"]:
            return

        self.readyChecks[message.id]["users"][reactPayload.user_id]["isReady"] = isAddReactionEvent

        await message.edit(content=self.constructReadyMessage(self.readyChecks[message.id]["users"]))

        for userID in self.readyChecks[message.id]["users"]:
            if not self.readyChecks[message.id]["users"][userID]["isReady"]:
                return

        del self.readyChecks[message.id]

    async def chooseCaptain(self, message, params):
        if message.author.voice == None or message.author.voice.channel == None:
            await message.channel.send("You are not in a voice channel!")
            return

        voice_states = message.author.voice.channel.voice_states
        candidates = []
        for memberID in voice_states.keys():
            candidates.append(message.channel.guild.get_member(memberID))
        
        await message.channel.send(random.choice(DiscordBot.CHOICE_STRINGS).format(random.choice(candidates).name))

    async def chooseTeams(self, message, params):
        if message.author.voice == None or message.author.voice.channel == None:
            await message.channel.send("You are not in a voice channel!")
            return

        # Parse out team count
        splitParams = params.split(" ", 1)
        specialUserString = ""
        if len(splitParams) > 1:
            specialUserString = splitParams[1]
        teamCount = 2
        if len(splitParams[0]) > 0:
            try:
                teamCount = int(splitParams[0])
            except ValueError:
                teamCount = 2
                specialUserString = params

        # Parse out special players
        specialUserMentions = []
        if len(specialUserString) > 1:
            specialUserMentions = specialUserString.replace("!", "").split(" ")
            for user in specialUserMentions:
                if user[:2] != "<@":
                    await message.channel.send("You need to `@mention` exceptional users for team selection.")
                    return

        # Compile lists of candidate mentions
        voice_states = message.author.voice.channel.voice_states
        candidates = []
        for memberID in voice_states.keys():
            candidates.append(message.channel.guild.get_member(memberID))

        if len(candidates) < teamCount:
            await message.channel.send("There are fewer players than teams!")
            return
        candidateMentions = []
        for candidate in candidates:
            candidateMentions.append(candidate.mention)
        for mention in specialUserMentions:
            if mention not in candidateMentions:
                await message.channel.send("{} is not in the current voice channel.".format(mention))
                return
        normalUserMentions = []
        for candidate in candidates:
            if candidate.mention not in specialUserMentions:
                normalUserMentions.append(candidate.mention)

        # Set up teams
        teams = []
        for i in range(teamCount):
            teams.append([])
        random.shuffle(specialUserMentions)
        random.shuffle(normalUserMentions)
        team_i = 0

        # Evenly distribute special users
        while len(specialUserMentions) > 0:
            teams[team_i].append(specialUserMentions.pop())
            team_i = (team_i + 1) % teamCount

        # If uneven special users, reorganize teams so teams with extra special users get remaining players last
        specialCutoffIndex = team_i
        while(team_i > 0):
            teams[team_i].append(normalUserMentions.pop())
            team_i = (team_i + 1) % teamCount
        teams = teams[specialCutoffIndex:] + teams[:specialCutoffIndex] 

        # Distribute remaining players
        while len(normalUserMentions) > 0:
            teams[team_i].append(normalUserMentions.pop())
            team_i = (team_i + 1) % teamCount

        random.shuffle(teams)

        outputMessage = "**__Teams__**\n"
        for i in range(teamCount):
            team = teams[i]
            team.sort()
            outputMessage += "**Team {}:** {}\n".format(i+1, ", ".join(team))

        await message.channel.send(outputMessage)

    async def meats(self, message, params):
        meats = [":bacon:", ":meat_on_bone:", ":cut_of_meat:", ":poultry_leg:"]
        await message.channel.send(random.choice(meats))

    ###################
    #  Event Methods  #
    ###################
    async def on_ready(self):
        print('Logged in as {} ({})'.format(self.client.user.name, self.client.user.id))
        print('------')

    async def on_message(self, message):
        commandPattern = "^\{}\S+\s*".format(self.prefix)
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

    async def on_raw_reaction_add(self, payload):
        if payload.message_id in self.readyChecks:
            await self.updateReadyCheck(self.readyChecks[payload.message_id]["message"], payload, True)

    async def on_raw_reaction_remove(self, payload):
        if payload.message_id in self.readyChecks:
            await self.updateReadyCheck(self.readyChecks[payload.message_id]["message"], payload, False)

    ###################
    #     Startup     #
    ###################

    def getName(self):
        return "generic"

    def __init__(self, prefix="!", greeting="Hello", farewell="Goodbye"):
        self.loop = asyncio.get_event_loop()
        self.client = discord.Client(loop=self.loop)

        self.prefix = prefix
        self.greeting = greeting
        self.farewell = farewell

        self.commandMap = {}
        self.eventListeners = {}

        self.readyChecks = {} # {messageID => {users: {userID: {mention: mentionString, isReady: bool}}, message: messageObj}}

        self.addCommand('help',     self.getHelp,    lambda x: True)
        self.addCommand('ping',     self.ping,       lambda x: True)
        self.addCommand('echo',     self.echo,       lambda x: True)

        self.addCommand('roll',     self.rollDice,   lambda x: True, "Roll dice", "4d3 + 4 + 1d20")
        self.addCommand('choose',   self.chooseRand, lambda x: True, "Choose a random member from the list", "a,list,of,things")

        self.addCommand('captain', self.chooseCaptain, lambda x: True, "Choose a random user from the current voice channel")
        self.addCommand('teams', self.chooseTeams, lambda x: True, "Divide the current channel into teams, 2 by default")
        self.addCommand('ready', self.readyCheck, lambda x: True, "Initiate a ready check for users in the current voice channel")

        self.addCommand('meats', self.meats, lambda x: True)
        
        self.client.event(self.on_ready)
        self.client.event(self.on_message)
        self.client.event(self.on_raw_reaction_add)
        self.client.event(self.on_raw_reaction_remove)
