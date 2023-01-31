import discord
import math, random
import re
import traceback
from datetime import datetime, timedelta
import pickle, json, csv, os

from .generic import DiscordBot

from discord.ext import commands 
from discord import app_commands

class VoteBot(DiscordBot):

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
    REASSIGNED_VOTE_EMOJI = "⬜"
    SAVE_EMOJI = ["🖨", "💾"]
    REFRESH_EMOJI = ["🔄", "↻", "🔃", "🔁"]





    async def parseVote(self, message, params):
        ballotPattern = "^([^\?]+\?)\s*(.+)$"

        ballotMatch = re.match(ballotPattern, params)

        if ballotMatch == None:
            await message.channel.send("I couldn't read your referendum. It should look like this: `!vote An Important Question? Choice A, Choice B, Choice C`. Remember the question mark and the commas, punctuation is important for robots!")
            return

        referendum = ballotMatch.group(1)
        choices = [a.strip() for a in ballotMatch.group(2).split(",")[:20]]

        validEmojiSets = []
        for key, emojiSet in VoteBot.EMOJI_SETS.items():
            if len(emojiSet) >= len(choices):
                validEmojiSets.append(key)

        emojiSetKey = random.choice(validEmojiSets)
        emojiMap = VoteBot.EMOJI_SETS[emojiSetKey]
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

        messageText = self.constructChoicesMessage(ballotText, choices, emoji, "You can see how people voted by clicking \"Reactions\" in the menu on this message!*")

        postedMessage = await message.channel.send(messageText)
        await self.populateVoteEmoji(postedMessage, emoji)


    async def voteRunoff(self, interaction: discord.Interaction):
        pass

    async def callRankVote(self, message, params):
        print("a")
        referendum, choices, emoji = await self.parseVote(message, params)

        text = self.constructChoicesMessage(referendum, choices, emoji, "*Click emoji in order from favorite to least favorite! Remember to double check your ballot!*")
        choiceMessage = await message.channel.send(text)

        text2 = self.constructBallotsMessage(referendum, choices, emoji, [], {}, {})
        ballotsMessage = await message.channel.send(text2)

        text3 = self.constructStandingsMessage_InstantRunoff(referendum, choices, emoji, [], {}, {})
        resultsMessage = await message.channel.send(text3)

        if message.guild.id not in self.elections:
            self.elections[choiceMessage.guild.id] = {}
        self.elections[choiceMessage.guild.id][choiceMessage.id] = {
            "guildID": choiceMessage.guild.id,
            "messageID": choiceMessage.id,
            "channelID": choiceMessage.channel.id,
            "ownerID": message.author.id,
            "choicesMessage": choiceMessage,
            "ballotsMessage": ballotsMessage,
            "resultsMessage": resultsMessage,
            "lastInteraction": datetime.now(),
            "text": referendum,
            "choices": choices,
            "emoji": emoji,
            "ballots": {},
            "names": {},
            "isInstantRunoff": True
        }

        await self.populateVoteEmoji(choiceMessage, emoji)

        await self.cleanupElections() # marshals this election as a byproduct

    
    def constructChoicesMessage(self, referendum, choices, emoji, helpString):
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
    def constructBallotsMessage(self, referendum, choices, emoji, standings, ballots, names, isClosed=False):
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

    def getVoteFromEmoji(self, electionObj, emoji):
        emojiName = emoji
        if not isinstance(emoji,str):
            emojiName = emoji.name 

        for i in range(len(electionObj["emoji"])):
            if electionObj["emoji"][i] == emojiName:
                return i
        return -1

    async def updateRankVote(self, reactionPayload):
        if reactionPayload.guild_id not in self.elections or reactionPayload.message_id not in self.elections[reactionPayload.guild_id] or reactionPayload.user_id == self.user.id:
            return

        electionObj = self.elections[reactionPayload.guild_id][reactionPayload.message_id]
        electionObj["lastInteraction"] = datetime.now()

        # Determine if it's a control emoji
        isClosed = False
        if reactionPayload.user_id == electionObj["ownerID"]:
            if reactionPayload.emoji.name in self.CANCEL_EMOJI:
                isClosed = True
            elif reactionPayload.emoji.name in self.REFRESH_EMOJI:
                print("swapski")
                electionObj["isInstantRunoff"] = not electionObj["isInstantRunoff"]

        # Determine what vote was cast
        newVote = self.getVoteFromEmoji(electionObj, reactionPayload.emoji)

        # Associate vote with a user
        if newVote != -1:
            if reactionPayload.event_type == "REACTION_ADD":
                if reactionPayload.user_id not in electionObj["names"]:
                    electionObj["names"][reactionPayload.user_id] = reactionPayload.member.nick or reactionPayload.member.name
                    electionObj["ballots"][reactionPayload.user_id] = []
                electionObj["ballots"][reactionPayload.user_id].append(newVote)
            else:
                if reactionPayload.user_id in electionObj["names"]:
                    electionObj["ballots"][reactionPayload.user_id].remove(newVote)

        await self.regenerateStandings(electionObj, isClosed)

        self.marshalElectionState()


    async def regenerateStandings(self, electionObj, isClosed=False):
        if electionObj["isInstantRunoff"]:
            await self.regenerateStandings_InstantRunoff(electionObj, isClosed)
        else:
            await self.regenerateStandings_WeightedVote(electionObj, isClosed)

        if isClosed:
            del self.elections[electionObj.guildID][electionObj.messageID] 

    async def regenerateStandings_InstantRunoff(self, electionObj, isClosed):
        # Count ballots
        majorityTarget = math.ceil(len(electionObj["ballots"])/2)
        majorityCandidates = [] # Winner(s)
        eliminatedCandidates = set()
        # for each candidate, show which canididate they got their instant-runoff votes from
        #
        # 1: A, B, C
        # 2: B, C, A
        # 3: C, B 
        # 4: C, A
        # 5: B
        # 6: A
        # 7: C
        # 8: B, A
        #
        # A:2,B:3,C:3
        # B:4,C:3, X:1
        #
        #  + A B C
        #  A 1 0 0 = 1
        #  B 1 3 0 = 4
        #  C 0 0 3 = 3
        #
        voteAssignments = []
        while len(majorityCandidates) == 0 and len(eliminatedCandidates) < len(electionObj["choices"]) - 1:
            print("eliminatedCandidates: #", len(eliminatedCandidates), eliminatedCandidates)
            majorityCandidates = []
            voteAssignments = [[0]*len(electionObj["choices"]) for i in range(len(electionObj["choices"]))]

            standings = [0]*len(electionObj["choices"])
            nonzeroStandingsSet = set() # candidates that were ever first-picks
            totalCounts = [0]*len(electionObj["choices"]) # total times a candidate was clicked
            for ballotUserID in electionObj["ballots"]:
                userBallot = electionObj["ballots"][ballotUserID]
                for ballot_i in range(len(userBallot)):
                    totalCounts[userBallot[ballot_i]] += 1
                if len(userBallot) > 0:
                    firstChoice = userBallot[0]
                    finalChoice = firstChoice
                    choice_i = 0
                    while (finalChoice in eliminatedCandidates) and (choice_i < len(userBallot)):
                        finalChoice = userBallot[choice_i]
                        choice_i += 1

                    if finalChoice != -1 and finalChoice not in eliminatedCandidates:
                        standings[finalChoice] += 1
                        nonzeroStandingsSet.add(finalChoice)
                        if standings[finalChoice] >= majorityTarget:
                            majorityCandidates.append(finalChoice)

                    print(" ballotUserID:", ballotUserID, " userBallot:", userBallot, "first:", firstChoice, "final:", finalChoice)
                    voteAssignments[finalChoice][firstChoice] += 1

            # Winner decided or dead tie
            if (len(majorityCandidates) == 1 and standings[majorityCandidates[0]] > majorityTarget) or (len(majorityCandidates) == 2 and (len(eliminatedCandidates) == len(electionObj["choices"]) - 2)):
                break

            nonzeroStandingsList = list(nonzeroStandingsSet)
            if len(nonzeroStandingsList) == 0:
                break

            nonzeroStandingsList.sort(key=lambda val: standings[val] + totalCounts[val]/(len(electionObj["ballots"])+1) )
            print("ELIMINATING: ", nonzeroStandingsList[0])
            eliminatedCandidates.add(nonzeroStandingsList[0])

        print("Vote Assignments:")
        for i in range(len(voteAssignments)):
            print(voteAssignments[i])

        if isClosed:
            await electionObj["choicesMessage"].edit(content=self.constructChoicesMessage(electionObj["text"], electionObj["choices"], electionObj["emoji"], "*This poll is now closed!*"))

        ballotsOutputString = self.constructBallotsMessage(electionObj["text"], electionObj["choices"], electionObj["emoji"], standings, electionObj["ballots"], electionObj["names"], isClosed)
        standingsOutputString = self.constructStandingsMessage_InstantRunoff(electionObj["text"], electionObj["choices"], electionObj["emoji"], voteAssignments, electionObj["ballots"], electionObj["names"], isClosed)
        await electionObj["ballotsMessage"].edit(content=ballotsOutputString)
        await electionObj["resultsMessage"].edit(content=standingsOutputString)


    #
    # referendum: string          referendum
    # choices: []string           choices, ordered
    # emoji: []emoji              emoji ordered by choices
    # voteAssignments: [][]int    vote counts, 2d array, first dimension is "final" vote, second dimension is "first" vote
    # ballots: {userId: []int}    vote orders, per user
    # names: {userId: []string}   usernames, per user
    # isClosed: bool
    #
    def constructStandingsMessage_InstantRunoff(self, referendum, choices, emoji, voteAssignments, ballots, names, isClosed=False):
        MAX_EMOJI_PER_MESSAGE = 196
        MAX_BAR_LENGTH = 12
        output = self.ZERO_WIDTH_SPACE + "\n**__Standings__**\n"

        reassignedVotes = [0]*len(voteAssignments) # "column sums" minus diagonal, the number of votes for a candidate that were applied to another candidate
        standings = [0]*len(voteAssignments) # "row sums", voteAssignments flattened to pure counts
        for i, firstChoiceArr in enumerate(voteAssignments):
            for j, count in enumerate(firstChoiceArr):
                standings[i] += count
                if i != j:
                    reassignedVotes[j] += count

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
            
            for i in range(len(voteAssignments)):
                numPureVotes = voteAssignments[i][i] # votes for this candidate that were not reassigned
                barString = (emoji[i]+self.ZERO_WIDTH_SPACE)*numPureVotes

                numReassignedVotes = reassignedVotes[i]
                barString += (self.REASSIGNED_VOTE_EMOJI+self.ZERO_WIDTH_SPACE)*numReassignedVotes

                for j, sourceVoteCount in enumerate(voteAssignments[i]):
                    if i != j:
                        barString += (emoji[j]+self.ZERO_WIDTH_SPACE)*sourceVoteCount

                output += "{} `{}{}` {}\n".format(emoji[i], standingsPaddings[i], standings[i], barString)


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


    async def regenerateStandings_WeightedVote(self, electionObj, isClosed=False):
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
            await electionObj["choicesMessage"].edit(content=self.constructChoicesMessage(electionObj["text"], electionObj["choices"], electionObj["emoji"], "*This poll is now closed!*"))

        ballotsOutputString = self.constructBallotsMessage(electionObj["text"], electionObj["choices"], electionObj["emoji"], standings, electionObj["ballots"], electionObj["names"], isClosed)
        standingsOutputString = self.constructStandingsMessage_WeightedChoice(electionObj["text"], electionObj["choices"], electionObj["emoji"], standings, electionObj["ballots"], electionObj["names"], isClosed)
        await electionObj["ballotsMessage"].edit(content=ballotsOutputString)
        await electionObj["resultsMessage"].edit(content=standingsOutputString)


    #
    # referendum: string          referendum
    # choices: []string           choices, ordered
    # emoji: []emoji              emoji ordered by choices
    # standings: []int            vote counts, ordered by choices
    # ballots: {userId: []int}    vote orders, per user
    # names: {userId: []string}   usernames, per user
    # isClosed: bool
    #
    def constructStandingsMessage_WeightedChoice(self, referendum, choices, emoji, standings, ballots, names, isClosed=False):
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



    async def cleanupElections(self):
        deletedSomething = False
        timeDeltaThreshold = timedelta(seconds=10)#timedelta(weeks=4)
        for guildID, guildElectionsMap in self.elections.items():
            for messageID, electionObj in guildElectionsMap.items():
                delta = datetime.now() - electionObj["lastInteraction"]
                if delta > timeDeltaThreshold:
                    print("Automatically closed election: {}".format(messageID))
                    await self.regenerateStandings(electionObj, True)
                    deletedSomething = True

        self.marshalElectionState()


    def marshalElectionState(self):
        if not os.path.isfile(self.electionsDataFilePath):
            os.makedirs(os.path.dirname(self.electionsDataFilePath), exist_ok=True)

        outputElections = {}
        for guildID, guildElectionsMap in self.elections.items():
            outputElections[guildID] = {}
            for messageID, electionObj in guildElectionsMap.items():
                outputElections[guildID][messageID] = {
                    "guildID":                  electionObj["guildID"],
                    "messageID":                electionObj["messageID"],
                    "channelID":                electionObj["channelID"],
                    "ownerID":                  electionObj["ownerID"],
                    "choicesMessageID":         electionObj["choicesMessage"].id,
                    "ballotsMessageID":         electionObj["ballotsMessage"].id,
                    "resultsMessageID":         electionObj["resultsMessage"].id,
                    "lastInteraction":          electionObj["lastInteraction"],
                    "text":                     electionObj["text"],
                    "choices":                  electionObj["choices"],
                    "emoji":                    electionObj["emoji"],
                    "ballots":                  electionObj["ballots"],
                    "names":                    electionObj["names"],
                    "isInstantRunoff":          electionObj["isInstantRunoff"]
                }

        with open(self.electionsDataFilePath, 'wb') as f:
            pickle.dump(outputElections, f, pickle.HIGHEST_PROTOCOL)


    # if votes were changed while bot was offline, resolve the changes 
    async def syncBallotState(self, electionObj):
        userMap = {} #{userID: user} 
        userEmojiMap = {} # {userID: [reactionEmoji, ...]}
        for reaction in electionObj["choicesMessage"].reactions:
            async for user in reaction.users():
                if user.id != self.user.id:
                    if user.id not in userEmojiMap:
                        userMap[user.id] = user
                        userEmojiMap[user.id] = []
                    userEmojiMap[user.id].append(reaction.emoji)

        # Clear added reactions because we don't know what order they came in
        # Update ballot for removed reactions
        reactionsToRemove = [] # [[emoji, user], ...]
        ballotWasUpdated = False
        for userID, emojiList in userEmojiMap.items():
            if userID in electionObj["ballots"]:
                ballot = electionObj["ballots"][userID]
                seenChoices = set()
                for emoji in emojiList:
                    choice = self.getVoteFromEmoji(electionObj, emoji)
                    if choice in ballot:
                        seenChoices.add(choice)
                    else:
                        reactionsToRemove.append([emoji,userMap[userID]])

                for choice in reversed(ballot):
                    if choice not in seenChoices:
                        ballotWasUpdated = True
                        ballot.remove(choice)

            else: # new voter added reactions while bot was offline, clear their reactions
                for emoji in emojiList:
                    reactionsToRemove.append([emoji,userMap[userID]])

        for tup in reactionsToRemove:
            await electionObj["choicesMessage"].remove_reaction(tup[0], tup[1])

        if ballotWasUpdated:
            await self.regenerateStandings(electionObj)



    async def unmarshalElectionState(self):
        try:
            if os.path.isfile(self.electionsDataFilePath):
                try:
                    importedElections = pickle.load(open(self.electionsDataFilePath, "rb"))
                    print("Unmarshaled {} elections. Fetching messages...".format(len(importedElections)))
                    successCount = 0
                    for guildID, guildElectionsMap in importedElections.items():
                        try: 
                            guild = await self.fetch_guild(guildID, with_counts=False)
                            # Collect channels in guild to fetch
                            channelMessagesIDMap = {} # {channelID: [messageID, messageID, ...]}
                            for messageID, electionObj in guildElectionsMap.items():
                                if electionObj["channelID"] not in channelMessagesIDMap:
                                    channelMessagesIDMap[electionObj["channelID"]] = []
                                channelMessagesIDMap[electionObj["channelID"]].append(messageID)

                            for channelID, messageIDList in channelMessagesIDMap.items():
                                try:
                                    channel = await guild.fetch_channel(channelID)
                                    for messageID in messageIDList:
                                        electionObj = importedElections[guildID][messageID]
                                        electionObj["choicesMessage"] = await channel.fetch_message(electionObj["choicesMessageID"])
                                        electionObj["ballotsMessage"] = await channel.fetch_message(electionObj["ballotsMessageID"])
                                        electionObj["resultsMessage"] = await channel.fetch_message(electionObj["resultsMessageID"])
                                        electionObj["isInstantRunoff"] = True # Easier with syncing logic to just discard this
                                        successCount += 1
                                except Exception as e:
                                    print("Failed to fetch ballot messages for choicesMessage {}: {}".format(electionObj["choicesMessageID"], e))
                                    print(traceback.format_exc())
                                    del importedElections[guildID][messageID]
                        except Exception as e:
                            print("Failed to fetch guild for guildID {}: {}".format(guildID, e))
                            print(traceback.format_exc())

                    print("Fetched messages for {} elections. Syncing ballots...".format(successCount))
                    try:
                        for guildID, guildElectionsMap in importedElections.items():
                            for messageID, electionObj in guildElectionsMap.items():
                                await self.syncBallotState(electionObj)
                        print("Synced ballot states. Unmarshaling complete.")
                    except Exception as e:
                        print("Failed to sync ballot states: {}".format(e))
                        print(traceback.format_exc())

                    self.elections = importedElections
                except Exception as e:
                    print("Failed to unpickle election file: {}".format(e))
                    print(traceback.format_exc())

            else:
                print("No elections file to import.")
                self.elections = {} # see init
        except Exception as e:
            print("Error unmarshaling election state: {}".format(e)) 
            print(traceback.format_exc())

    async def on_ready(self):
        await super().on_ready()
        await self.unmarshalElectionState()

    async def on_raw_reaction_add(self, payload):
        try:
            await super().on_raw_reaction_add(payload)
            await self.updateRankVote(payload)
        except Exception as e:
            print("ERROR adding reaction: {}".format(e))
            print(traceback.format_exc())

    async def on_raw_reaction_remove(self, payload):
        try:
            await super().on_raw_reaction_remove(payload)
            await self.updateRankVote(payload)
        except Exception as e:
            print("ERROR removing reaction: {}".format(e))
            print(traceback.format_exc())

    def __init__(self, prefix="!", greeting="Hello", farewell="Goodbye", *, intents, **options):
        super().__init__(prefix, greeting, farewell, intents=intents, options=options)

        self.electionsDataFilePath = "storage/{}/electionsData.pickle".format(self.getName())

        # self.elections[guild.id][message.id] = {
        #     "ownerID": string,
        #     "choicesMessage": message,
        #     "ballotsMessage": message,
        #     "resultsMessage": message,
        #     "lastInteraction": datetime,
        #     "text": string,
        #     "choices": []string,
        #     "emoji": []emoji,
        #     "ballots": {userId: string},
        #     "names": {userId: string},
        #     "isInstantRunoff": bool,
        # }
        self.elections = {}

        try:
            self.tree.add_command(app_commands.Command(
                name="vote",
                description="Create an instant-runoff vote",
                callback=self.voteRunoff,
            ))
        except Exception as e:
            print(f'caught {type(e)}: ', e)
        # self.addCommand('meats', self.meats, lambda x: True)


        self.addCommand('vote', self.callSimpleVote, lambda x: True, "Call a vote", "Who is the best Star Trek captain? Kirk, Picard, Janeway")
        self.addCommand('rankvote', self.callRankVote, lambda x: True, "Call a rank choice vote", "Who should be captain of our starship? Kirk, Picard, Janeway")