import discord
import asyncio
import random, math
import urllib.request
import re
import os, io
import threading
import datetime, time

from .generic import DiscordBot

GAME_CHANNEL_NAME = "idle-game-zone"

class IdleGameBot(DiscordBot):
    class GameSession:
        class Player:
            def __init__(self, discordUserObject, importString=""):
                self.discordUserObject = discordUserObject

                if importString == "":
                    self.currencyTotal = {
                        "$": 0,
                    }

                    self.items = {
                        "ALLOWANCE":          1,
                        "ITEM_LEMON":         0,
                        "ITEM_MELON":         0,
                        "ITEM_MONEY_PRINTER": 0,
                    }

                    self.income = self.calculateBaseIncome()
                else:
                    pass #TODO import from string

            def updateItems(self, itemChanges):
                for itemKey in itemChanges:
                    self.items[itemKey] += itemChanges[itemKey]
                self.income = self.calculateBaseIncome()

            def calculateBaseIncome(self):
                incomeResult = {
                    "$": 0
                }

                incomeResult["$"] += self.items["ALLOWANCE"]
                incomeResult["$"] += self.items["ITEM_LEMON"]
                incomeResult["$"] += 5 * self.items["ITEM_MELON"]
                incomeResult["$"] += 50 * self.items["ITEM_MONEY_PRINTER"]

                return incomeResult

            # Remember that positive currencyTuples mean ADDING TO currencyTotal!
            def transact(self, currencyTuple):
                self.currencyTotal[currencyTuple[0]] += currencyTuple[1]


        KEY_TO_EMOJI_MAP = {
            "ITEM_LEMON":         "🍋",
            "ITEM_MELON":         "🍈",
            "ITEM_MONEY_PRINTER": "🖨️",
            "ITEM_BROKEN_HOUSE":  "🏚️",
            "NUMERAL_0": "0️⃣",
            "NUMERAL_1": "1️⃣",
            "NUMERAL_2": "2️⃣",
            "NUMERAL_3": "3️⃣",
            "NUMERAL_4": "4️⃣",
            "NUMERAL_5": "5️⃣",
            "NUMERAL_6": "6️⃣",
            "NUMERAL_7": "7️⃣",
            "NUMERAL_8": "8️⃣",
            "NUMERAL_9": "9️⃣",
            "BANK_STATUS_BULL": "🐄",
            "BANK_STATUS_CAMEL": "🐪",
        }

        EMOJI_TO_KEY_MAP = {
            "🍋": "ITEM_LEMON",
            "🍈": "ITEM_MELON",
            "🖨️": "ITEM_MONEY_PRINTER",
            "🏚️": "ITEM_HOUSE",
            "0️⃣": "NUMERAL_0",
            "1️⃣": "NUMERAL_1",
            "2️⃣": "NUMERAL_2",
            "3️⃣": "NUMERAL_3",
            "4️⃣": "NUMERAL_4",
            "5️⃣": "NUMERAL_5",
            "6️⃣": "NUMERAL_6",
            "7️⃣": "NUMERAL_7",
            "8️⃣": "NUMERAL_8",
            "9️⃣": "NUMERAL_9",
            "🐄": "BANK_STATUS_BULL",
            "🐪": "BANK_STATUS_CAMEL",
        }

        LOTTO_KEY_TO_NUM_MAP = {
            "NUMERAL_0": 0,
            "NUMERAL_1": 1,
            "NUMERAL_2": 2,
            "NUMERAL_3": 3,
            "NUMERAL_4": 4,
            "NUMERAL_5": 5,
            "NUMERAL_6": 6,
            "NUMERAL_7": 7,
            "NUMERAL_8": 8,
            "NUMERAL_9": 9
        }

        ITEM_COSTS = {
            "ITEM_LEMON": ["$", -100],
            "ITEM_MELON": ["$", -990],
            "ITEM_MONEY_PRINTER": ["$", -49000],
            "ITEM_BROKEN_HOUSE": ["$", -1000000],
        }

        ##################
        #### INITIALIZATION
        ##################

        def __init__(self, client, guild, gameChannel):
            self.client = client
            self.guild = guild
            self.channel = gameChannel # the game channel
            self.players = {} # maps discordUserIDs to Player objects
            self.buildingMessageObjects = {} # maps BLDG string constants to messages

            # Bank Properties
            self.bankMarketStatus = "BANK_STATUS_BULL" # toggles at regular intervals
            self.correctMarketUserIDs = [] # userIDs of players who have toggled the bull/camel emoji

            # Lottery Properties
            self.lotteryDrawTime = 0 #datetime.datetime
            self.todayLotteryNumbers = [0,0,0]
            self.yesterdayLotteryNumbers = [0,0,0]
            self.yesterdayLotteryWinners = [[],[],[]] # third, second, first place --- nested array of playerIDs
            self.yesterdayLotteryPrizePool = 0
            self.todayLotteryPrizePool = 0

            # Timing Properties
            self.counter = 0 # time keeper
            self.lastInteraction = datetime.datetime.now() # updated to now whenever there are reactions/messages in the game channel
            self.slumberLevel = 0 # tracks if the bot is "slumbering" (still running but less aggressively updating UI)
            self.eventCounters = {} # maps EVENT string constants to counters (these counters tick down, not up)
            self.eventMessages = {} # maps EVENT string constants to message objects

        async def initializeBuildings(self):
            # CONFIG PLACEHOLDER
            self.buildingMessageObjects["BLDG_CONFIG"] = await self.channel.send(":construction:")

            # BANK
            self.buildingMessageObjects["BLDG_BANK"] = await self.channel.send(self.generateBankMessage())
            await self.buildingMessageObjects["BLDG_BANK"].add_reaction(self.KEY_TO_EMOJI_MAP[self.bankMarketStatus])

            # SHOP 1
            self.buildingMessageObjects["BLDG_SHOP_1"] = await self.channel.send(self.generateShop1Message())
            await self.buildingMessageObjects["BLDG_SHOP_1"].add_reaction(self.KEY_TO_EMOJI_MAP["ITEM_LEMON"])
            await self.buildingMessageObjects["BLDG_SHOP_1"].add_reaction(self.KEY_TO_EMOJI_MAP["ITEM_MELON"])
            await self.buildingMessageObjects["BLDG_SHOP_1"].add_reaction(self.KEY_TO_EMOJI_MAP["ITEM_MONEY_PRINTER"])
            await self.buildingMessageObjects["BLDG_SHOP_1"].add_reaction(self.KEY_TO_EMOJI_MAP["ITEM_BROKEN_HOUSE"])

            # LOTTERY
            self.buildingMessageObjects["BLDG_LOTTERY"] = await self.channel.send(":construction:")
            await self.refreshLottery()

            # COMMIT CONFIG
            await self.buildingMessageObjects["BLDG_CONFIG"].edit(content=self.encodeState())

        async def refreshLottery(self):
            self.yesterdayLotteryNumbers = self.todayLotteryNumbers
            self.todayLotteryNumbers = self.drawLotteryNumbers()
            self.lotteryDrawTime = datetime.datetime.now() + datetime.timedelta(seconds=10) # TODO make sure this doesn't drift

            # determine prize pool
            dollarSum = 0
            for playerID in self.players:
                dollarSum += self.players[playerID].currencyTotal["$"]
            self.yesterdayLotteryPrizePool = self.todayLotteryPrizePool
            self.todayLotteryPrizePool = max(100000, int(dollarSum*.01))

            await self.buildingMessageObjects["BLDG_LOTTERY"].edit(content=self.generateLotteryMessage())
            await self.buildingMessageObjects["BLDG_LOTTERY"].clear_reactions()
            for item in self.LOTTO_KEY_TO_NUM_MAP:
                await self.buildingMessageObjects["BLDG_LOTTERY"].add_reaction(self.KEY_TO_EMOJI_MAP[item])

        # third, second, first prize
        def calculateLotteryPrizes(self, prizePool):
            return [int(prizePool * .11), int(prizePool * .22), int(prizePool * .66)]

        def drawLotteryNumbers(self):
            # select the 3 lotto numbers
            possibleLotteryNumbers = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
            lottoNumbers = []
            while len(lottoNumbers) < 3:
                lottoNumbers.append(possibleLotteryNumbers.pop(random.randrange(0, len(possibleLotteryNumbers))))
            lottoNumbers.sort()

            return lottoNumbers

        ##################
        #### GAME EVENT HANDLERS
        ##################

        async def onTick(self):
            # Determine the activity level of the bot
            tempSlumberLevel = 0
            SLUMBER_MINUTES_THRESHOLDS = [.5, 10, 1440]
            SLUMBER_LEVEL_UPDATE_RATES = [1, 5, 30, 600] #in seconds
            self.counter += 1
            lastInteractDelta = datetime.datetime.now() - self.lastInteraction
            for i in range(len(SLUMBER_MINUTES_THRESHOLDS)):
                if lastInteractDelta > datetime.timedelta(minutes=SLUMBER_MINUTES_THRESHOLDS[i]):
                    tempSlumberLevel = i + 1
            self.slumberLevel = tempSlumberLevel

            # PLAYER INCOME
            for userID in self.players:
                player = self.players[userID]
                income = player.income

                finalIncome = income["$"]
                if player.discordUserObject.id in self.correctMarketUserIDs:
                    finalIncome *= 1.25

                player.currencyTotal["$"] += math.ceil(finalIncome)

            # Update bank based off of activity level
            if self.counter % SLUMBER_LEVEL_UPDATE_RATES[self.slumberLevel] == 0: 
                await self.buildingMessageObjects["BLDG_BANK"].edit(content=self.generateBankMessage())

            # Update "save" file
            if self.counter % 60 == 0:
                await self.buildingMessageObjects["BLDG_CONFIG"].edit(content=self.encodeState())

            if self.counter % 10 == 0:#(60 * 30) == 0: 
                # Reset bank market status
                if self.bankMarketStatus == "BANK_STATUS_BULL":
                    self.bankMarketStatus = "BANK_STATUS_CAMEL"
                else:
                    self.bankMarketStatus = "BANK_STATUS_BULL"
                await self.buildingMessageObjects["BLDG_BANK"].clear_reactions()
                await self.buildingMessageObjects["BLDG_BANK"].add_reaction(self.KEY_TO_EMOJI_MAP[self.bankMarketStatus])
                self.correctMarketUserIDs = []
                await self.buildingMessageObjects["BLDG_BANK"].edit(content=self.generateBankMessage())

                # Check if it's lottery drawing time
                if datetime.datetime.now() > self.lotteryDrawTime:
                    print("Drawing lotto!")
                    playerLottoChoices = {} # maps integers 0-9 to lists of player IDs
                    self.buildingMessageObjects["BLDG_LOTTERY"] = await self.channel.fetch_message(self.buildingMessageObjects["BLDG_LOTTERY"].id) # need to update local message object to get reactions
                    for reaction in self.buildingMessageObjects["BLDG_LOTTERY"].reactions:
                        lottoNum = self.LOTTO_KEY_TO_NUM_MAP[self.EMOJI_TO_KEY_MAP[reaction.emoji]]
                        playerLottoChoices[lottoNum] = []
                        async for user in reaction.users():
                            if user.id != self.client.user.id:
                                playerLottoChoices[lottoNum].append(user.id)

                    print(playerLottoChoices)

                    # make sure everyone only gets 3 numbers
                    playerNumberCounts = {} # maps player IDs to counts of lottery numbers selected
                    for i in range(10):
                        for j in range(len(playerLottoChoices[i]), 0, -1): # range through each playerLottoChoices list backwards so we can pop from it safely
                            i_userIDs = j - 1
                            userID = playerLottoChoices[i][i_userIDs]
                            if userID not in playerNumberCounts:
                                playerNumberCounts[userID] = 0
                            if playerNumberCounts[userID] < 3: 
                                playerNumberCounts[userID] += 1
                            else: # TOO MANY CHOICES
                                playerNumberCounts[userID].pop(i_userIDs)

                    # Count correct guesses
                    lottoMatchCounts = {} # maps playerIDs to counts of correct guesses
                    for winningNumber in self.todayLotteryNumbers:
                        for userID in playerLottoChoices[winningNumber]:
                            if userID not in lottoMatchCounts:
                                lottoMatchCounts[userID] = 0
                            lottoMatchCounts[userID] += 1

                    # Determine winners
                    self.yesterdayLotteryWinners = [[],[],[]] # third, second, first place
                    for userID in lottoMatchCounts:
                        self.yesterdayLotteryWinners[lottoMatchCounts[userID] - 1].append(userID)

                    # Award winners
                    prizes = self.calculateLotteryPrizes(self.todayLotteryPrizePool)
                    for i in range(3):
                        if len(self.yesterdayLotteryWinners[i]) > 0:
                            prizePerPlayer = math.floor(prizes[i]/len(self.yesterdayLotteryWinners[i]))
                            for playerID in self.yesterdayLotteryWinners[i]:
                                self.players[playerID].transact(["$", prizePerPlayer])

                    # Begin next lottery
                    await self.refreshLottery()


            # check for timed event triggers
            for key in self.eventCounters:
                self.eventCounters[key] -= 1
                if self.eventCounters[key] == 0:
                    if key == "EVENT_SHOOTING_STAR":
                        # TODO modify a building with the shooting star event
                        # TODO reset event counter
                        pass

        async def messageReceived(self, message):
            if message.channel.id == self.channel.id:
                self.lastInteraction = datetime.datetime.now()

                if message.content == "!register":
                    self.registerPlayer(message.author)

                await message.delete(delay=15)

        async def reactionToggled(self, payload, toggledOn):
            if payload.channel_id == self.channel.id:
                if payload.user_id in self.players.keys():
                    player = self.players[payload.user_id]
                    self.lastInteraction = datetime.datetime.now()

                    for key in self.eventMessages:
                        if self.eventMessages[key].id == payload.message_id:
                            pass

                    if payload.message_id == self.buildingMessageObjects["BLDG_BANK"].id:
                        if payload.emoji.name == self.KEY_TO_EMOJI_MAP[self.bankMarketStatus]:
                            if toggledOn:
                                self.correctMarketUserIDs.append(payload.user_id)
                            else:
                                self.correctMarketUserIDs.remove(payload.user_id)

                    elif payload.message_id == self.buildingMessageObjects["BLDG_SHOP_1"].id:
                        SHOP_1_ITEMS = [
                            "ITEM_LEMON",
                            "ITEM_MELON",
                            "ITEM_MONEY_PRINTER"
                        ]
                        for shopItem in SHOP_1_ITEMS:
                            if payload.emoji.name == self.KEY_TO_EMOJI_MAP[shopItem]:
                                itemCost = self.ITEM_COSTS[shopItem]
                                if player.currencyTotal[itemCost[0]] > itemCost[1]:
                                    player.updateItems({shopItem: 1})
                                    player.transact(self.ITEM_COSTS[shopItem])
                        
                    elif payload.message_id == self.buildingMessageObjects["BLDG_LOTTERY"].id:
                        pass # only need to look at reactions on lottery at drawing time
                else:
                    user = self.client.get_user(payload.user_id)
                    helpfulMessage = await self.channel.send("{} you are not registered with the game. Type `!register` to join!".format(user.mention))
                    await helpfulMessage.delete(delay=15)


        ##################
        #### ON_MESSAGE ACTIONS
        ##################

        def registerPlayer(self, user):
            self.players[user.id] = IdleGameBot.GameSession.Player(user)
            print("Registered Player {}".format(user.name))

        ##################
        #### BUILDING MESSAGES
        ##################

        def generateBankMessage(self):
            bankEmojiString = ":bank::bank::bank:"
            if self.slumberLevel == 1:
                bankEmojiString = ":bank::bank::zzz:"
            elif self.slumberLevel == 2:
                bankEmojiString = ":bank::zzz::zzz:"
            elif self.slumberLevel == 3:
                bankEmojiString = ":zzz::zzz::zzz:"
            resultString =  "`~~~~~~~~~~~~~~~~~~~~~~~`\n"
            resultString += bankEmojiString + " **BANK** " + bankEmojiString + "\n"
            resultString += "`~~~~~~~~~~~~~~~~~~~~~~~`\n\n"
            resultString += "_This money, like most money, is just a number in a computer._\n\n"

            if self.bankMarketStatus == "BANK_STATUS_BULL":
                resultString += ":cow2: _We're currently in a __bull__ market! Select the bull to get 25\% extra income!_ :cow2:\n\n"
            else:
                resultString += ":camel: _We're currently in a __camel__ market! Select the camel to get 25\% extra income!_ :camel:\n\n"


            longestNameLength = 0
            longestDollarTotalLength = 0
            # figure out what length to buffer names at
            for userID in self.players:
                player = self.players[userID]

                if len(player.discordUserObject.name) > longestNameLength:
                    longestNameLength = len(player.discordUserObject.name)

                currencyLength = len(self.currencyString("$", player.currencyTotal["$"]))
                if currencyLength > longestDollarTotalLength:
                    longestDollarTotalLength = currencyLength

            resultString += "```"
            for userID in self.players:
                player = self.players[userID]
                bonusString = ""
                mult = 1.0
                if userID in self.correctMarketUserIDs:
                    bonusString = " ^"
                    mult = 1.25

                currentCurrStr = self.currencyString("$", player.currencyTotal["$"])
                resultString += "{} = {} + {}/sec{}\n".format(
                    player.discordUserObject.name + ' '*(longestNameLength - len(player.discordUserObject.name)),
                    currentCurrStr + ' '*(longestDollarTotalLength - len(currentCurrStr)),
                    self.currencyString("$", math.ceil(player.income["$"] * mult)),
                    bonusString
                )
            resultString += "```"

            return resultString

        def generateShop1Message(self):
            shopEmojiString = ":convenience_store::convenience_store::convenience_store:"
            resultString =  "`~~~~~~~~~~~~~~~~~~~~~~`\n"
            resultString += shopEmojiString + " **SHOP** " + shopEmojiString + "\n"
            resultString += "`~~~~~~~~~~~~~~~~~~~~~~`\n\n"
            resultString += "_Buy somethin', will ya?_\n\n"
            shopInventory = [
                ["ITEM_LEMON",         self.ITEM_COSTS["ITEM_LEMON"],         "+$1/sec",   "Lemons into lemonade, right?"],
                ["ITEM_MELON",         self.ITEM_COSTS["ITEM_MELON"],         "+$10/sec",  "Melons into melonade... Right...?"],
                ["ITEM_MONEY_PRINTER", self.ITEM_COSTS["ITEM_MONEY_PRINTER"], "+$500/sec", "Top of the line money printer!"],
                ["ITEM_BROKEN_HOUSE",  self.ITEM_COSTS["ITEM_BROKEN_HOUSE"],  "A house!",  "It ain't much, but it's home."],
            ]

            resultString += self.prettyPrintInventory(shopInventory)
            return resultString

        def generateLotteryMessage(self):
            lotteryEmojiString = ":moneybag::moneybag::moneybag:"
            resultString =  "`~~~~~~~~~~~~~~~~~~~~~~`\n"
            resultString += lotteryEmojiString + " **LOTTERY** " + lotteryEmojiString + "\n"
            resultString += "`~~~~~~~~~~~~~~~~~~~~~~`\n\n"

            resultString += "_Every day the lottery hint will change! Choose your three lucky numbers and you could be a winner! (Only the lowest three numbers selected will be counted. Terms and conditions apply.)_\n"

            # determine notable features about the drawing
            features = {
                "PRIMES": 0,
                "EVENS": 0,
                "ODDS": 0,
                "THREES": 0,
                "LUCKYSEVEN": 0,
            }
            for num in self.todayLotteryNumbers:
                if num == 1 or num == 2 or num == 3 or num == 5 or num == 7:
                    features["PRIMES"] += 1
                if num % 2 == 0:
                    features["EVENS"] += 1
                else: 
                    features["ODDS"] += 1
                if num % 3 == 0:
                    features["THREES"] += 1
                if num == 7:
                    features["LUCKYSEVEN"] += 1

            # select hints to display
            candidates = []
            for key in features:
                if features[key] > 0:
                    candidates.append(key)
            chosenFeatures = []
            while len(chosenFeatures) < 2:
                chosenFeatures.append(candidates.pop(random.randrange(0, len(candidates)))) # TODO these are rerandomized on every call to generateLotteryMessage, possibly memoize them if we care

            FEATURE_STRINGS_PLURAL = {
                "PRIMES": "{} primes",
                "EVENS": "{} even numbers" ,
                "ODDS": "{} odd numbers",
                "THREES": "{} numbers divisible by three",
            }
            FEATURE_STRINGS_SINGULAR = {
                "PRIMES": "1 prime",
                "EVENS": "1 even number" ,
                "ODDS": "1 odd number",
                "THREES": "1 number divisible by three",
                "LUCKYSEVEN": "a Lucky Seven"
            }
            finalFeatureStrings = []
            for featureKey in chosenFeatures:
                if features[featureKey] == 1:
                    finalFeatureStrings.append(FEATURE_STRINGS_SINGULAR[featureKey])
                else:
                    finalFeatureStrings.append(FEATURE_STRINGS_PLURAL[featureKey].format(str(features[featureKey])))

            # make sure that lucky seven is at the end
            if finalFeatureStrings[0] == FEATURE_STRINGS_SINGULAR["LUCKYSEVEN"]:
                finalFeatureStrings.append(finalFeatureStrings.pop(0))

            # Show/hide clarification on hint based on applicability
            NO_OVERLAP_PAIRS = [
                ["EVENS", "ODDS"],
                ["ODDS", "EVENS"],
                ["EVENS", "LUCKYSEVEN"],
                ["THREES", "LUCKYSEVEN"]
            ]
            possibleOverlapString = " _(These can overlap)_"
            for pair in NO_OVERLAP_PAIRS:
                if finalFeatureStrings[0] == pair[0] and finalFeatureStrings[1] == pair[1]:
                    possibleOverlapString = ""

            resultString += "\n__Today's Hint__: There's {} and {}!{}\n\n".format(finalFeatureStrings[0], finalFeatureStrings[1], possibleOverlapString)

            # Display results of yesterday's lottery!
            resultString += "Yesterday's winning numbers were **{}**.\n\n".format(self.listStringsWithCommas(self.yesterdayLotteryNumbers))
            if len([item for sublist in self.yesterdayLotteryWinners for item in sublist]) > 0: # flattened
                resultString += "_Congratulations to Yesterday's Winners:_\n"
                winnerStrings = []
                verbStrings = []
                for winnerList in self.yesterdayLotteryWinners: #third, second, first
                    if len(winnerList) > 0:
                        winnerMentions = []
                        for winnerID in winnerList:
                            winnerMentions.append(self.players[winnerID].discordUserObject.mention)

                        if len(winnerList) == 1:
                            verbStrings.append("takes")
                        else:
                            verbStrings.append("will split")

                        winnerStrings.append(self.listStringsWithCommas(winnerMentions))
                    else:
                        winnerStrings.append("Nobody")
                        verbStrings.append("got")

                prizes = self.calculateLotteryPrizes(self.yesterdayLotteryPrizePool)

                resultString += ":first_place: {} {} the first place prize of {}!\n".format(winnerStrings[2], verbStrings[2], str(prizes[2]))
                resultString += ":second_place: {} {} the second place prize of {}!\n".format(winnerStrings[1], verbStrings[1], str(prizes[1]))
                resultString += ":third_place: {} {} the third place prize of {}!\n".format(winnerStrings[0], verbStrings[0], str(prizes[0]))
            else:
                resultString += "There were no lottery winners yesterday. Better luck next time!"

            return resultString

        ##################
        #### DISPLAY HELPERS
        ##################

        def listStringsWithCommas(self, arr):
            if len(arr) == 0:
                return ""
            elif len(arr) == 1:
                return str(arr[0])
            elif len(arr) == 2:
                return str(arr[0]) + " and " + str(arr[1])
            else:
                result = "and " + str(arr[-1])
                for item in reversed(arr[:-1]):
                    result = str(item) + ", " + result
                return result

        # self.currencyString("$", "123456") => "$123,456"
        # self.currencyString("%", "123456789") => "%123m"
        def currencyString(self, unit, currencyInteger):
            negativeString = ""
            if currencyInteger < 0:
                negativeString = "-"
                currencyInteger = currencyInteger * -1

            def doCommas(numStr):
                if len(numStr) > 3:
                    return numStr[:-3] + "," + numStr[-3:]
                else:
                    return numStr

            currencyStringRaw = str(currencyInteger)
            result = currencyStringRaw

            # TODO decimal place for mbtq
            if len(currencyStringRaw) > 15:
                result = doCommas(currencyStringRaw[0:len(currencyStringRaw) - 15]) + "q"
            elif len(currencyStringRaw) > 12:
                result = currencyStringRaw[0:len(currencyStringRaw) - 12] + "t"
            elif len(currencyStringRaw) > 9:
                result = currencyStringRaw[0:len(currencyStringRaw) - 9] + "b"
            elif len(currencyStringRaw) > 6:
                result = currencyStringRaw[0:len(currencyStringRaw) - 6] + "m"
            elif len(currencyStringRaw) > 3:
                result = doCommas(currencyStringRaw)
            else:
                result = currencyStringRaw

            return negativeString + unit + result

        # inventoryList = [ [emojiID, priceTuple, effectDescription, flavorText], ... ]
        def prettyPrintInventory(self, inventoryList):
            result = ""

            maxPriceLength  = 0 
            maxEffectLength = 0
            for item in inventoryList:
                priceStr = self.currencyString(item[1][0], item[1][1])
                if len(priceStr) > maxPriceLength:
                    maxPriceLength = len(priceStr)
                if len(item[2]) > maxEffectLength:
                    maxEffectLength = len(item[2])

            for item in inventoryList:
                priceStr = self.currencyString(item[1][0], item[1][1])
                result += "• {} `{} | {} | {}`\n".format(
                    self.KEY_TO_EMOJI_MAP[item[0]],
                    " "*(maxPriceLength - len(priceStr)) + priceStr,
                    " "*(maxEffectLength - len(item[2])) + item[2],
                    item[3]
                )

            return result

        ##################
        #### ENCODING
        ##################

        CURRENT_VERSION = "0"

        BLOCK_0 = "0" # Version Number
        BLOCK_1 = "1" # System Message IDs
        BLOCK_2 = "2" # Milestones
        BLOCK_3 = "3" # Reserved
        BLOCK_4 = "4" # Reserved
        BLOCK_5 = "5" # Reserved
        BLOCK_6 = "6" # Player statistics

        ENCODING_INDEX_BLDG_BANK = 0
        ENCODING_INDEX_BLDG_STORE_1 = 1

        ENCODING_CHARSET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZåâêîôûŵŷäëïöüẅÿáéíóúẃýàèìòùẁỳçñÅÂÊÎÔÛŴŶÄËÏÖÜẄŸÁÉÍÓÚẂÝÀÈÌÒÙẀỲÇÑ~!@#$^&*()<>?/-_+=[]|µπø∂åßƒ†§¶£¢‡∆∫√∑"
        # convert a base 10 integer string into a base len(ENCODING_CHARSET) integer string
        def compressInt(self, num):
            result = ""
            radix = len(self.ENCODING_CHARSET)
            while num > 0:
                rem = num % radix
                result = self.ENCODING_CHARSET[int(rem)] + result
                num = (num - rem) / radix
            return result

        # reverses compressInt
        def decompressInt(self, inputStr):
            result = 0
            for i in range(len(inputStr)):
                order = len(inputStr) - (i + 1)
                magnitude = 1
                while order > 0:
                    magnitude *= len(self, ENCODING_CHARSET)
                    order -= 1
                result += magnitude * self, ENCODING_CHARSET.find(inputStr[i])
            return result

        # encode the state as a string
        def encodeState(self):
            # BLOCK_0 - Version
            stateString = self.CURRENT_VERSION

            stateString += "."
            # BLOCK_1 - System Message IDs

            stateString += ",".join([
                self.compressInt(self.buildingMessageObjects["BLDG_CONFIG"].id),
                self.compressInt(self.buildingMessageObjects["BLDG_BANK"].id),
                self.compressInt(self.buildingMessageObjects["BLDG_SHOP_1"].id),
            ])

            stateString += "."
            #BLOCK 2 - Milestones

            stateString += "."
            #BLOCK 3

            stateString += "."
            #BLOCK 4

            stateString += "."
            #BLOCK 5

            stateString += "."
            #BLOCK 6

            return stateString

        # set game state variables based on import string (encoded by encodeState)
        async def importState(self, importString):
            pass #TODO

    ##################
    #### BOT INITIALIZATION
    ##################

    def __init__(self, prefix="!", greeting="Hello", farewell="Goodbye"):
        super().__init__(prefix, greeting, farewell)

        self.gameSessions = {} # maps guildIDs to GameSession objects

    async def on_ready(self):
        await super().on_ready()

        for guild in self.client.guilds:
            gameChannel = None

            for channel in guild.channels:
                if channel.name == GAME_CHANNEL_NAME and isinstance(channel, discord.TextChannel):
                    print("Found " + guild.name + "." + channel.name)
                    gameChannel = channel

            if gameChannel is not None:
                self.gameSessions[guild.id] = IdleGameBot.GameSession(self.client, guild, gameChannel)

                # TODO search for configuration message

                # success = await self.gameSessions[guild.id].importState() # TODO
                success = None
                if success == None: # game not initialized
                    await self.gameSessions[guild.id].initializeBuildings()
                elif success == False: # error importing
                    await gameChannel.send("There was an error importing the game state.")
                    return

                self.loop.create_task(IdleGameBot.tick(self.gameSessions[guild.id]))

    ##################
    #### BOT EVENT HANDLERS
    ##################

    async def tick(gameSession):
        while True:
            await gameSession.onTick()
            await asyncio.sleep(1)

    async def on_message(self, message):
        await super().on_message(message)
        if message.guild.id in self.gameSessions.keys() and message.author.id != self.client.user.id:
            await self.gameSessions[message.guild.id].messageReceived(message)

    async def on_raw_reaction_add(self, payload):
        await super().on_raw_reaction_add(payload)
        if payload.guild_id in self.gameSessions.keys() and payload.user_id != self.client.user.id:
            await self.gameSessions[payload.guild_id].reactionToggled(payload, True)

    async def on_raw_reaction_remove(self, payload):
        await super().on_raw_reaction_remove(payload)
        if payload.guild_id in self.gameSessions.keys() and payload.user_id != self.client.user.id:
            await self.gameSessions[payload.guild_id].reactionToggled(payload, False)