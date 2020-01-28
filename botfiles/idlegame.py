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
            def __init__(self, discordUserObject):
                self.discordUserObject = discordUserObject

                self.currencyTotal = {
                    "$": 0,
                    "SOCIETY_FILM":    0,
                    "SOCIETY_ART":     0,
                    "SOCIETY_THEATER": 0,
                    "SOCIETY_GAMING":  0,
                }

                self.items = {
                    "ALLOWANCE":          1,
                    "ITEM_LEMON":         0,
                    "ITEM_MELON":         0,
                    "ITEM_MONEY_PRINTER": 0,
                    "ITEM_BROKEN_HOUSE":  0,
                    "UPGRADE_OFFICE": 0,
                    "UPGRADE_PADDOCK": 0,
                    "UPGRADE_LAB": 0,
                    "ANIMAL_CHICKEN": 3,
                    "ANIMAL_RABBIT": 2,
                    "ANIMAL_PIG": 3,
                    "ANIMAL_COW": 3,
                    "ANIMAL_UNICORN": 1,
                }

                self.houseMessageObject = None

                self.refreshBaseIncome()

            def updateItems(self, itemChanges):
                for itemKey in itemChanges:
                    self.items[itemKey] += itemChanges[itemKey]
                self.income = self.getBaseIncome()

            def refreshBaseIncome(self):
                self.income = self.getBaseIncome()

            def getBaseIncome(self):
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

            def __str__(self):
                return "<userID:{0}, currencyTotal:{1}, items:{2}>".format(self.discordUserObject.id, str(self.currencyTotal), str(self.items))

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
            "SOCIETY_FILM": "🎬",
            "SOCIETY_ART": "🎨",
            "SOCIETY_THEATER": "🎭",
            "SOCIETY_GAMING": "🕹️",
            "UPGRADE_BULLETIN": "📌",
            "UPGRADE_OFFICE": "🗄",
            "UPGRADE_PADDOCK": "🏞️",
            "UPGRADE_LAB": "🔬",
            "ANIMAL_CHICKEN": "🐔",
            "ANIMAL_RABBIT": "🐰",
            "ANIMAL_PIG": "🐷",
            "ANIMAL_COW": "🐮",
            "ANIMAL_UNICORN": "🦄",
            "ANIMAL_ROOSTER": "🐓",
        }

        EMOJI_TO_KEY_MAP = {v: k for k, v in KEY_TO_EMOJI_MAP.items()}

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
            "ITEM_LEMON":         ["$", -100],
            "ITEM_MELON":         ["$", -990],
            "ITEM_MONEY_PRINTER": ["$", -49000],
            "ITEM_BROKEN_HOUSE":  ["$", -1],
            "UPGRADE_BULLETIN":   ["$", -10000],
            "ANIMAL_CHICKEN":     ["$", -50000],
            "ANIMAL_RABBIT":      ["$", -75000],
            "ANIMAL_PIG":         ["$", -100000],
            "ANIMAL_COW":         ["$", -500000],
            "ANIMAL_UNICORN":     ["$", -5000000],
        }

        SHOP_1_ITEMS = [
            "ITEM_LEMON",
            "ITEM_MELON",
            "ITEM_MONEY_PRINTER",
            "ITEM_BROKEN_HOUSE"
        ]

        ART_SOCIETY_ITEMS = [
            "SOCIETY_FILM",
            "SOCIETY_ART",
            "SOCIETY_THEATER",
            "SOCIETY_GAMING",
        ]

        HOUSE_DEPOT_ITEMS = [
            "UPGRADE_BULLETIN",
            "UPGRADE_OFFICE",
            "UPGRADE_PADDOCK",
            "UPGRADE_LAB",
        ]

        ANIMAL_MART_ITEMS = [
            "ANIMAL_CHICKEN",
            "ANIMAL_RABBIT",
            "ANIMAL_PIG",
            "ANIMAL_COW",
            "ANIMAL_UNICORN",
        ]

        HOUSE_UPGRADE_COSTS = {
            "UPGRADE_OFFICE":  [
                ["$", -1],#["$",  -2000000],
                ["$", -2],#["$", -10000000],
                ["$", -3],#["$", -20000000],
            ],
            "UPGRADE_PADDOCK": [
                ["$", -1],#["$",  -5000000],
                ["$", -2],#["$", -30000000],
                ["$", -3],#["$", -80000000],
            ],
            "UPGRADE_LAB":     [
                ["$", -1],#["$",  -20000000],
                ["$", -2],#["$", -100000000],
                ["$", -3],#["$", -500000000],
            ],   
        }

        ANIMAL_STATISTICS = {
            "ANIMAL_CHICKEN": {"REPRO_RATE": 0.5, "ITEM_PRODUCED": "ITEM_EGG",     "PROD_RATE": 0.5},
            "ANIMAL_RABBIT":  {"REPRO_RATE": 0.7, "ITEM_PRODUCED": None,           "PROD_RATE": 0},
            "ANIMAL_PIG":     {"REPRO_RATE": 0.4, "ITEM_PRODUCED": None,           "PROD_RATE": 0},
            "ANIMAL_COW":     {"REPRO_RATE": 0.2, "ITEM_PRODUCED": "ITEM_MILK",    "PROD_RATE": 0.5},
            "ANIMAL_UNICORN": {"REPRO_RATE":   0, "ITEM_PRODUCED": "ITEM_GLITTER", "PROD_RATE": 0.1},
        }

        PADDOCK_SIZES = [5, 10, 20]
        MAX_ANIMALS_PER_ROW = 12

        ##################
        #### INITIALIZATION
        ##################

        def __init__(self, eventLoop, client, guild, gameChannel):
            self.loop = eventLoop
            self.client = client
            self.guild = guild
            self.channel = gameChannel # the game channel

            # Game component references
            self.players = {} # maps discordUserIDs to Player objects
            self.buildingMessageObjects = {} # maps BLDG string constants to messages
            self.milestones = {} # maps milestone keys to playerIDs

            # Bank Properties
            self.bankMarketStatus = "BANK_STATUS_BULL" # toggles at regular intervals
            self.correctMarketUserIDs = [] # userIDs of players who have toggled the bull/camel emoji

            # Lottery Properties
            self.lotteryDrawTime = datetime.datetime.now() + datetime.timedelta(days=1)
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

            # Sanity check encoding mechanism
            assert len(set(i for i in self.ENCODING_CHARSET if self.ENCODING_CHARSET.count(i)>1)) == 0

        async def initializeBuildings(self):
            # CONFIG PLACEHOLDER
            self.buildingMessageObjects["BLDG_CONFIG"] = await self.channel.send(":construction:")

            # BANK
            self.buildingMessageObjects["BLDG_BANK"] = await self.channel.send(self.generateBankMessage())
            await self.buildingMessageObjects["BLDG_BANK"].add_reaction(self.KEY_TO_EMOJI_MAP[self.bankMarketStatus])

            # SHOP 1
            self.buildingMessageObjects["BLDG_SHOP_1"] = await self.channel.send(self.generateShop1Message())
            for item in self.SHOP_1_ITEMS:
                await self.buildingMessageObjects["BLDG_SHOP_1"].add_reaction(self.KEY_TO_EMOJI_MAP[item])    
            
            # LOTTERY
            self.buildingMessageObjects["BLDG_LOTTERY"] = await self.channel.send(":construction:")
            await self.refreshLottery()

            # ART SOCIETY
            self.buildingMessageObjects["BLDG_ART_SOCIETY"] = await self.channel.send(self.generateArtSocietyMessage())
            for item in self.ART_SOCIETY_ITEMS:
                await self.buildingMessageObjects["BLDG_ART_SOCIETY"].add_reaction(self.KEY_TO_EMOJI_MAP[item])    

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


        async def initializeHouseDepot(self):
            self.buildingMessageObjects["BLDG_HOUSE_DEPOT"] = await self.channel.send(self.generateHouseDepotMessage())
            for item in self.HOUSE_DEPOT_ITEMS:
                await self.buildingMessageObjects["BLDG_HOUSE_DEPOT"].add_reaction(self.KEY_TO_EMOJI_MAP[item])

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

        def calculateSocietyDonationPrices(self):
            SOCIETY_DONATION_INCREMENT = 2

            sums = {
                "SOCIETY_FILM":    ["$", SOCIETY_DONATION_INCREMENT],
                "SOCIETY_ART":     ["$", SOCIETY_DONATION_INCREMENT],
                "SOCIETY_THEATER": ["$", SOCIETY_DONATION_INCREMENT],
                "SOCIETY_GAMING":  ["$", SOCIETY_DONATION_INCREMENT],
            }

            for playerID in self.players:
                player = self.players[playerID]

                for society in sums:
                    sums[society][1] += player.currencyTotal[society] * SOCIETY_DONATION_INCREMENT

            return sums

        ##################
        #### GAME EVENT HANDLERS
        ##################

        async def onTick(self):
            # Determine the activity level of the bot
            tempSlumberLevel = 0
            SLUMBER_MINUTES_THRESHOLDS = [2, 15, 1440]
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

            if self.counter % (60 * 30) == 0: 
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
                    self.loop.create_task(self.refreshLottery())


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
                elif message.content == "!save":
                    await self.buildingMessageObjects["BLDG_CONFIG"].edit(content=self.encodeState())

                await message.delete(delay=15)

        async def reactionToggled(self, payload, toggledOn):
            if payload.channel_id == self.channel.id:
                userID = payload.user_id
                if userID in self.players.keys():
                    player = self.players[userID]
                    self.lastInteraction = datetime.datetime.now()

                    for key in self.eventMessages:
                        if self.eventMessages[key].id == payload.message_id:
                            pass

                    if payload.message_id == self.buildingMessageObjects["BLDG_BANK"].id:
                        if payload.emoji.name == self.KEY_TO_EMOJI_MAP[self.bankMarketStatus]:
                            if toggledOn:
                                self.correctMarketUserIDs.append(userID)
                            elif userID in self.correctMarketUserIDs:
                                self.correctMarketUserIDs.remove(userID)

                    elif payload.message_id == self.buildingMessageObjects["BLDG_SHOP_1"].id:
                        for shopItem in self.SHOP_1_ITEMS:
                            if payload.emoji.name == self.KEY_TO_EMOJI_MAP[shopItem]:
                                itemCost = self.ITEM_COSTS[shopItem]
                                if player.currencyTotal[itemCost[0]] > max(0, -1 * itemCost[1]): # make sure that the player can afford it
                                    if shopItem == "ITEM_BROKEN_HOUSE":
                                        await self.initializeHouseDepot()
                                        player.houseMessageObject = await self.channel.send(self.generatePlayerHouseMessage(userID))
                                        # if player.items["ITEM_BROKEN_HOUSE"] > 0: # prevent players from getting more than one house
                                        #     return
                                        # else:
                                        #     if "FIRST_HOUSE" not in self.milestones:
                                        #         self.initializeHouseDepot()
                                        #         self.milestones["FIRST_HOUSE"] = userID
                                        #     player.houseMessageObject = await self.channel.send(self.generatePlayerHouseMessage(userID))

                                    player.updateItems({shopItem: 1})
                                    player.transact(itemCost)
                        
                    elif payload.message_id == self.buildingMessageObjects["BLDG_LOTTERY"].id:
                        pass # only need to look at reactions on lottery at drawing time
                    elif payload.message_id == self.buildingMessageObjects["BLDG_ART_SOCIETY"].id:
                        for society in self.ART_SOCIETY_ITEMS:
                            if payload.emoji.name == self.KEY_TO_EMOJI_MAP[society]:
                                itemCost = self.calculateSocietyDonationPrices()[society] # currency tuple
                                if player.currencyTotal[itemCost[0]] > max(0, -1 * itemCost[1]): # make sure that the player can afford it
                                    player.transact(itemCost) # pay for the reputation
                                    player.transact([society, 1]) # get the reputation
                                    await self.buildingMessageObjects["BLDG_ART_SOCIETY"].edit(content=self.generateArtSocietyMessage())
                    elif payload.message_id == self.buildingMessageObjects["BLDG_HOUSE_DEPOT"].id:
                        for shopItem in self.HOUSE_DEPOT_ITEMS:
                            if payload.emoji.name == self.KEY_TO_EMOJI_MAP[shopItem]:
                                itemCost = self.HOUSE_UPGRADE_COSTS[shopItem][player.items[shopItem]]
                                if player.currencyTotal[itemCost[0]] > max(0, -1 * itemCost[1]): # make sure that the player can afford it
                                    player.updateItems({shopItem: 1})
                                    player.transact(itemCost)
                                    await player.houseMessageObject.edit(content=self.generatePlayerHouseMessage(userID))

                else:
                    user = self.client.get_user(userID)
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

                currencyLength = len(self.currencyString(["$", player.currencyTotal["$"]]))
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

                currentCurrStr = self.currencyString(["$", player.currencyTotal["$"]])
                resultString += "{} = {} + {}/sec{}\n".format(
                    player.discordUserObject.name + ' '*(longestNameLength - len(player.discordUserObject.name)),
                    currentCurrStr + ' '*(longestDollarTotalLength - len(currentCurrStr)),
                    self.currencyString(["$", math.ceil(player.income["$"] * mult)]),
                    bonusString
                )
            resultString += "```"

            return resultString

        def generateShop1Message(self):
            shopEmojiString = ":shopping_cart::convenience_store::shopping_cart:"
            resultString =  "`~~~~~~~~~~~~~~~~~~~~~~`\n"
            resultString += shopEmojiString + " **SHOP** " + shopEmojiString + "\n"
            resultString += "`~~~~~~~~~~~~~~~~~~~~~~`\n\n"
            resultString += "_Buy somethin', will ya?_\n"
            shopInventory = [
                ["ITEM_LEMON",         self.ITEM_COSTS["ITEM_LEMON"],         "+$1/sec",   "Lemons into lemonade, right?"],
                ["ITEM_MELON",         self.ITEM_COSTS["ITEM_MELON"],         "+$10/sec",  "Melons into melonade... Right...?"],
                ["ITEM_MONEY_PRINTER", self.ITEM_COSTS["ITEM_MONEY_PRINTER"], "+$500/sec", "Top of the line money printer!"],
                ["ITEM_BROKEN_HOUSE",  self.ITEM_COSTS["ITEM_BROKEN_HOUSE"],  "A house!",  "It ain't much, but it's home."],
                #["ITEM_BOX",           self.ITEM_COSTS["ITEM_BOX"],          "+25 inventory space for each item",  "Gotta put all those lemons somewhere!"],
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

        def generateArtSocietyMessage(self):
            emojiString = ":art::clapper::performing_arts:"
            resultString =  "`~~~~~~~~~~~~~~~~~~~~~~~~~~~`\n"
            resultString += emojiString + " **ART SOCIETY** " + emojiString + "\n"
            resultString += "`~~~~~~~~~~~~~~~~~~~~~~~~~~~`\n\n"


            nameBuffer = 0
            societyBuffers = {
                "SOCIETY_FILM": 0,
                "SOCIETY_ART": 0,
                "SOCIETY_THEATER": 0,
                "SOCIETY_GAMING": 0,
            }
            # figure out what length to buffer names at
            for userID in self.players:
                player = self.players[userID]

                if len(player.discordUserObject.name) > nameBuffer:
                    nameBuffer = len(player.discordUserObject.name)

                for society in societyBuffers:
                    repLength = len(str(player.currencyTotal[society]))
                    if repLength > societyBuffers[society]:
                        societyBuffers[society] = repLength

            resultString += "_Our Generous Benefactors..._\n"
            for userID in self.players:
                player = self.players[userID]

                resultString += "`{}:`     :clapper:` {}`     :art:`{}`     :performing_arts:`{}`     :joystick:`{}`\n".format(
                    player.discordUserObject.name + ' '*(nameBuffer - len(player.discordUserObject.name)),
                    ' '*(societyBuffers["SOCIETY_FILM"]    - len(str(player.currencyTotal["SOCIETY_FILM"])))    + str(player.currencyTotal["SOCIETY_FILM"]),
                    ' '*(societyBuffers["SOCIETY_ART"]     - len(str(player.currencyTotal["SOCIETY_ART"])))     + str(player.currencyTotal["SOCIETY_ART"]),
                    ' '*(societyBuffers["SOCIETY_THEATER"] - len(str(player.currencyTotal["SOCIETY_THEATER"]))) + str(player.currencyTotal["SOCIETY_THEATER"]),
                    ' '*(societyBuffers["SOCIETY_GAMING"]  - len(str(player.currencyTotal["SOCIETY_GAMING"])))  + str(player.currencyTotal["SOCIETY_GAMING"]),
                )

            societyPrices = self.calculateSocietyDonationPrices()

            resultString += "\n_Care to make a donation?_\n"
            shopInventory = [
                ["SOCIETY_FILM",    societyPrices["SOCIETY_FILM"],     "+1 film rep",    "Donations go to asking awkward questions at our yearly festival."],
                ["SOCIETY_ART",     societyPrices["SOCIETY_ART"],      "+1 art rep",     "Donations go to art installations on corporate campuses."],
                ["SOCIETY_THEATER", societyPrices["SOCIETY_THEATER"],  "+1 theater rep", "Donations go to high school productions of Seussical."],
                ["SOCIETY_GAMING",  societyPrices["SOCIETY_GAMING"],   "+1 gaming rep",  "Donations go to Overwatch lootboxes."],
            ]
            resultString += self.prettyPrintInventory(shopInventory)

            return resultString

        def generateHouseDepotMessage(self):
            emojiString = ":shopping_cart::safety_vest::shopping_cart:"
            resultString =  "`~~~~~~~~~~~~~~~~~~~~~~~~~~~~~`\n"
            resultString += emojiString + " **HOUSE DEPOT** " + emojiString + "\n"
            resultString += "`~~~~~~~~~~~~~~~~~~~~~~~~~~~~~`\n\n"

            resultString += "_You seem like the DIY type. Why not make a few improvements to your house?_\n"

            shopInventory = [
                ["UPGRADE_BULLETIN", self.ITEM_COSTS["UPGRADE_BULLETIN"], "Change the message on your house", "You will be prompted via DM."],
                ["UPGRADE_OFFICE",   "Listed on house",        "Upgrade a home office",            "Bring work home with you!"],
                ["UPGRADE_PADDOCK",  "Listed on house",        "Upgrade a paddock",                "A place to put your animals."],
                ["UPGRADE_LAB",      "Listed on house",        "Upgrade a laboratory",             "What kind of mad science will you get up to?"],
            ]
            resultString += self.prettyPrintInventory(shopInventory)
            return resultString

        def generateAnimalShopMessage(self):
            emojiString = ":shopping_cart::cow::shopping_cart:"
            resultString =  "`~~~~~~~~~~~~~~~~~~~~~~`\n"
            resultString += emojiString + " **ANIMAL MART** " + emojiString + "\n"
            resultString += "`~~~~~~~~~~~~~~~~~~~~~~`\n\n"

            resultString += "_Get some animals for your paddock. Get two and maybe they'll do what animals do ;)_"

            shopInventory = [
                ["ANIMAL_CHICKEN", self.ITEM_COSTS["ANIMAL_CHICKEN"], "+1 Chicken", "Produces eggs when they aren't reproducing."],
                ["ANIMAL_RABBIT",  self.ITEM_COSTS["ANIMAL_RABBIT"],  "+1 Rabbit",  "Reproduces at a fast rate."],
                ["ANIMAL_PIG",     self.ITEM_COSTS["ANIMAL_PIG"],     "+1 Pig",     "Reproduces at a medium rate."],
                ["ANIMAL_COW",     self.ITEM_COSTS["ANIMAL_COW"],     "+1 Cow",     "Reproduces at a slow rate. Produces milk."],
                ["ANIMAL_UNICORN", self.ITEM_COSTS["ANIMAL_UNICORN"], "+1 Unicorn", "Produces unicorn dust, does not reproduce."],
            ]
            resultString += self.prettyPrintInventory(shopInventory)
            return resultString

        def generatePlayerHouseMessage(self, playerID):
            player = self.players[playerID]

            emojiString = ":spider_web::house_abandoned::spider_web:"

            resultString =  "`~~~~~~~~~~~~~~~~~~~~~~~~~~`\n"
            houseName = " **{}'s HOUSE** ".format(player.discordUserObject.name.upper())
            resultString += emojiString + houseName + emojiString + "\n"
            resultString += "`~~~~~~~~~~~~~~~~~~~~~~~~~~`\n\n"

            resultString += "_{}_\n\n".format("House Sweet House")

            # Office
            resultString += ":file_cabinet: __**Office Level {}**__ - _Next Upgrade: {}_\n".format(player.items["UPGRADE_OFFICE"], self.currencyString(self.HOUSE_UPGRADE_COSTS["UPGRADE_OFFICE"][player.items["UPGRADE_OFFICE"]]))
            if player.items["UPGRADE_OFFICE"] == 0:
                resultString += "_This room seems just drab enough to build a home office in._\n\n"
            elif player.items["UPGRADE_OFFICE"] == 1:
                resultString += "• :ledger: __Ledger__: Click to get a DM with your current item totals.\n\n"

            # Paddock
            resultString += ":park: __**Paddock Level {}**__ - _Next Upgrade: {}_\n".format(player.items["UPGRADE_PADDOCK"], self.currencyString(self.HOUSE_UPGRADE_COSTS["UPGRADE_PADDOCK"][player.items["UPGRADE_PADDOCK"]]))
            resultString += self.generatePaddock(player)


            # Lab
            resultString += ":microscope: __**Laboratory Level {}**__ - _Next Upgrade: {}_\n".format(player.items["UPGRADE_LAB"], self.currencyString(self.HOUSE_UPGRADE_COSTS["UPGRADE_LAB"][player.items["UPGRADE_LAB"]]))
            if player.items["UPGRADE_LAB"] == 0:
                resultString += "_This room seems just dark and stormy enough to build a laboratory in._\n\n"
            elif player.items["UPGRADE_LAB"] == 1:
                resultString += "• :syringe: **Hormones** Lvl 1 - (0% + .2%/min) Increase animal item production and reproduction\n"
                resultString += "• :abacus:  **Finance** Lvl 1 - (0% + .2%/min) Increase income\n"
                resultString += "• :books: **Research Practices** Lvl 1 - (0% + .2%/min) Increase research rates\n"
                resultString += "• :alembic: **Alchemy** Lvl 1 - (0% + .2%/min) Unlock the secrets of alchemy\n"

            return resultString


        ##################
        #### DISPLAY HELPERS
        ##################

        def generatePaddock(self, player):
            paddockLevel = player.items["UPGRADE_PADDOCK"]
            if paddockLevel == 0:
                return "_You've got a lot of land here. Why not build an enclosure for some animals?_\n\n"

            resultString = "• :truck: __Truck__: Click to get a DM with animal management options."

            playerAnimals = {}
            for animalKey in self.ANIMAL_STATISTICS:
                if animalKey in player.items:
                    playerAnimals[animalKey] = player.items[animalKey]

            if player.items["ANIMAL_CHICKEN"] >= 2:
                resultString += "• :rooster: __Rooster__: Toggle on to have your chickens produce chickens instead of eggs."

            resultString += "——————————————————————\n"

            # Determine a position for each animal, taking the next position if occupied
            dimension = self.PADDOCK_SIZES[paddockLevel] * self.MAX_ANIMALS_PER_ROW
            positions = {}
            for animalKey in playerAnimals:
                for i in range(playerAnimals[animalKey]):
                    position = random.randrange(dimension)

                    while position in positions:
                        position = (position + 1) % dimension

                    positions[i] = animalKey

            # Populate the rows with animals
            rows = ["" for i in range(self.PADDOCK_SIZES[paddockLevel])]
            for i in positions:
                rowNum = math.floor(i / self.MAX_ANIMALS_PER_ROW)
                rows[rowNum] += self.KEY_TO_EMOJI_MAP[positions[i]]

            # space them out a bit
            for row in rows:
                if len(row) > 0:
                    spaces = (self.MAX_ANIMALS_PER_ROW - len(row)) * 6
                    for i in range(spaces):
                        spacePos = random.randrange(len(row))
                        row = row[:spacePos] + " " + row[spacePos+1:]

                resultString += "|" + row + "\n"

            resultString += "——————————————————————\n"

            return resultString

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
        def currencyString(self, currencyTuple):
            if isinstance(currencyTuple, str):
                return currencyTuple

            unit = currencyTuple[0]
            currencyInteger = currencyTuple[1]
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
                priceStr = self.currencyString(item[1])
                if len(priceStr) > maxPriceLength:
                    maxPriceLength = len(priceStr)
                if len(item[2]) > maxEffectLength:
                    maxEffectLength = len(item[2])

            for item in inventoryList:
                priceStr = self.currencyString(item[1])
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

        BUILDING_MESSAGE_OBJECTS_ENCODING_ORDER = [
            "BLDG_CONFIG",
            "BLDG_BANK",
            "BLDG_SHOP_1",
            "BLDG_LOTTERY",
            "BLDG_ART_SOCIETY",
            "BLDG_HOUSE_DEPOT"
        ]
        PLAYER_CURRENCY_ENCODING_ORDER = [
            "$",
            "SOCIETY_FILM",
            "SOCIETY_ART",
            "SOCIETY_THEATER",
            "SOCIETY_GAMING",
        ]
        PLAYER_ITEMS_ENCODING_ORDER = [
            "ALLOWANCE",
            "ITEM_LEMON",
            "ITEM_MELON",
            "ITEM_MONEY_PRINTER",
            "ITEM_BROKEN_HOUSE",
            "UPGRADE_OFFICE",
            "UPGRADE_PADDOCK",
            "UPGRADE_LAB",
            "ANIMAL_CHICKEN",
            "ANIMAL_RABBIT",
            "ANIMAL_PIG",
            "ANIMAL_COW",
            "ANIMAL_UNICORN",
        ]

        ENCODING_CHARSET = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZāēīōūåâêîôûŵŷäëïöüẅÿáéíóúẃýàèìòùẁỳçñĀĒĪŌŪÅÂÊÎÔÛŴŶÄËÏÖÜẄŸÁÉÍÓÚẂÝÀÈÌÒÙẀỲÇÑ!@#$^&*<>?/_+=≠±|µπø∂ßƒ†§¶£¢‡∆∫√∑"

        # convert a base 10 POSITIVE integer string into a base len(ENCODING_CHARSET) integer string
        def compressInt(self, num):
            num = int(num)
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
                    magnitude *= len(self.ENCODING_CHARSET)
                    order -= 1
                result += magnitude * self.ENCODING_CHARSET.find(inputStr[i])
            return result

        # Encode the state as a string. State is encoded as integers in a 4-nested array. levels are separated by the following separators, in order: highest [.,:;] lowest
        def encodeState(self):
            # BLOCK_0 - Version Number
            stateStrings = [self.CURRENT_VERSION]

            # BLOCK_1 - System Message IDs
            stateStrings.append(",".join([self.compressInt(self.buildingMessageObjects[key].id) for key in self.BUILDING_MESSAGE_OBJECTS_ENCODING_ORDER if key in self.buildingMessageObjects]))

            # BLOCK 2 - Player statistics
            stateStrings.append(",".join([
                ":".join([
                    self.compressInt(playerID),
                    ";".join([self.compressInt(player.currencyTotal[currencyKey]) for currencyKey in self.PLAYER_CURRENCY_ENCODING_ORDER]),
                    ";".join([self.compressInt(player.items[itemKey]) for itemKey in self.PLAYER_ITEMS_ENCODING_ORDER]),
                    self.compressInt(player.houseMessageObject.id) if player.houseMessageObject != None else "0",
                ]) for (playerID, player) in self.players.items()
            ]))

            return ".".join(stateStrings)

        # set game state variables based on importString (encoded by encodeState)
        async def importState(self, importString):
            blocks = importString.split(".")

            if blocks[0] != self.CURRENT_VERSION:
                print("Warning: Version mismatch, {} found, {} expected".format(blocks[0], self.CURRENT_VERSION))

            systemMessageIDs = blocks[1].split(",")
            self.buildingMessageObjects = dict(zip(self.BUILDING_MESSAGE_OBJECTS_ENCODING_ORDER, [await self.channel.fetch_message(self.decompressInt(messageID)) for messageID in systemMessageIDs]))

            for playerEncoding in blocks[2].split(","):
                playerBlocks = playerEncoding.split(":")
                playerID = self.decompressInt(playerBlocks[0])

                player = IdleGameBot.GameSession.Player(self.client.get_user(playerID))
                player.currencyTotal = dict(zip(self.PLAYER_CURRENCY_ENCODING_ORDER, [self.decompressInt(total) for total in playerBlocks[1].split(";")]))
                player.items = dict(zip(self.PLAYER_ITEMS_ENCODING_ORDER, [self.decompressInt(count) for count in playerBlocks[2].split(";")]))
                if playerBlocks[3] != 0:
                    player.houseMessageObject = await self.channel.fetch_message(self.decompressInt(playerBlocks[3]))

                player.refreshBaseIncome()
                self.players[playerID] = player

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
                gameSession = IdleGameBot.GameSession(self.loop, self.client, guild, gameChannel)
                self.gameSessions[guild.id] = gameSession

                # Search for a configuration message, and import it if it exists. otherwise, initialize the game.
                firstMessageArr = await gameChannel.history(limit=1,oldest_first=True).flatten()
                if len(firstMessageArr) == 0:
                    await self.gameSessions[guild.id].initializeBuildings()
                else:
                    print(firstMessageArr[0].content)
                    await gameSession.importState(firstMessageArr[0].content)

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