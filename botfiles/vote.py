import discord
import asyncio
import random
import urllib.request
import re
import os, io
import threading
import datetime, time

from .generic import DiscordBot

class VoteBot(DiscordBot):
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

            if userID in self.votes:
                for voteIndex, existingChoiceIndex in enumerate(self.votes[userID]):
                    if existingChoiceIndex == removedChoiceIndex:
                        self.votes[userID].pop(voteIndex)
                        return

    # !callvote Send a manned mission to mars. [yes, no, give money to the rich]
    async def callVote(self, message, params):
        for messageID in self.currentReferendums:
            if self.currentReferendums[messageID].initiatorID == message.author.id and not self.currentReferendums[messageID].closed:
                await message.channel.send("You already have a referendum on the floor! Type `{}` to resolve the vote!".format(self.buildCommandHint(self.commandMap['elect'])))
                return

        ballotPattern = "([^\?]+\?)\s*(\d*)"
        choicePattern = "[,;\s]*\"([^\"]+)\""

        # Parse parameters
        ballotMatch = re.match(ballotPattern, params) # !callvote Elect a letter [a, b, c] numvotes
        choicesMatch = re.findall(choicePattern, params)
        if ballotMatch == None:
            ballotText = None
        else:
            ballotText = ballotMatch.group(1)
            choices = choicesMatch

            try:
                maxVoteCount = int(ballotMatch.group(2))
                if maxVoteCount < 1 or maxVoteCount > len(choices):
                    maxVoteCount = len(choices)
            except:
                maxVoteCount = len(choices)

        if ballotText is None:
            helpfulMessage = "You need text for your referendum! Try `{}`".format(self.buildCommandHint(self.commandMap['callvote']))
            if params != "":
                helpfulMessage += "\n*Psst, the question mark `?` is important for me to be able to read your referendum!*"

            await message.channel.send(helpfulMessage)
            return
        if len(choices) == 0:
            helpfulMessage = "You need choices for your referendum! Try `{}`".format(self.buildCommandHint(self.commandMap['callvote']))
            if len(re.sub(ballotPattern, "", params)) != 0:
                helpfulMessage += "\n*Psst, Remember to surround your choices with `\"quotes\"`!*"
            await message.channel.send(helpfulMessage)
            return

        referendum = self.Referendum(message.author.id, ballotText, choices, maxVoteCount)

        def constructBallotMessage(referendum):
            ballotMessage = "__**Referendum:**__ {}\n\n__**Choices**__".format(referendum.text)
            for i, choice in enumerate(referendum.choices):
                ballotMessage = "{}\n{} {}".format(ballotMessage, referendum.emojiMap[i], choice)

            helpMessage = ""
            if maxVoteCount != len(choices):
                if maxVoteCount == 1:
                    helpMessage = " You have one vote: your MOST RECENT vote will be the one that is counted."
                else:
                    helpMessage = " You have {} votes: your MOST RECENT {} votes will be the ones that are counted.".format(referendum.maxVoteCount, referendum.maxVoteCount)

            ballotMessage = ballotMessage + "\n\n*Click an emoji below to vote!" + helpMessage + "*"

            return ballotMessage

        postedMessage = await message.channel.send(constructBallotMessage(referendum))

        self.currentReferendums[postedMessage.id] = referendum

        # Add the ballot options as reactions. If we get a Forbidden error, that means that people added extra reactions before the bot could finish adding them.
        # In that case, we're going to adjust the ballot to use their reactions as options.
        injectedReaction = False
        for i, choice in enumerate(referendum.choices):
            try:
                await postedMessage.add_reaction(referendum.emojiMap[i])
            except discord.errors.Forbidden:
                injectedReaction = True
                break

        if injectedReaction:
            updatedPostedMessage = await message.channel.get_message(postedMessage.id)
            for i, reaction in enumerate(updatedPostedMessage.reactions):
                referendum.emojiMap[i] = reaction.emoji

            await postedMessage.edit(content=constructBallotMessage(referendum))

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
                break
        if noReferendum:
            await message.channel.send("You don't have a referendum on the floor! Type `{}` to start a vote!".format(self.buildCommandHint(self.commandMap['callvote'])))
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
        resultMessageText = wrapperString + "\n\nRegarding the referendum, \"{}\", put forth by {}, the votes are in, and the winner is".format(referendum.text, message.guild.get_member(referendum.initiatorID).mention)
        resultsMessage = await message.channel.send(resultMessageText+ "\n\n" + wrapperString)

        # Pause for effect
        for i in range(3):
            time.sleep(.5)
            resultMessageText = resultMessageText + "."
            newMessage = resultMessageText + "\n\n" + wrapperString
            await resultsMessage.edit(content=newMessage)

        time.sleep(1)

        # Construct the winner announcement
        voteString = "vote"
        if largestTally > 1:
            voteString = "votes"

        tieVote = False
        winnerString = "{} \"{}\"".format(referendum.emojiMap[winnerIndices[0]], referendum.choices[winnerIndices[0]])
        if len(winnerIndices) > 1:
            tieVote = True
            for i, winner in enumerate(winnerIndices[1:]):
                nextWinner = "{} \"{}\"".format(referendum.emojiMap[winner], referendum.choices[winner])
                if i + 1 == len(winnerIndices) - 1:
                    winnerString = winnerString + " and " + nextWinner
                else:
                    winnerString = winnerString + ", " + nextWinner
            resultMessageText += " a tie between {}, with {} {} each!".format(winnerString, largestTally, voteString)
        elif len(winnerIndices) == 1:
            resultMessageText += " {}, with {} {}!".format(winnerString, largestTally, voteString)

        await resultsMessage.edit(content=resultMessageText + "\n\n" + wrapperString)

        self.currentReferendums.pop(referendumKey, None)


    ###################
    #     Events      #
    ###################

    async def on_reaction_add(self, reaction, user):
        await super().on_reaction_add(reaction, user)
        if user.id != self.client.user.id and reaction.message.author.id == self.client.user.id:
            if reaction.message.id in self.currentReferendums:
                self.currentReferendums[reaction.message.id].addVote(user.id, reaction.emoji)

    async def on_reaction_remove(self, reaction, user):
        await super().on_reaction_remove(reaction, user)
        if user.id != self.client.user.id and reaction.message.author.id == self.client.user.id:
            if reaction.message.id in self.currentReferendums:
                self.currentReferendums[reaction.message.id].removeVote(user.id, reaction.emoji)


    ###################
    #     Startup     #
    ###################

    def __init__(self, prefix="!", greeting="Hello", farewell="Goodbye"):
        super().__init__(prefix, "Peace be upon you.", "Passing into the Iris.")

        self.addCommand('callvote', self.callVote,    lambda x: True, "Call a vote", "Kirk or Picard? \"Sheridan\", \"Adama\", \"Skywalker\"")
        self.addCommand('elect',    self.resolveVote, lambda x: True, "Count votes and decide a winner!")
        self.currentReferendums = {} #currentReferendums[message.ID] = Referendum