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

    @staticmethod
    def memberIsWish(member):
        return member.id == DiscordBot.WISH_USER_ID

    def buildCommandHint(self, command):
        commandHint = self.prefix + command.name
        if command.paramsHint is not None:
            commandHint += " " + command.paramsHint

        return commandHint

    ###################
    #    Commands     #
    ###################

    async def getHelp(self, message, params):
        helpMessage = "*{}*\n\n**Available Commands:**\n".format(self.greeting)
        for name, cmd in sorted(self.commandMap.items()):
            if cmd.permission(message.author) and len(cmd.helpMessage) > 0:
                helpMessage += "    `{}` - {}\n".format(self.buildCommandHint(cmd), cmd.helpMessage)

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
        def __init__(self, initiatorID, text, choices, maxVoteCount):
            self.initiatorID = initiatorID
            self.text = text
            self.choices = []
            self.emojiMap = {} # emojiMap[choiceID] = emoji
            self.maxVoteCount = maxVoteCount
            self.votes = {} #votes[userID] = [choiceIndex1, choiceIndex2, ...]
            self.closed = False

            # Construct the emoji map
            emojiCode = 127462 # :regional_identifier_a:
            for i, choice in enumerate(choices):
                if i > 19:
                    break
                self.choices.append(choice)
                self.emojiMap[i] = chr(emojiCode)
                emojiCode = emojiCode + 1

        def getChoiceFromEmoji(self, emoji):
            # Get the choice index from the emoji
            choiceIndex = None
            for index, mapEmoji in self.emojiMap.items():
                if mapEmoji == emoji:
                    choiceIndex = index

            return choiceIndex


        def addVote(self, userID, emoji):
            if self.closed:
                return

            addedChoiceIndex = self.getChoiceFromEmoji(emoji)
            if addedChoiceIndex is None:
                return

            if userID not in self.votes:
                self.votes[userID] = []

            nextVoteIndex = len(self.votes[userID]) % self.maxVoteCount

            if nextVoteIndex >= len(self.votes[userID]):
                self.votes[userID].append(addedChoiceIndex)
            else:
                self.votes[userID][nextVoteIndex] = addedChoiceIndex

        def removeVote(self, userID, emoji):
            if self.closed:
                return

            removedChoiceIndex = self.getChoiceFromEmoji(emoji)
            if removedChoiceIndex is None:
                return

            for voteIndex, existingChoiceIndex in enumerate(self.votes[userID]):
                if existingChoiceIndex == removedChoiceIndex:
                    self.votes[userID].pop(voteIndex)
                    return


    currentReferendums = {} #currentReferendums[message.ID] = Referendum
    # !callvote Send a manned mission to mars. [yes, no, give money to the rich]
    async def callVote(self, message, params):
        for messageID in self.currentReferendums:
            if self.currentReferendums[messageID].initiatorID == message.author.id and not self.currentReferendums[messageID].closed:
                await self.client.send_message(message.channel, "You already have a referendum on the floor! Type `{}` to resolve the vote!".format(self.buildCommandHint(self.commandMap['elect'])))
                return

        # Parse parameters
        params = re.match("([^\[]+)\s*\[([^\]]+)\]\s*(\d+)?", params) # !callvote Elect a letter [a, b, c] numvotes
        ballotText = params.group(1)
        choices = re.split('[;|,]', params.group(2))
        try:
            maxVoteCount = int(params.group(3))
            if maxVoteCount < 1:
                maxVoteCount = 1
        except:
            maxVoteCount = 1

        if ballotText is None:
            await self.client.send_message(message.channel, "You need text for your referendum! Try `{}`".format(self.buildCommandHint(self.commandMap['elect'])))
            return
        if len(choices) is None:
            await self.client.send_message(message.channel, "You need choices for your referendum! Try `{}`".format(self.buildCommandHint(self.commandMap['elect'])))
            return

        referendum = self.Referendum(message.author.id, ballotText, choices, maxVoteCount)

        def constructBallotMessage(referendum):
            ballotMessage = "__**Referendum:**__ {}\n\n__**Choices**__".format(referendum.text)
            for i, choice in enumerate(referendum.choices):
                ballotMessage = "{}\n{} {}".format(ballotMessage, referendum.emojiMap[i], choice)

            helpMessage = "You have one vote: your MOST RECENT vote will be the one that is counted."
            if maxVoteCount > 1:
                helpMessage = "You have {} votes: your MOST RECENT {} votes will be the ones that are counted.".format(referendum.maxVoteCount, referendum.maxVoteCount)

            ballotMessage = ballotMessage + "\n\n*Click an emoji to vote! " + helpMessage + "*"

            return ballotMessage

        postedMessage = await self.client.send_message(message.channel, constructBallotMessage(referendum))

        self.currentReferendums[postedMessage.id] = referendum        

        # Add the ballot options as reactions. If we get a Forbidden error, that means that people added extra reactions before the bot could finish adding them.
        # In that case, we're going to adjust the ballot to use their reactions as options.
        injectedReaction = False
        for i, choice in enumerate(referendum.choices):
            try:
                await self.client.add_reaction(postedMessage, referendum.emojiMap[i])
            except discord.errors.Forbidden:
                injectedReaction = True
                break

        if injectedReaction:
            updatedPostedMessage = await self.client.get_message(message.channel, postedMessage.id)
            for i, reaction in enumerate(updatedPostedMessage.reactions):
                referendum.emojiMap[i] = reaction.emoji

            await self.client.edit_message(postedMessage, constructBallotMessage(referendum))

    async def resolveVote(self, message, params):
        # Find the referendum
        noReferendum = True
        referendum = None
        referendumKey = None
        for messageID in self.currentReferendums:
            if self.currentReferendums[messageID].initiatorID == message.author.id:
                noReferendum = False
                referendum = self.currentReferendums[messageID]
                referendumKey = messageID
        if noReferendum:
            await self.client.send_message(message.channel, "You don't have a referendum on the floor! Type `{}` to start a vote!".format(self.buildCommandHint(self.commandMap['callvote'])))
            return

        referendum.closed = True

        wrapperString = ":ballot_box: :ballot_box: :ballot_box:"

        # count the votes
        choiceTallies = {}
        for i, choice in enumerate(referendum.choices):
            choiceTallies[i] = 0
        for userID in referendum.votes:
            for vote in referendum.votes[userID]:
                choiceTallies[vote] = choiceTallies[vote] + 1

        # determine the winner(s)
        largestTally = -1
        winnerIndices = []
        for choiceIndex in choiceTallies:
            if choiceTallies[choiceIndex] == largestTally:
                winnerIndices.append(choiceIndex)
            elif choiceTallies[choiceIndex] > largestTally:
                largestTally = choiceTallies[choiceIndex]
                winnerIndices = [choiceIndex]

        # Announce tally
        resultMessageText = wrapperString + "\n\nRegarding the referendum, \"{}\", put forth by {}, the votes are in, and the winner is".format(referendum.text, message.server.get_member(referendum.initiatorID).mention)
        resultsMessage = await self.client.send_message(message.channel, resultMessageText+ "\n\n" + wrapperString)

        # Pause for effect
        for i in range(3):
            time.sleep(1)
            resultMessageText = resultMessageText + "."
            resultsMessage = await self.client.edit_message(resultsMessage, resultMessageText + "\n\n" + wrapperString)

        time.sleep(1)

        # Construct the winner announcement
        voteString = "vote"
        if largestTally > 1:
            voteString = "votes"

        tieVote = False
        winnerString = "\"{}\"".format(referendum.choices[winnerIndices[0]])
        if len(winnerIndices) > 1:
            tieVote = True
            for i, winner in enumerate(winnerIndices[1:]):
                nextWinner = "\"{}\"".format(referendum.choices[winner])
                if i + 1 == len(winnerIndices) - 1:
                    winnerString = winnerString + " and " + nextWinner
                else:
                    winnerString = winnerString + ", " + nextWinner
            resultMessageText += " a tie between {}, with {} {} each!".format(winnerString, largestTally, voteString)
        elif len(winnerIndices) == 1:
            resultMessageText += " {}, with {} {}!".format(winnerString, largestTally, voteString)

        await self.client.edit_message(resultsMessage, resultMessageText + "\n\n" + wrapperString)

        self.currentReferendums.pop(referendumKey)


    ###################
    #  Event Methods  #
    ###################

    async def logToChannel(self, message):
        #await self.client.send_message(self.client.get_server(DiscordBot.LOGS_SERVER_ID).get_channel(DiscordBot.LOGS_CHANNEL_ID), message)
        #print("{}: {}".format(self.client.user.name, message))

    async def on_ready(self):
        print('Logged in as {} ({})'.format(self.client.user.name, self.client.user.id))
        print('------')
        #self.loop.create_task(self.canaryLog())

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
        if user.id != self.client.user.id and reaction.message.author.id == self.client.user.id:
            if reaction.message.id in self.currentReferendums:
                self.currentReferendums[reaction.message.id].addVote(user.id, reaction.emoji)

    async def on_reaction_remove(self, reaction, user):
        if user.id != self.client.user.id and reaction.message.author.id == self.client.user.id:
            if reaction.message.id in self.currentReferendums:
                self.currentReferendums[reaction.message.id].removeVote(user.id, reaction.emoji)


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
        self.addCommand('ping',     self.ping,       lambda x: True)
        self.addCommand('echo',     self.echo,       lambda x: True)

        self.addCommand('roll',     self.getDieRoll, lambda x: True, "Roll X Y-sided dice",                  "XdY")
        self.addCommand('choose',   self.chooseRand, lambda x: True, "Choose a random member from the list", "a,list,of,things")

        self.addCommand('callvote', self.callVote,    lambda x: True, "Call a vote", "referendum text [choice a, choice b, choice c, ...]")
        self.addCommand('elect',    self.resolveVote, lambda x: True, "Count votes and decide a winner!")

        
        self.client.event(self.on_ready)
        self.client.event(self.on_message)
        self.client.event(self.on_reaction_add)
        self.client.event(self.on_reaction_remove)

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
