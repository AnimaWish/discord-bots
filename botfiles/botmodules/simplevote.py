import discord
import asyncio
import random
import urllib.request
import re
import math
import os, io
import threading
import datetime, time

from .generic import DiscordBot

class SimpleVoteBot(DiscordBot):
    EMOJI_SETS = {
        "letters": ["🇦","🇧","🇨","🇩","🇪","🇫","🇬","🇭","🇮","🇯","🇰","🇱","🇲","🇳","🇴","🇵","🇶","🇷","🇸","🇹","🇺","🇻","🇼","🇽","🇾","🇿"],
        #"mammals": ["🐶","🐱","🐭","🐹","🐰","🦊","🐻","🐼","🐨","🐯","🦁","🐮","🐷","🐵","🐺","🐗","🐴",], 
        "fish": ["🐙","🦑","🦀","🐡","🐠","🐟","🐬","🐳","🦈","🐊","🐚","🦐","🦞"], 
        "bugs": ["🐝","🐛","🦋","🐌","🐞","🦟","🦗","🦂",],
        "plants": ["🌵","🌲","🌴","🍁","🍄","💐","🌹","🌻","🌳"],
        "fruit": ["🍎","🍐","🍊","🍋","🍌","🍉","🍇","🍓","🍈","🍒","🍑","🥭","🍍","🥥","🥝",],
        "vegetables": ["🍅","🥑","🥦","🥒","🌶","🌽","🥕","🧅","🥔",],
        "junkfood": ["🥨","🧀","🥓","🥞","🧇","🍗","🌭","🍔","🍟","🍕","🥪","🌮","🍝","🎂","🍭","🍫","🍿","🍩","🍪",],
        "drinks": ["🍺","🥂","🍷","🥃","🍸","🍹",],
        "sports": ["⚽", "🏀","🏈","⚾","🎾","🏐","🏉","🥏","🎱","🏓","🏸","🏒","🏏",],
        "instruments": ["🎹","🥁","🎷","🎺","🎸","🪕","🎻","🎤",],
        "vehicles": ["🚗","🚕","🚌","🏎","🚓","🚑","🚒","🚛","🚜","🚲","🛵","🚂","✈️","🚀","🛸","🚁","🚤"],
        "money": ["💵","💴","💶","💷","💳","💎","⏳","🧂"],
        "hearts": ["❤️","🧡","💛","💚","💙","💜","🤍","🤎"],
        "photos": ["🗾","🎑","🏞","🌄","🌠","🎆","🌇","🌃","🌉","🌁"],
        "bodyparts": ["🦶","🦵","👄","🦷","👅","👂","👃","👁","🧠"],
        "clothes": ["🧥","🥼","🦺","👚","👕","👖","🩲","🩳","👔","👗","👙","👘","🥻","🩱"],
        "misc": ["🔫","🧲","💣","🔪","🚬","⚰️","🔮","🔬","💊","💉","🧬","🦠","🌡","🧸","🎁","💿","⏰","🧯","💎",], 
    }

    CANCEL_EMOJI = ["🚫", "⛔", "🛑"]

    ZERO_WIDTH_SPACE = "‎"

    async def parseVote(self, message, params):
        ballotPattern = "^([^\?]+\?)\s*(.+)$"

        ballotMatch = re.match(ballotPattern, params)

        if ballotMatch == None:
            await message.channel.send("I couldn't read your referendum. It should look like this: `!vote An Important Question? Choice A, Choice B, Choice C`. Remember the question mark and the commas, punctuation is important for robots!")
            return

        referendum = ballotMatch.group(1)
        choices = [a.strip() for a in ballotMatch.group(2).split(",")[:20]]

        validEmojiSets = []
        for key, emojiSet in SimpleVoteBot.EMOJI_SETS.items():
            if len(emojiSet) >= len(choices):
                validEmojiSets.append(key)

        emojiSetKey = random.choice(validEmojiSets)
        emojiMap = SimpleVoteBot.EMOJI_SETS[emojiSetKey]
        if emojiSetKey != "letters":
            random.shuffle(emojiMap)

        return (referendum, choices, emojiMap[:len(choices)])

    async def populateVoteEmoji(self, voteMessage, emojiMap, depth=1):
        # Add the ballot options as reactions. If we get a Forbidden error, that means that people added extra reactions before the bot could finish adding them.
        # In that case, we're going to adjust the ballot to use their reactions as options.
        injectedReaction = False
        for i, emoji in enumerate(emojiMap):
            try:
                await voteMessage.add_reaction(emoji)
            except discord.errors.Forbidden:
                injectedReaction = True
                break

        if injectedReaction:
            if depth < 5:
                await voteMessage.clear_reactions()
                await self.populateVoteEmoji(voteMessage, emoji, depth + 1)
            else: 
                await voteMessage.edit(content="Someone thinks they're clever and won't let me set up the ballot. Try again when they've had their naptime.")


    async def callSimpleVote(self, message, params):
        ballotText, choices, emoji = await self.parseVote(message, params)

        messageText = self.constructBallotMessage(ballotText, choices, emoji, "You can see how people voted by clicking \"Reactions\" in the menu on this message!*")

        postedMessage = await message.channel.send(messageText)
        await self.populateVoteEmoji(postedMessage, emoji)


    async def callRankVote(self, message, params):
        referendum, choices, emoji = await self.parseVote(message, params)

        text = self.constructBallotMessage(referendum, choices, emoji, "*Click emoji in order from favorite to least favorite! Remember to double check your ballot!*")
        choiceMessage = await message.channel.send(text)

        text2 = self.constructRankChoiceResultBallotsMessage(referendum, choices, emoji, [], {}, {})
        resultBallotsMessage = await message.channel.send(text2)

        text3 = self.constructRankChoiceResultStandingsMessage(referendum, choices, emoji, [], {}, {})
        resultStandingsMessage = await message.channel.send(text3)

        self.elections[choiceMessage.id] = {
            "ownerId": message.author.id,
            "ballotMessage": choiceMessage,
            "resultBallotsMessage": resultBallotsMessage,
            "resultStandingsMessage": resultStandingsMessage,
            "text": referendum,
            "choices": choices,
            "emoji": emoji,
            "ballots": {},
            "names": {}
        }

        await self.populateVoteEmoji(choiceMessage, emoji)

    async def updateRankVote(self, reactionPayload, isClosed=False):
        electionObj = self.elections[reactionPayload.message_id]

        newVote = -1
        for i in range(len(electionObj["emoji"])):
            if electionObj["emoji"][i] == reactionPayload.emoji.name:
                newVote = i
                break

        if newVote == -1 and reactionPayload.emoji.name not in self.CANCEL_EMOJI:
            return

        if newVote != -1:
            if reactionPayload.event_type == "REACTION_ADD":
                if reactionPayload.user_id not in electionObj["names"]:
                    electionObj["names"][reactionPayload.user_id] = reactionPayload.member.nick or reactionPayload.member.name
                    electionObj["ballots"][reactionPayload.user_id] = []
                electionObj["ballots"][reactionPayload.user_id].append(newVote)
            else:
                if reactionPayload.user_id in electionObj["names"]:
                    electionObj["ballots"][reactionPayload.user_id].remove(newVote)

        def sequence_exponential(n, i):
            return 2^(n-i-1)

        def sequence_421(n, i):
            if i == 0:
                return 4
            if i == 1:
                return 2
            return 1

        def sequence_geometric(n,i,c):
            return (n*n)/(n+c*i)

        def sequence_arithmetic(n,i,c):
            return n-(c*i)

        def sequence_gamix(n,i):
            return min(sequence_geometric(n,i,2),sequence_arithmetic(n,i,1))

        def sequence_gamix_frac(n,i,c):
            return c * (float(sequence_gamix(n,i)) / n)

        strengths = [int(sequence_gamix(len(electionObj["choices"]),i)) for i in range(len(electionObj["choices"]))]
        standings = [0]*len(electionObj["choices"])
        for ballot in electionObj["ballots"]:
            for vote_i in range(len(electionObj["ballots"][ballot])):
                standings[electionObj["ballots"][ballot][vote_i]] += strengths[vote_i]

        if isClosed:
            await electionObj["ballotMessage"].edit(content=self.constructBallotMessage(electionObj["text"], electionObj["choices"], electionObj["emoji"], "*This poll is now closed!*"))

        ballotsOutputString = self.constructRankChoiceResultBallotsMessage(electionObj["text"], electionObj["choices"], electionObj["emoji"], standings, electionObj["ballots"], electionObj["names"], isClosed)
        standingsOutputString = self.constructRankChoiceResultStandingsMessage(electionObj["text"], electionObj["choices"], electionObj["emoji"], standings, electionObj["ballots"], electionObj["names"], isClosed)
        await electionObj["resultBallotsMessage"].edit(content=ballotsOutputString)
        await electionObj["resultStandingsMessage"].edit(content=standingsOutputString)
        if isClosed:
            del self.elections[reactionPayload.message_id] 
    
    def constructBallotMessage(self, referendum, choices, emoji, helpString):
        output = "**__Referendum:__** {}\n".format(referendum)
        output += "\n**__Choices__**\n"
        for i in range(len(choices)):
            output += "{} {}\n".format(emoji[i], choices[i])

        output += "\n" + helpString

        return output

    #
    # referendum: string          referendum
    # choices: []string           choices, ordered
    # emoji: []emoji              emoji ordered by choices
    # standings: []int            vote counts, ordered by choices
    # ballots: {userId: []int}    vote orders, per user
    # names: {userId: []string}   usernames, per user
    # isClosed: bool
    #
    def constructRankChoiceResultBallotsMessage(self, referendum, choices, emoji, standings, ballots, names, isClosed=False):
        # Determine padding information for Ballots
        longestNameLength = 0
        for name in names.values():
            if len(name) > longestNameLength:
                longestNameLength = len(name)
        voteListPaddings = {}
        for userId, name in names.items():
            voteListPaddings[userId] = " "*(longestNameLength - len(name))

        output = self.ZERO_WIDTH_SPACE + "\n**__Ballots__**\n"
        if len(ballots) > 0:
            for userId, votes in ballots.items():
                if len(votes) == 0:
                    continue
                voteListString = ""
                for i, vote in enumerate(votes):
                    voteListString += "**{}.** {} ".format(i + 1, emoji[vote])
                output += "`{}{}` {}\n".format(names[userId], voteListPaddings[userId], voteListString)
        else:
            output += "*No ballots have been cast!*\n"
        return output

    #
    # referendum: string          referendum
    # choices: []string           choices, ordered
    # emoji: []emoji              emoji ordered by choices
    # standings: []int            vote counts, ordered by choices
    # ballots: {userId: []int}    vote orders, per user
    # names: {userId: []string}   usernames, per user
    # isClosed: bool
    #
    def constructRankChoiceResultStandingsMessage(self, referendum, choices, emoji, standings, ballots, names, isClosed=False):
        MAX_EMOJI_PER_MESSAGE = 199
        MAX_BAR_LENGTH = 12
        output = self.ZERO_WIDTH_SPACE + "\n**__Standings__**\n"

        # Determine padding information for Standings
        longestStandingLength = 0
        largestStandingValue = 0
        currentLeaders = []
        for i, standing in enumerate(standings):
            if len(str(standing)) > longestStandingLength:
                longestStandingLength = len(str(standing))
            if standing > largestStandingValue:
                largestStandingValue = standing
                currentLeaders = [emoji[i] + " " + choices[i]]
            elif standing == largestStandingValue:
                currentLeaders.append(emoji[i] + " " + choices[i])
        standingsPaddings = {}
        for i in range(len(standings)):
            standingsPaddings[i] = " "*(longestStandingLength - len(str(standings[i])))

        # Determine how many "elements"/"emoji" from maximum are consumed by static labels
        maxEmojiBufferCount = 4 # bold for "Standings" + 2 ballot emoji + italics for "Thank you"
        if isClosed:
            maxEmojiBufferCount = maxEmojiBufferCount + 2 * len(currentLeaders) # emoji and bold for each leader

        # Determine proportion information for standings
        standingsProportions = {}
        for i in range(len(standings)):
            standingsProportions[i] = 1
            if largestStandingValue > 0:
                standingsProportions[i] = float(standings[i]) / float(largestStandingValue)

        if len(standings) > 0:
            standingEmojiCounts = []
            totalEmojiCount = 999999999999999 # sum of standingEmojiCounts
            currentBarLength = MAX_BAR_LENGTH # decremented per iteration of while loop
            # Determine the number of emoji per bar, scaling the bar lengths down until we are sure they will all fit in the limit
            while totalEmojiCount > (MAX_EMOJI_PER_MESSAGE - maxEmojiBufferCount):
                standingEmojiCounts = []
                totalEmojiCount = 0
                for i in range(len(standings)):
                    numEmoji = 0
                    if largestStandingValue > 0 and largestStandingValue <= currentBarLength:
                        numEmoji = standings[i]
                    elif largestStandingValue > currentBarLength:
                        numEmoji = int(math.floor(currentBarLength * standingsProportions[i]))
                    if numEmoji == 0 and standings[i] > 0:
                        numEmoji = 1
                    standingEmojiCounts.append(numEmoji)
                    totalEmojiCount = totalEmojiCount + numEmoji
                currentBarLength = currentBarLength - 1
            
            for i in range(len(standings)):
                output += "{} `{}{}` {}\n".format(emoji[i], standingsPaddings[i], standings[i], (emoji[i]+self.ZERO_WIDTH_SPACE)*standingEmojiCounts[i])
        else:
            output += "*No ballots have been cast!*\n"
        if isClosed:
            leaderString = "**{}** is the victor!".format(currentLeaders[0])
            if len(currentLeaders) == 2:
                leaderString = "**{}** and **{}** are the victors!".format(currentLeaders[0], currentLeaders[1])
            if len(currentLeaders) > 2:
                leaderString = ""
                for leader in currentLeaders[:-1]:
                    leaderString += "**{}**, ".format(leader)
                leaderString += "and **{}** are the victors!".format(currentLeaders[-1])

            output += "\n🗳️ *The polls have closed, and {}* 🗳️".format(leaderString)
        else:
            output += "\n🗳️ *Thank you for taking part in the democratic process!* 🗳️"
        return output

    async def on_raw_reaction_add(self, payload):
        await super().on_raw_reaction_add(payload)

        if payload.user_id != self.client.user.id and payload.message_id in self.elections:
            if payload.emoji.name in self.CANCEL_EMOJI and payload.user_id == self.elections[payload.message_id]["ownerId"]:
                await self.updateRankVote(payload, True)
            else:
                await self.updateRankVote(payload, False)

    async def on_raw_reaction_remove(self, payload):
        await super().on_raw_reaction_remove(payload)
        if payload.user_id != self.client.user.id and payload.message_id in self.elections:
            await self.updateRankVote(payload, False)

    ###################
    #     Startup     #
    ###################

    def __init__(self, prefix="!", greeting="Hello", farewell="Goodbye"):
        super().__init__(prefix, greeting, farewell)


        # self.elections[message.id] = {
        #     "ownerId": string,
        #     "ballotMessage": message,
        #     "resultBallotsMessage": message,
        #     "resultStandingsMessage": message,
        #     "text": string,
        #     "choices": []string,
        #     "emoji": []emoji,
        #     "ballots": {userId: string},
        #     "names": {userId: string}
        # }
        self.elections = {}

        self.addCommand('vote', self.callSimpleVote, lambda x: True, "Call a vote", "Who is the best Star Trek captain? Kirk, Picard, Janeway")
        self.addCommand('rankvote', self.callRankVote, lambda x: True, "Call a rank choice vote", "Who should be captain of our starship? Kirk, Picard, Janeway")