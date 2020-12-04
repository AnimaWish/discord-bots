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
        #"letters": ["🇦","🇧","🇨","🇩","🇪","🇫","🇬","🇭","🇮","🇯","🇰","🇱","🇲","🇳","🇴","🇵","🇶","🇷","🇸","🇹","🇺","🇻","🇼","🇽","🇾","🇿"],
        "mammals": ["🐶","🐱","🐭","🐹","🐰","🦊","🐻","🐼","🐨","🐯","🦁","🐮","🐷","🐵","🐺","🐗","🐴",], 
        "fish": ["🐙","🦑","🦀","🐡","🐠","🐟","🐬","🐳","🐋","🦈","🐊","🐚","🦐","🦞"], 
        "bugs": ["🐝","🐛","🦋","🐌","🐞","🦟","🦗","🦂",],
        "plants": ["🌵","🌲","🌴","🍁","🍄","💐","🌹","🌻","🌳"],
        "fruit": ["🍎","🍐","🍊","🍋","🍌","🍉","🍇","🍓","🍈","🍒","🍑","🥭","🍍","🥥","🥝",],
        "vegetables": ["🍅","🥑","🥦","🥒","🌶","🌽","🥕","🧅","🥔",],
        "junkfood": ["🥨","🧀","🥓","🥞","🧇","🍗","🌭","🍔","🍟","🍕","🥪","🌮","🍝","🎂","🍭","🍫","🍿","🍩","🍪",],
        "drinks": ["🍺","🥂","🍷","🥃","🍸","🍹",],
        "sports": ["⚽", "🏀","🏈","⚾","🎾","🏐","🏉","🥏","🎱","🏓","🏸","🏒","🏏",],
        "instruments": ["🎹","🥁","🎷","🎺","🎸","🪕","🎻","🎤",],
        "vehicles": ["🚗","🚕","🚌","🏎","🚓","🚑","🚒","🚛","🚜","🚲","🛵","🚂","✈️","🚀","🛸","🚁","🚤","⛵️",],
        "misc": ["🔫","🧲","💣","🔪","🚬","⚰️","🔮","🔬","💊","💉","🧬","🦠","🌡","🧸","🎁","💿","⏰","🧯","💎",], 
    }

    async def parseVote(self, message, params):
        ballotPattern = "^([^\?]+\?)\s*(.+)$"

        ballotMatch = re.match(ballotPattern, params)

        if ballotMatch == None:
            await message.channel.send("I couldn't read your referendum. It should look like this: `!vote An Important Question? Choice A, Choice B, Choice C`. Remember the question mark and the commas, punctuation is important for robots!")
            return

        referendum = ballotMatch.group(1)
        choices = ballotMatch.group(2).split(",")[:20]

        validEmojiSets = []
        for key, emojiSet in SimpleVoteBot.EMOJI_SETS.items():
            if len(emojiSet) >= len(choices):
                validEmojiSets.append(key)

        emojiSetKey = random.choice(validEmojiSets)
        emojiMap = SimpleVoteBot.EMOJI_SETS[emojiSetKey][:len(choices)]
        if emojiSetKey != "letters":
            random.shuffle(emojiMap)

        return (referendum, choices, emojiMap)

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

        def constructBallotMessage(text, choices, emoji):
            ballotMessage = "__**Referendum:**__ {}\n\n__**Choices**__".format(ballotText)
            for i, choice in enumerate(choices):
                ballotMessage = "{}\n{} {}".format(ballotMessage, emoji[i], choice.strip())

            ballotMessage = ballotMessage + "\n\n*Click an emoji below to vote! You can see how people voted by clicking \"Reactions\" in the menu on this message!*"

            return ballotMessage

        messageText = constructBallotMessage(ballotText, choices, emoji)

        postedMessage = await message.channel.send(messageText)
        await self.populateVoteEmoji(postedMessage, emoji)


    async def callRankVote(self, message, params):
        referendum, choices, emoji = await self.parseVote(message, params)

        text = self.constructRankChoiceMessage(referendum, choices, emoji, [], {}, {})
        postedMessage = await message.channel.send(text)

        self.elections[postedMessage.id] = {
            "message": postedMessage,
            "text": referendum,
            "choices": choices,
            "emoji": emoji,
            "ballots": {},
            "names": {}
        }

        await self.populateVoteEmoji(postedMessage, emoji)

    async def updateRankVote(self, reactionPayload, isClosed=False):
        electionObj = self.elections[reactionPayload.message_id]

        newVote = -1
        for i in range(len(electionObj["emoji"])):
            if electionObj["emoji"][i] == reactionPayload.emoji.name:
                newVote = i
                break

        if newVote == -1:
            return

        if reactionPayload.event_type == "REACTION_ADD":
            if reactionPayload.user_id not in electionObj["names"]:
                electionObj["names"][reactionPayload.user_id] = reactionPayload.member.nick or reactionPayload.member.name
                electionObj["ballots"][reactionPayload.user_id] = []
            electionObj["ballots"][reactionPayload.user_id].append(newVote)
        else:
            if reactionPayload.user_id in electionObj["names"]:
                electionObj["ballots"][reactionPayload.user_id].remove(newVote)

        def generateExponentialVoteStrength():
            voteStrengths = [0]*len(electionObj["choices"])
            for ballot in electionObj["ballots"]:
                voteStrength = 2**(len(electionObj["choices"]) - 1)
                for i in range(len(voteStrength)):
                    voteStrengths[i] = voteStrength
                    voteStrength /= 2
            return voteStrengths

        def generate421VoteStrength():
            voteStrengths = [0]*len(electionObj["choices"])
            if len(electionObj["choices"]) == 1:
                return [1]
            elif len(electionObj["choices"]) == 2:
                return [2,1]
            else:
                voteStrengths[0] = 4
                voteStrengths[1] = 2
                for i in range(len(voteStrengths) - 2):
                    voteStrengths[i + 2] = 1
                return voteStrengths

        strengths = generate421VoteStrength()
        standings = [0]*len(electionObj["choices"])
        for ballot in electionObj["ballots"]:
            for vote_i in range(len(electionObj["ballots"][ballot])):
                standings[electionObj["ballots"][ballot][vote_i]] += strengths[vote_i]

        outputString = self.constructRankChoiceMessage(electionObj["text"], electionObj["choices"], electionObj["emoji"], standings, electionObj["ballots"], electionObj["names"], isClosed)
        await electionObj["message"].edit(content=outputString)

    #
    # referendum: string          referendum
    # choices: []string           choices, ordered
    # emoji: []emoji              emoji ordered by choices
    # standings: []int            vote counts, ordered by choices
    # ballots: {userId: []int}    vote orders, per user
    # names: {userId: []string}   usernames, per user
    # isClosed: bool
    #
    def constructRankChoiceMessage(self, referendum, choices, emoji, standings, ballots, names, isClosed=False):
        # Determine padding information for Ballots
        longestNameLength = 0
        for name in names.values():
            if len(name) > longestNameLength:
                longestNameLength = len(name)
        voteListPaddings = {}
        for userId, name in names.items():
            voteListPaddings[userId] = " "*(longestNameLength - len(name))

        # Determine padding information for Standings
        longestStandingLength = 0
        largestStandingValue = 0
        currentLeaders = []
        for i, standing in enumerate(standings):
            if len(str(standing)) > longestStandingLength:
                longestStandingLength = len(str(standing))
            if standing > largestStandingValue:
                largestStandingValue = standing
                currentLeaders = [i]
            elif standing == largestStandingValue:
                currentLeaders.append(i)
        standingsPaddings = {}
        for i in range(len(standings)):
            standingsPaddings[i] = " "*(longestStandingLength - len(str(standings[i])))

        # Determine proportion information for standings
        standingsProportions = {}
        for i in range(len(standings)):
            standingsProportions[i] = 1
            if largestStandingValue > 0:
                standingsProportions[i] = float(standings[i]) / float(largestStandingValue)

        output = "**__Referendum:__** {}\n".format(referendum)
        output += "\n**__Choices__**\n"
        for i in range(len(choices)):
            output += "{} {}\n".format(emoji[i], choices[i])
        output += "\n**__Ballots__**\n"
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
        output += "\n**__Standings__**\n"
        if len(standings) > 0:
            for i in range(len(standings)):
                numEmoji = 0
                if largestStandingValue > 0:
                    numEmoji = int(math.floor(12 * standingsProportions[i]))
                if numEmoji == 0 and standings[i] > 0:
                    numEmoji = 1
                output += "{} `{}{}` {}\n".format(emoji[i], standingsPaddings[i], standings[i], emoji[i]*numEmoji)
        else:
            output += "*No ballots have been cast!*\n"
        if isClosed:
            leaderString = "**{}** is the victor!".format(currentLeaders[0])
            if len(currentLeaders) == 2:
                leaderString = "**{}** and **{}** are the victors!".format(currentLeaders[0], currentLeaders[1])
            if len(currentLeaders) > 2:
                leaderString = ""
                for leader in currentLeaders[:-1]:
                    leaderString += "**{}**,".format(leader)
                leaderString += "and **{}** are the victors!".format(currentLeaders[-1])

            output += "\nThe polls have closed, and {}".format(leaderString)
        else:
            output += "\n*Click emoji in order from favorite to least favorite! Remember to double check your ballot!*"
        return output

    async def on_raw_reaction_add(self, payload):
        await super().on_raw_reaction_add(payload)

        if payload.user_id != self.client.user.id and payload.message_id in self.elections:
            await self.updateRankVote(payload, False)

    async def on_raw_reaction_remove(self, payload):
        await super().on_raw_reaction_remove(payload)
        if payload.user_id != self.client.user.id and payload.message_id in self.elections:
            if payload.emoji.name == "🚫" and payload.user_id == self.elections[payload.message_id]["message"].author.id:
                await self.updateRankVote(payload, True)
            else:
                await self.updateRankVote(payload, False)

    ###################
    #     Startup     #
    ###################

    def __init__(self, prefix="!", greeting="Hello", farewell="Goodbye"):
        super().__init__(prefix, greeting, farewell)


        # self.elections[message.id] = {
        #     "message": messageObj,
        #     "text": string,
        #     "choices": []string,
        #     "emoji": []emoji,
        #     "ballots": {userId: string},
        #     "names": {userId: string}
        # }
        self.elections = {}

        self.addCommand('vote', self.callSimpleVote, lambda x: True, "Call a vote", "Who is the best Star Trek captain? Kirk, Picard, Janeway")
        self.addCommand('rankvote', self.callRankVote, lambda x: True, "Call a rank choice vote", "Who should be captain of our starship? Kirk, Picard, Janeway")