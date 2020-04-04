import discord
import asyncio
import random, math
import urllib.request
import re
import os, io
import threading
import pickle
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
                    "ITEM_GLITTER":       0,
                    "ITEM_ROCKET_FUEL":   0,
                    "UPGRADE_OFFICE":     0,
                    "UPGRADE_PADDOCK":    0,
                    "UPGRADE_LAB":        0,
                }

                self.animalPositions = {
                    "ANIMAL_CHICKEN": [],
                    "ANIMAL_RABBIT": [],
                    "ANIMAL_PIG": [],
                    "ANIMAL_COW": [],
                    "ANIMAL_UNICORN": [],
                }

                self.research = {
                    "RESEARCH_HORMONES": {"LEVEL": 0, "TOTAL": 0, "RATE": 0},
                    "RESEARCH_FINANCE":  {"LEVEL": 0, "TOTAL": 0, "RATE": 0},
                    "RESEARCH_RESEARCH": {"LEVEL": 0, "TOTAL": 0, "RATE": 0},
                    "RESEARCH_ALCHEMY":  {"LEVEL": 0, "TOTAL": 0, "RATE": 0},
                }

                self.houseMessageObject = None
                self.houseBulletinString = "House Sweet House"
                self.bulletinUpdatePending = False
                self.roosterEnabled = False

                self.refreshBaseIncome()

            def updateItems(self, itemChanges):
                for itemKey in itemChanges:
                    if itemKey not in self.items:
                        self.items[itemKey] = 0
                    self.items[itemKey] += itemChanges[itemKey]
                self.income = self.getBaseIncome()

            def getBaseIncome(self):
                incomeResult = {
                    "$": 0
                }

                incomeResult["$"] += self.items["ALLOWANCE"]
                incomeResult["$"] += self.items["ITEM_LEMON"]
                incomeResult["$"] += 10 * self.items["ITEM_MELON"]
                incomeResult["$"] += 500 * self.items["ITEM_MONEY_PRINTER"]

                incomeResult["$"] *= 1.0 + .02 * self.research["RESEARCH_FINANCE"]["LEVEL"]

                return incomeResult

            def refreshBaseIncome(self):
                self.income = self.getBaseIncome()

            def addAnimal(self, animalType):
                occupiedPositions = [item for k, sublist in self.animalPositions.items() for item in sublist]

                dimension = IdleGameBot.GameSession.PADDOCK_SIZES[self.items["UPGRADE_PADDOCK"]] * IdleGameBot.GameSession.MAX_ANIMALS_PER_ROW

                if len(occupiedPositions) >= dimension:
                    return

                pos = random.randrange(dimension)
                while pos in occupiedPositions:
                    pos = (pos + 1) % dimension

                self.animalPositions[animalType].append(pos)

            def removeAnimals(self, animalType, count):
                for i in range(count):
                    self.animalPositions[animalType].pop(random.randrange(len(self.animalPositions[animalType])))
                    if len(self.animalPositions[animalType]) == 0:
                        print("Could not remove {} {}, removed {}".format(count, animalType, i + 1))
                        return

            # Remember that positive currencyTuples mean ADDING TO currencyTotal!
            def transact(self, currencyTuple):
                self.currencyTotal[currencyTuple[0]] += currencyTuple[1]

            NO_DISPLAY_ITEMS = [
                "ALLOWANCE",
                "ITEM_BROKEN_HOUSE",
                "UPGRADE_OFFICE",
                "UPGRADE_PADDOCK",
                "UPGRADE_LAB",
            ]

            def generateItemDigest(self):
                result = "Here is your inventory as of right now:\n"
                for itemKey in self.items:
                    if itemKey not in self.NO_DISPLAY_ITEMS:
                        result += "{}: {}\n".format(IdleGameBot.GameSession.KEY_TO_EMOJI_MAP[itemKey], self.items[itemKey])

                result += "\n" + self.generateAnimalDigest()              

                return result

            def generateAnimalDigest(self):
                result = "Here are your animal populations as of right now:\n"
                for animalKey in self.animalPositions:
                    result += "{}: {}\n".format(IdleGameBot.GameSession.KEY_TO_EMOJI_MAP[animalKey], len(self.animalPositions[animalKey]))

                return result

            def __str__(self):
                return "<userID:{0}, currencyTotal:{1}, items:{2}>".format(self.discordUserObject.id, str(self.currencyTotal), str(self.items))

            def __getstate__(self):
                    # Copy the object's state from self.__dict__ which contains
                    # all our instance attributes. Always use the dict.copy()
                    # method to avoid modifying the original state.
                    state = self.__dict__.copy()
                    # Remove the unpicklable entries.
                    state['discordUserObject'] = None
                    if self.houseMessageObject is not None:
                        state['houseMessageObject'] = self.houseMessageObject.id
                    return state

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
            "ANIMAL_TOAD": "🐸",
            "OPTION_LEDGER": "📒",
            "OPTION_ANIMAL_TRUCK": "🚚",
            "OPTION_ROOSTER": "🐓",
            "OPTION_REFRESH": "♻️",
            "RESEARCH_HORMONES": "💉",
            "RESEARCH_FINANCE": "🧮",
            "RESEARCH_RESEARCH": "📚",
            "RESEARCH_ALCHEMY": "⚗️",
            "ITEM_EGG": "🥚",
            "ITEM_MILK": "🥛",
            "ITEM_GLITTER": "✨",
            "ITEM_ROCKET_FUEL": "🛢️",
            "ITEM_ROCKET": "🚀",
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
            "ITEM_BROKEN_HOUSE":  ["$", -1], # TODO ["$", -1000000], 
            "UPGRADE_BULLETIN":   ["$", -1], # TODO ["$", -1000],
            "ANIMAL_CHICKEN":     ["$", -50000],
            "ANIMAL_RABBIT":      ["$", -75000],
            "ANIMAL_PIG":         ["$", -100000],
            "ANIMAL_COW":         ["$", -500000],
            "ANIMAL_UNICORN":     ["$", -5000000],
            "ITEM_EGG":           ["$", 1000], # note that these are positive
            "ITEM_MILK":          ["$", 10000], # note that these are positive
            "ITEM_ROCKET_FUEL":   ["ITEM_GLITTER", -100],
            "ITEM_ROCKET":        ["ITEM_ROCKET_FUEL", -100],
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

        WITCH_HUT_ITEMS = [
            "ITEM_ROCKET_FUEL",
            "ITEM_ROCKET",    
            "ITEM_EGG",       
            "ITEM_MILK",
        ]

        RESEARCH_TYPES = [
            "RESEARCH_HORMONES",
            "RESEARCH_FINANCE",
            "RESEARCH_RESEARCH",
            "RESEARCH_ALCHEMY"
        ]

        HOUSE_UPGRADE_COSTS = {
            "UPGRADE_OFFICE":  [
                ["$", -1],# TODO ["$",  -1000000],
            ],
            "UPGRADE_PADDOCK": [
                ["$", -1],# TODO ["$",  -5000000],
                ["$", -2],# TODO ["$", -30000000],
                ["$", -3],# TODO ["$", -80000000],
            ],
            "UPGRADE_LAB":     [
                ["$", -1],# TODO ["$",  -20000000],
                ["$", -2],# TODO ["$", -100000000],
            ],   
        }

        HOUSE_UPGRADE_AVAILABLE_EMOJI = {
            "UPGRADE_OFFICE": [
                ["OPTION_LEDGER"],
            ],
            "UPGRADE_PADDOCK": [
                ["OPTION_ANIMAL_TRUCK", "OPTION_ROOSTER"],
                ["OPTION_ANIMAL_TRUCK", "OPTION_ROOSTER"],
                ["OPTION_ANIMAL_TRUCK", "OPTION_ROOSTER"],
            ],
            "UPGRADE_LAB": [
                ["RESEARCH_HORMONES", "RESEARCH_FINANCE", "RESEARCH_RESEARCH"],
                ["RESEARCH_HORMONES", "RESEARCH_FINANCE", "RESEARCH_RESEARCH", "RESEARCH_ALCHEMY"],
            ],
        }

        def getAvailableEmojiForHouseUpgrades(self, playerID):
            result = []
            for upgradeKey in self.HOUSE_UPGRADE_AVAILABLE_EMOJI:
                upgradeLevel = self.players[playerID].items[upgradeKey]
                if upgradeLevel > 0:
                    if upgradeLevel >= len(self.HOUSE_UPGRADE_AVAILABLE_EMOJI[upgradeKey]):
                        upgradeLevel = len(self.HOUSE_UPGRADE_AVAILABLE_EMOJI[upgradeKey]) - 1

                    for optionKey in self.HOUSE_UPGRADE_AVAILABLE_EMOJI[upgradeKey][upgradeLevel]:
                        result.append(optionKey)

            return result

        ANIMAL_STATISTICS = {
            "ANIMAL_CHICKEN": {"REPRO_RATE": 0.24, "ITEM_PRODUCED": "ITEM_EGG",     "PROD_RATE": 0.8},
            "ANIMAL_RABBIT":  {"REPRO_RATE": 0.4,  "ITEM_PRODUCED": None,           "PROD_RATE": 0},
            "ANIMAL_PIG":     {"REPRO_RATE": 0.18, "ITEM_PRODUCED": None,           "PROD_RATE": 0},
            "ANIMAL_COW":     {"REPRO_RATE": 0.08, "ITEM_PRODUCED": "ITEM_MILK",    "PROD_RATE": 0.5},
            "ANIMAL_UNICORN": {"REPRO_RATE":    0, "ITEM_PRODUCED": "ITEM_GLITTER", "PROD_RATE": 0.05},
        }

        RESEARCH_LEVEL_THRESHOLDS = {
            "RESEARCH_HORMONES": [0, 1000, 5000, 10000, 20000, 50000, 100000, 500000, 1000000, 5000000, 10000000, 20000000, 30000000, 40000000, 50000000, 100000000, 1000000000, 10000000000, 99999999999999999999],
            "RESEARCH_FINANCE":  [0, 1000, 5000, 10000, 20000, 50000, 100000, 500000, 1000000, 5000000, 10000000, 20000000, 30000000, 40000000, 50000000, 100000000, 1000000000, 10000000000, 99999999999999999999],
            "RESEARCH_RESEARCH": [0, 1000, 5000, 10000, 20000, 50000, 100000, 500000, 1000000, 5000000, 10000000, 20000000, 30000000, 40000000, 50000000, 100000000, 1000000000, 10000000000, 99999999999999999999],
            "RESEARCH_ALCHEMY":  [0, 10], #TODO [10000000],
        }

        PADDOCK_SIZES = [0, 4, 6, 8]
        MAX_ANIMALS_PER_ROW = 14

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
            self.correctMarketPlayerIDs = [] # userIDs of players who have toggled the bull/camel emoji

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

        async def initializeBuildings(self):
            self.buildingMessageObjects["BLDG_BANK"] = await self.channel.send(":construction:")
            self.buildingMessageObjects["BLDG_SHOP_1"] = await self.channel.send(":construction:")
            self.buildingMessageObjects["BLDG_LOTTERY"] = await self.channel.send(":construction:")
            self.buildingMessageObjects["BLDG_ART_SOCIETY"] = await self.channel.send(":construction:")
          
            if "MILESTONE_FIRST_HOUSE" in self.milestones:
                print("Found milestone MILESTONE_FIRST_HOUSE")
                self.buildingMessageObjects["BLDG_HOUSE_DEPOT"] = await self.channel.send(":construction:")
                for playerID in self.players:
                    self.players[playerID].houseMessageObject = await self.channel.send(":construction:")

            if "MILESTONE_FIRST_ALCHEMY" in self.milestones:
                print("Found milestone MILESTONE_FIRST_ALCHEMY")
                self.buildingMessageObjects["BLDG_WITCH_HUT"] = await self.channel.send(":construction:")

            await self.reinitializeBuildings()

        async def reinitializeBuildings(self):
            for key in self.buildingMessageObjects:
                await self.reinitializeBuilding(key)

            for playerID in self.players:
                await self.reinitializePlayerBuilding(playerID)

        async def reinitializeBuilding(self, buildingKey, reinitEmojis = True):
            if reinitEmojis:
                await self.buildingMessageObjects[buildingKey].clear_reactions()

            if buildingKey == "BLDG_BANK":
                await self.buildingMessageObjects["BLDG_BANK"].edit(content = self.generateBankMessage())
                if reinitEmojis:
                    self.correctMarketPlayerIDs = [] 
                    await self.buildingMessageObjects["BLDG_BANK"].add_reaction(self.KEY_TO_EMOJI_MAP[self.bankMarketStatus])

            elif buildingKey == "BLDG_SHOP_1":
                await self.buildingMessageObjects["BLDG_SHOP_1"].edit(content = self.generateShop1Message())
                if reinitEmojis:
                    for item in self.SHOP_1_ITEMS:
                        await self.buildingMessageObjects["BLDG_SHOP_1"].add_reaction(self.KEY_TO_EMOJI_MAP[item])    

            elif buildingKey == "BLDG_LOTTERY":
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
                if reinitEmojis:
                    await self.buildingMessageObjects["BLDG_LOTTERY"].clear_reactions()
                    for item in self.LOTTO_KEY_TO_NUM_MAP:
                        await self.buildingMessageObjects["BLDG_LOTTERY"].add_reaction(self.KEY_TO_EMOJI_MAP[item])

            elif buildingKey == "BLDG_ART_SOCIETY":
                await self.buildingMessageObjects["BLDG_ART_SOCIETY"].edit(content = self.generateArtSocietyMessage())
                if reinitEmojis:
                    for item in self.ART_SOCIETY_ITEMS:
                        await self.buildingMessageObjects["BLDG_ART_SOCIETY"].add_reaction(self.KEY_TO_EMOJI_MAP[item])    

            elif buildingKey == "BLDG_HOUSE_DEPOT":
                await self.buildingMessageObjects["BLDG_HOUSE_DEPOT"].edit(content = self.generateHouseDepotMessage())
                if reinitEmojis:
                    for item in self.HOUSE_DEPOT_ITEMS:
                        await self.buildingMessageObjects["BLDG_HOUSE_DEPOT"].add_reaction(self.KEY_TO_EMOJI_MAP[item])

                if "MILESTONE_FIRST_PADDOCK" in self.milestones:
                    if reinitEmojis:
                        for item in self.ANIMAL_MART_ITEMS:
                            await self.buildingMessageObjects["BLDG_HOUSE_DEPOT"].add_reaction(self.KEY_TO_EMOJI_MAP[item])

            elif buildingKey == "BLDG_WITCH_HUT":
                await self.buildingMessageObjects["BLDG_WITCH_HUT"].edit(content = self.generateWitchHutMessage())
                if reinitEmojis:
                    for item in self.WITCH_HUT_ITEMS:
                        await self.buildingMessageObjects["BLDG_WITCH_HUT"].add_reaction(self.KEY_TO_EMOJI_MAP[item])


        async def reinitializePlayerBuilding(self, playerID, reinitEmojis = True):
            player = self.players[playerID]

            if player.houseMessageObject is None:
                return

            if reinitEmojis:
                await player.houseMessageObject.clear_reactions()

            await player.houseMessageObject.edit(content = self.generatePlayerHouseMessage(playerID))

            if reinitEmojis:
                for optionKey in self.getAvailableEmojiForHouseUpgrades(playerID):
                    await player.houseMessageObject.add_reaction(self.KEY_TO_EMOJI_MAP[optionKey])

            await self.recalculateResearchRatesForPlayer(playerID)


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

        ##################
        #### LOGIC HELPERS
        ##################

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

        def simulatePlayerAnimalMovement(self, playerID):
            player = self.players[playerID]
            possibleMoves = [0, -1, 1, -1*self.MAX_ANIMALS_PER_ROW, self.MAX_ANIMALS_PER_ROW]
            dimension = self.PADDOCK_SIZES[player.items["UPGRADE_PADDOCK"]] * self.MAX_ANIMALS_PER_ROW

            for animalKey in player.animalPositions:
                for i in range(len(player.animalPositions[animalKey])):
                    pos = player.animalPositions[animalKey][i]
                    newPos = pos + random.sample(possibleMoves, 1)[0]

                    occupied = []
                    for k,l in player.animalPositions.items():
                        for item in l:
                            occupied.append(item)

                    if newPos < 0 or newPos >= dimension or newPos in occupied:
                        newPos = pos
                    player.animalPositions[animalKey][i] = newPos

        def simulatePlayerAnimalProduction(self, playerID):
            player = self.players[playerID]
            for animalKey in player.animalPositions:
                if animalKey == "ANIMAL_CHICKEN" and player.roosterEnabled:
                    continue
                stats = self.ANIMAL_STATISTICS[animalKey]
                if stats["ITEM_PRODUCED"] is not None:
                    if random.random() < stats["PROD_RATE"] + (.02 * player.research["RESEARCH_HORMONES"]["LEVEL"]):
                        player.updateItems({stats["ITEM_PRODUCED"]: 1})

        def simulatePlayerAnimalReproduction(self, playerID):
            player = self.players[playerID]
            births = {}
            for animalKey in player.animalPositions:
                if animalKey == "ANIMAL_CHICKEN" and not player.roosterEnabled:
                    continue
                if len(player.animalPositions[animalKey]) >= 2:
                    births[animalKey] = 0
                    for i in range(int(len(player.animalPositions[animalKey])/2)):
                        if random.random() < self.ANIMAL_STATISTICS[animalKey]["REPRO_RATE"] + (.02 * player.research["RESEARCH_HORMONES"]["LEVEL"]):
                            births[animalKey] += 1

            for animalKey in births:
                player.addAnimal(animalKey)

        def calculateSocietyDonationPrices(self):
            SOCIETY_DONATION_INCREMENT = -2

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

        def calculateSalePrice(self, key):
            return [self.ITEM_COSTS[key][0], math.floor(self.ITEM_COSTS[key][1] * -0.25)]

        ##################
        #### GAME EVENT HANDLERS
        ##################

        async def onTick(self):
            # Determine the activity level of the bot
            tempSlumberLevel = 0
            SLUMBER_MINUTES_THRESHOLDS = [2, 15, 1440]
            BANK_SLUMBER_LEVEL_UPDATE_RATES = [1, 5, 30, 600] #in seconds
            PADDOCK_SLUMBER_LEVEL_UPDATE_RATES = [5, 10, 60, 900] #in seconds
            self.counter += 1
            lastInteractDelta = datetime.datetime.now() - self.lastInteraction
            for i in range(len(SLUMBER_MINUTES_THRESHOLDS)):
                if lastInteractDelta > datetime.timedelta(minutes=SLUMBER_MINUTES_THRESHOLDS[i]):
                    tempSlumberLevel = i + 1
            self.slumberLevel = tempSlumberLevel

            playerIDsWithHousesToRefresh = {}

            # PLAYER INCOME
            for playerID in self.players:
                player = self.players[playerID]

                finalIncome = player.income["$"]
                if player.discordUserObject.id in self.correctMarketPlayerIDs:
                    finalIncome *= 1.25
                player.currencyTotal["$"] += math.ceil(finalIncome)

                # PLAYER RESEARCH
                if self.counter % (5) == 0: # TODO should be 60
                    if player.houseMessageObject is not None and player.items["UPGRADE_LAB"] > 0:
                        for researchKey in player.research:
                            player.research[researchKey]["TOTAL"] += player.research[researchKey]["RATE"]
                            if player.research[researchKey]["LEVEL"] < len(self.RESEARCH_LEVEL_THRESHOLDS[researchKey]) - 1 and player.research[researchKey]["TOTAL"] >= self.getXPLevelOffset(researchKey, player.research[researchKey]["LEVEL"] + 1):
                                player.research[researchKey]["LEVEL"] += 1
                                if researchKey == "RESEARCH_ALCHEMY":
                                    if "MILESTONE_FIRST_ALCHEMY" not in self.milestones:
                                        self.milestones["MILESTONE_FIRST_ALCHEMY"] = playerID
                                        self.buildingMessageObjects["BLDG_WITCH_HUT"] = await self.channel.send(":construction:")
                                        await self.reinitializeBuilding("BLDG_WITCH_HUT")
                        playerIDsWithHousesToRefresh[playerID] = True

            # Update bank based off of activity level
            if self.counter % BANK_SLUMBER_LEVEL_UPDATE_RATES[self.slumberLevel] == 0: 
                await self.buildingMessageObjects["BLDG_BANK"].edit(content=self.generateBankMessage())

            # Update paddock positions and research display based off of activity level
            if self.counter % PADDOCK_SLUMBER_LEVEL_UPDATE_RATES[self.slumberLevel] == 0:
                for playerID in self.players:
                    player = self.players[playerID]
                    if player.houseMessageObject is not None and player.items["UPGRADE_PADDOCK"] > 0:
                        self.simulatePlayerAnimalMovement(playerID)
                        playerIDsWithHousesToRefresh[playerID] = True

            # Simulate item production for animals
            if self.counter % (60 * 10) == 0:
                for playerID in self.players:
                    self.simulatePlayerAnimalProduction(playerID)

            # Simulate animal reproduction
            if self.counter % (60 * 120) == 0:
                for playerID in self.players:
                    self.simulatePlayerAnimalReproduction(playerID)

            if self.counter % (60 * 30) == 0: 
                # Reset bank market status
                if self.bankMarketStatus == "BANK_STATUS_BULL":
                    self.bankMarketStatus = "BANK_STATUS_CAMEL"
                else:
                    self.bankMarketStatus = "BANK_STATUS_BULL"
                await self.buildingMessageObjects["BLDG_BANK"].clear_reactions()
                await self.buildingMessageObjects["BLDG_BANK"].add_reaction(self.KEY_TO_EMOJI_MAP[self.bankMarketStatus])
                self.correctMarketPlayerIDs = []
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

                    # make sure everyone only gets 3 numbers
                    playerNumberCounts = {} # maps player IDs to counts of lottery numbers selected
                    for i in range(10):
                        for j in range(len(playerLottoChoices[i]), 0, -1): # range through each playerLottoChoices list backwards so we can pop from it safely
                            i_playerIDs = j - 1
                            playerID = playerLottoChoices[i][i_playerIDs]
                            if playerID not in playerNumberCounts:
                                playerNumberCounts[playerID] = 0
                            if playerNumberCounts[playerID] < 3: 
                                playerNumberCounts[playerID] += 1
                            else: # TOO MANY CHOICES
                                playerNumberCounts[playerID].pop(i_userIDs)

                    # Count correct guesses
                    lottoMatchCounts = {} # maps playerIDs to counts of correct guesses
                    for winningNumber in self.todayLotteryNumbers:
                        for playerID in playerLottoChoices[winningNumber]:
                            if playerID not in lottoMatchCounts:
                                lottoMatchCounts[playerID] = 0
                            lottoMatchCounts[playerID] += 1

                    # Determine winners
                    self.yesterdayLotteryWinners = [[],[],[]] # third, second, first place
                    for playerID in lottoMatchCounts:
                        self.yesterdayLotteryWinners[lottoMatchCounts[playerID] - 1].append(playerID)

                    # Award winners
                    prizes = self.calculateLotteryPrizes(self.todayLotteryPrizePool)
                    for i in range(3):
                        if len(self.yesterdayLotteryWinners[i]) > 0:
                            prizePerPlayer = math.floor(prizes[i]/len(self.yesterdayLotteryWinners[i]))
                            for playerID in self.yesterdayLotteryWinners[i]:
                                self.players[playerID].transact(["$", prizePerPlayer])

                    # Begin next lottery
                    self.loop.create_task(self.refreshLottery())

            for playerID in playerIDsWithHousesToRefresh:
                print("Rerendering player house")
                await self.reinitializePlayerBuilding(playerID, reinitEmojis=False)

            # check for timed event triggers
            for key in self.eventCounters:
                self.eventCounters[key] -= 1
                if self.eventCounters[key] == 0:
                    if key == "EVENT_SHOOTING_STAR":
                        # TODO modify a building with the shooting star event
                        # TODO reset event counter
                        pass

        async def onReactionToggled(self, payload, toggledOn):
            if payload.channel_id == self.channel.id:
                playerID = payload.user_id
                if playerID in self.players.keys():
                    player = self.players[playerID]
                    self.lastInteraction = datetime.datetime.now()

                    for key in self.eventMessages:
                        if self.eventMessages[key].id == payload.message_id:
                            pass

                    if payload.emoji.name == self.KEY_TO_EMOJI_MAP["OPTION_REFRESH"]:
                        for buildingKey in self.buildingMessageObjects:
                            if self.buildingMessageObjects[buildingKey].id == payload.message_id:
                                await self.reinitializeBuilding(buildingKey)
                                return

                        for targetPlayerID in self.players:
                            if self.players[targetPlayerID].houseMessageObject is not None and payload.message_id == self.players[targetPlayerID].houseMessageObject.id:
                                await self.reinitializePlayerBuilding(targetPlayerID)
                                return

                    if payload.message_id == self.buildingMessageObjects["BLDG_BANK"].id:
                        if payload.emoji.name == self.KEY_TO_EMOJI_MAP[self.bankMarketStatus]:
                            if toggledOn:
                                self.correctMarketPlayerIDs.append(playerID)
                            elif playerID in self.correctMarketPlayerIDs:
                                self.correctMarketPlayerIDs.remove(playerID)

                    elif payload.message_id == self.buildingMessageObjects["BLDG_SHOP_1"].id:
                        for shopItem in self.SHOP_1_ITEMS:
                            if payload.emoji.name == self.KEY_TO_EMOJI_MAP[shopItem]:
                                itemCost = self.ITEM_COSTS[shopItem]
                                if player.currencyTotal[itemCost[0]] > max(0, -1 * itemCost[1]): # make sure that the player can afford it
                                    if shopItem == "ITEM_BROKEN_HOUSE":
                                        if "MILESTONE_FIRST_HOUSE" not in self.milestones:
                                            await self.initializeHouseDepot()
                                            self.milestones["MILESTONE_FIRST_HOUSE"] = playerID

                                        if player.items["ITEM_BROKEN_HOUSE"] > 0: # prevent players from getting more than one house
                                            return
                                        else:
                                            player.houseMessageObject = await self.channel.send(self.generatePlayerHouseMessage(playerID))
                                            await self.reinitializePlayerBuilding(playerID)
                                        
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
                                    await self.reinitializeBuilding("BLDG_ART_SOCIETY", False)

                    elif "BLDG_HOUSE_DEPOT" in self.buildingMessageObjects and payload.message_id == self.buildingMessageObjects["BLDG_HOUSE_DEPOT"].id:
                        for shopItem in self.HOUSE_DEPOT_ITEMS:
                            if payload.emoji.name == self.KEY_TO_EMOJI_MAP[shopItem]:
                                if payload.emoji.name == self.KEY_TO_EMOJI_MAP["UPGRADE_BULLETIN"]:
                                    itemCost = self.ITEM_COSTS["UPGRADE_BULLETIN"]
                                    if player.currencyTotal[itemCost[0]] > max(0, -1 * itemCost[1]): # make sure that the player can afford it
                                        self.loop.create_task(self.sendPlayerBulletinPrompt(player))
                                        player.transact(itemCost)
                                elif len(self.HOUSE_UPGRADE_COSTS[shopItem]) > player.items[shopItem]:
                                    itemCost = self.HOUSE_UPGRADE_COSTS[shopItem][player.items[shopItem]]
                                    if player.currencyTotal[itemCost[0]] > max(0, -1 * itemCost[1]): # make sure that the player can afford it
                                        player.updateItems({shopItem: 1})
                                        player.transact(itemCost)
                                        await self.reinitializePlayerBuilding(playerID)
                                        if shopItem == "UPGRADE_PADDOCK" and "MILESTONE_FIRST_PADDOCK" not in self.milestones:
                                            self.milestones["MILESTONE_FIRST_PADDOCK"] = player.discordUserObject.id
                                            await self.reinitializeBuilding("BLDG_HOUSE_DEPOT")

                    elif "BLDG_WITCH_HUT" in self.buildingMessageObjects and payload.message_id == self.buildingMessageObjects["BLDG_WITCH_HUT"].id:
                        if player.research["RESEARCH_ALCHEMY"]["LEVEL"] > 0:
                            for shopItem in self.WITCH_HUT_ITEMS:
                                if payload.emoji.name == self.KEY_TO_EMOJI_MAP[shopItem]:
                                    itemCost = self.ITEM_COSTS[shopItem]
                                    if itemCost[0] in self.KEY_TO_EMOJI_MAP:
                                        if player.items[itemCost[0]] >= -1 * itemCost[1]:
                                            player.updateItems({shopItem: 1})
                                            player.updateItems({itemCost[0]: itemCost[1]})
                                            if shopItem == "ITEM_ROCKET":
                                                await self.channel.send(":rocket: {} has won the game! :rocket:".format(player.discordUserObject.mention))
                                    else:
                                        if player.items[shopItem] > 0:
                                            player.updateItems({shopItem: -1})
                                            player.transact(itemCost)

                    elif payload.message_id == player.houseMessageObject.id:
                        allowedReactions = self.getAvailableEmojiForHouseUpgrades(playerID)
                        if self.EMOJI_TO_KEY_MAP[payload.emoji.name] in allowedReactions:
                            if payload.emoji.name == self.KEY_TO_EMOJI_MAP["OPTION_LEDGER"]:
                                await player.discordUserObject.send(content = player.generateItemDigest())
                            elif payload.emoji.name == self.KEY_TO_EMOJI_MAP["OPTION_ANIMAL_TRUCK"]:
                                self.loop.create_task(self.sendPlayerAnimalTruckPrompt(player))
                            elif payload.emoji.name == self.KEY_TO_EMOJI_MAP["OPTION_ROOSTER"]:
                                if toggledOn:
                                    player.roosterEnabled = True
                                elif playerID in self.correctMarketPlayerIDs:
                                    player.roosterEnabled = False
                                await player.houseMessageObject.edit(content = self.generatePlayerHouseMessage(playerID))
                            elif self.EMOJI_TO_KEY_MAP[payload.emoji.name] in self.RESEARCH_TYPES:
                                player.houseMessageObject = await self.channel.fetch_message(player.houseMessageObject.id)
                                await self.recalculateResearchRatesForPlayer(playerID)

                else:
                    user = self.client.get_user(playerID)
                    helpfulMessage = await self.channel.send("{} you are not registered with the game. Type `!register` to join!".format(user.mention))
                    await helpfulMessage.delete(delay=15)

        async def guildMessageReceived(self, message):
            if message.channel.id == self.channel.id:
                self.lastInteraction = datetime.datetime.now()

                if message.content == "!register":
                    self.registerPlayer(message.author)

                await message.delete(delay=15)

        async def directMessageReceived(self, message):
            if message.author.id in self.players:
                if message.content.split(" ")[0] == "!sell":
                    await self.sellAnimal(message.author.id, message)
                elif self.players[message.author.id].bulletinUpdatePending:
                    await self.bulletinUpdate(message.author.id, message)
                else:
                    await self.players[message.author.id].discordUserObject.send(content="I'm not expecting any messages from you.")

        ##################
        #### PROMPTS
        ##################

        async def sendPlayerBulletinPrompt(self, player):
            prompt = "What would you like your new bulletin to be? It is currently \"_{}_\".\n".format(player.houseBulletinString)
            await player.discordUserObject.send(prompt)
            player.bulletinUpdatePending = True

        async def sendPlayerAnimalTruckPrompt(self, player):
            animalRatesString = "Going rates for animals:\n"
            for animalKey in player.animalPositions:
                    animalRatesString += "{}: {}\n".format(IdleGameBot.GameSession.KEY_TO_EMOJI_MAP[animalKey], self.currencyString(self.calculateSalePrice(animalKey)))

            prompt = "{}\n {}\n To sell animals, type e.g. \"!sell 5 :cow:\"".format(player.generateAnimalDigest(), animalRatesString)

            await player.discordUserObject.send(prompt)

        ##################
        #### ON_MESSAGE ACTIONS
        ##################

        def registerPlayer(self, user):
            self.players[user.id] = IdleGameBot.GameSession.Player(user)
            print("Registered Player {}".format(user.name))

        async def bulletinUpdate(self, playerID, message):
            player = self.players[playerID]
            if player.bulletinUpdatePending:
                newBulletin = str.replace(message.content, "`", "")
                newBulletin = str.replace(newBulletin, "_", "")
                await player.discordUserObject.send(content="Your new bulletin message is now:\n\n _{}_\n\n Have a nice day!".format(newBulletin))
                player.houseBulletinString = newBulletin
                await player.houseMessageObject.edit(content = self.generatePlayerHouseMessage(playerID))
                player.bulletinUpdatePending = False

        async def sellAnimal(self, playerID, message):
            player = self.players[playerID]

            inputParts = message.content.split(" ") # ["!sell", "X", ":cow:"]
            count = int(inputParts[1])

            # Validate product
            if inputParts[2] not in self.EMOJI_TO_KEY_MAP:
                await player.discordUserObject.send(content="I didn't recognize what you want to sell.")
            elif self.EMOJI_TO_KEY_MAP[inputParts[2]] not in self.ANIMAL_STATISTICS:
                await player.discordUserObject.send(content="That's not an animal! We're not running a pawn shop here!")

            animalKey = self.EMOJI_TO_KEY_MAP[inputParts[2]]

            # Validate count
            if count == None:
                await player.discordUserObject.send(content="Sorry, how many did you want to sell? I'm not convinced that's a real number.")
            elif count < 0:
                await player.discordUserObject.send(content="Really funny, but I ain't getting fooled by that one.")

            if len(player.animalPositions[animalKey]) < count:
                await player.discordUserObject.send(content="It doesn't look to me like you have that many to sell!")
            else:
                individualSaleValue = self.calculateSalePrice(animalKey)
                sellValue = [individualSaleValue[0], individualSaleValue[1] * count]
                player.transact(sellValue)
                player.removeAnimals(animalKey, count)
                await player.discordUserObject.send(content="Sold {} {} for {}!".format(inputParts[1], inputParts[2], self.currencyString(sellValue)))

        async def gift(self, message):
            if message.author.id not in self.players:
                helpfulMessage = await self.channel.send("{} you are not registered with the game. Type `!register` to join!".format(user.mention))
                await helpfulMessage.delete(delay=15)
                return

            sourcePlayer = self.players()

            messageArr = message.content.split(" ")

            mention = messageArr[1]

            if messageArr[2][0] == "$":
                item = "$"
                count = int(messageArr[2][1:])
            else:
                count = int(messageArr[2])
                item = messageArr[3]

            targetPlayer = None
            for playerID in self.players:
                if self.players[playerID].discordUserObject.mention == mention:
                    targetPlayer = self.players[playerID]

            if targetPlayer is None:
                await message.channel.send("That player is not registered with the game.")
                return

            if count == None or count <= 0:
                await message.channel.send("You need to give a positive integer number of items to that player.")
                return

            if item != "$" and item not in self.EMOJI_TO_KEY_MAP:
                await message.channel.send("That is not an item i can send. Make sure you use an emoji or a dollar sign.")
                return

            if item == "$":
                if count < sourcePlayer.currencyTotal["$"]:
                    await message.channel.send("You don't have that much to give!")
                    return
                else:
                    sourcePlayer.transact({"$": -1 * count})
                    targetPlayer.transact({"$": count})
                    await message.channel.send("Transerred {} to {}".format(self.currencyString(["$", count]), mention))
                    return
            else:
                emojiKey = self.EMOJI_TO_KEY_MAP[item]
                if count < sourcePlayer.items[emojiKey]:
                    await message.channel.send("You don't have that many to give!")
                    return
                else:
                    sourcePlayer.updateItems({emojiKey: -1 * count})
                    targetPlayer.updateItems({emojiKey: count})
                    await message.channel.send("Transerred {} {} to {}".format(self.currencyString(["", count]), item, mention))
                    return

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
                if userID in self.correctMarketPlayerIDs:
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
                if chosenFeatures[0] == pair[0] and chosenFeatures[1] == pair[1]:
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

            if "MILESTONE_FIRST_PADDOCK" in self.milestones:
                resultString += "\n_Now carrying livestock for paddocks! Get two and maybe they'll do what animals do ;)_\n"

                animalInventory = [
                    ["ANIMAL_CHICKEN", self.ITEM_COSTS["ANIMAL_CHICKEN"], "+1 Chicken", "Produces eggs when they aren't reproducing."],
                    ["ANIMAL_RABBIT",  self.ITEM_COSTS["ANIMAL_RABBIT"],  "+1 Rabbit",  "Reproduces at a fast rate."],
                    ["ANIMAL_PIG",     self.ITEM_COSTS["ANIMAL_PIG"],     "+1 Pig",     "Reproduces at a medium rate."],
                    ["ANIMAL_COW",     self.ITEM_COSTS["ANIMAL_COW"],     "+1 Cow",     "Reproduces at a slow rate. Produces milk."],
                    ["ANIMAL_UNICORN", self.ITEM_COSTS["ANIMAL_UNICORN"], "+1 Unicorn", "Produces unicorn dust, does not reproduce."],
                ]

                resultString += self.prettyPrintInventory(animalInventory)
            
            return resultString

        def generateWitchHutMessage(self):
            emojiString = ":fire::woman_mage::fire:"
            resultString =  "`~~~~~~~~~~~~~~~~~~~~~~~~~~~~~`\n"
            resultString += emojiString + " **WITCH'S HUT** " + emojiString + "\n"
            resultString += "`~~~~~~~~~~~~~~~~~~~~~~~~~~~~~`\n\n"

            resultString += "_Eeeee-heee-hee! Welcome to my humble abode traveler. I trust you are well versed in the alchemic arts?_\n"

            shopInventory = [
                ["ITEM_ROCKET_FUEL", "-100 unicorn dust", "+1 Rocket Fuel", "Make things go fast. Requires alchemy."],
                ["ITEM_ROCKET",      "-100 rocket fuel",      "Win the game",   "What, just 'cuz I'm a witch I can't be a rocket scientist too?"],
                ["ITEM_EGG",         self.ITEM_COSTS["ITEM_EGG"],         "-1 egg",         "I'm feeling quite peckish, mind sparing a few eggs?"],
                ["ITEM_MILK",        self.ITEM_COSTS["ITEM_MILK"],        "-1 milk",        "I'd kill for a tall glass of milk right now."],
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

            resultString += "_{}_\n\n".format(player.houseBulletinString)

            if player.items["UPGRADE_OFFICE"] < len(self.HOUSE_UPGRADE_COSTS["UPGRADE_OFFICE"]):
                nextOfficeCost = self.currencyString(self.HOUSE_UPGRADE_COSTS["UPGRADE_OFFICE"][player.items["UPGRADE_OFFICE"]])
            else:
                nextOfficeCost = "MAX"
            if player.items["UPGRADE_PADDOCK"] < len(self.HOUSE_UPGRADE_COSTS["UPGRADE_PADDOCK"]):
                nextPaddockCost = self.currencyString(self.HOUSE_UPGRADE_COSTS["UPGRADE_PADDOCK"][player.items["UPGRADE_PADDOCK"]])
            else:
                nextPaddockCost = "MAX"
            if player.items["UPGRADE_LAB"] < len(self.HOUSE_UPGRADE_COSTS["UPGRADE_LAB"]):
                nextLabCost = self.currencyString(self.HOUSE_UPGRADE_COSTS["UPGRADE_LAB"][player.items["UPGRADE_LAB"]])
            else:
                nextLabCost = "MAX"

            # Office
            resultString += ":file_cabinet: __**Office Level {}**__ - _Next Upgrade: {}_\n".format(player.items["UPGRADE_OFFICE"], nextOfficeCost)
            if player.items["UPGRADE_OFFICE"] == 0:
                resultString += "_This room seems just drab enough to build a home office in._\n\n"
            elif player.items["UPGRADE_OFFICE"] == 1:
                resultString += "• :ledger: __Ledger__: Click to get a DM with your current item totals.\n\n"

            # Paddock
            resultString += ":park: __**Paddock Level {}**__ - _Next Upgrade: {}_\n".format(player.items["UPGRADE_PADDOCK"], nextPaddockCost)
            resultString += self.generatePaddock(playerID)

            # Lab
            resultString += ":microscope: __**Laboratory Level {}**__ - _Next Upgrade: {}_\n".format(player.items["UPGRADE_LAB"], nextLabCost)
            resultString += self.generateLaboratory(playerID)

            return resultString


        ##################
        #### DISPLAY HELPERS
        ##################

        def generatePaddock(self, playerID):
            player = self.players[playerID]
            paddockLevel = player.items["UPGRADE_PADDOCK"]
            if paddockLevel == 0:
                return "_You've got a lot of land here. Why not build an enclosure for some animals?_\n\n"

            resultString = "• :truck: __Truck__: Click to get a DM with animal management options.\n"

            playerAnimals = {}
            for animalKey in self.ANIMAL_STATISTICS:
                if animalKey in player.items:
                    playerAnimals[animalKey] = player.items[animalKey]

            roosterPrompt = "This guy is going to have a hard time doing his job without any hens."
            if len(player.animalPositions["ANIMAL_CHICKEN"]) >= 2:
                if player.roosterEnabled:
                    roosterPrompt = "[ON] Toggle off to have your chickens produce eggs instead of new chickens."
                else:
                    roosterPrompt = "[OFF] Toggle on to have your chickens produce new chickens instead of eggs."


            resultString += "• :rooster: __Rooster__: {}\n".format(roosterPrompt)

            resultString += "—————————————————————\n"

            rows = [[" "*6 for j in range(self.MAX_ANIMALS_PER_ROW)] for i in range(self.PADDOCK_SIZES[paddockLevel])] # hardcoded constant, rough space width of an emoji

            # populate the rows with emoji
            for animalKey in player.animalPositions:
                for animalPos in player.animalPositions[animalKey]:
                    rows[int(animalPos/self.MAX_ANIMALS_PER_ROW)][animalPos%self.MAX_ANIMALS_PER_ROW] = self.KEY_TO_EMOJI_MAP[animalKey]

            for row in rows:
                resultString += "|" + "".join(row) + "|\n"

            resultString += "—————————————————————\n"

            return resultString

        def generateLaboratory(self, playerID):
            player = self.players[playerID]
            labLevel = player.items["UPGRADE_LAB"]
            resultString = ""
            if labLevel == 0:
                resultString += "_This room seems just dark and stormy enough to build a laboratory in._\n\n"
            elif labLevel == 1:
                itemDescriptions = {
                    "RESEARCH_HORMONES": ":syringe: **Hormones** Lvl {} - `({}/{} + {}/min)` Increase animal item production and reproduction by 5% per level\n",
                    "RESEARCH_FINANCE":  ":abacus:  **Finance** Lvl {} - `({}/{} + {}/min)` Increase income by 2% per level\n",
                    "RESEARCH_RESEARCH": ":books: **Research Practices** Lvl {} - `({}/{} + {}/min)` Increase research rates by 10% per level\n",
                    "RESEARCH_ALCHEMY":  ":alembic: **Alchemy** Lvl {} - `({}/{} + {}/min)` Unlock the secrets of alchemy\n",
                }

                for researchKey in self.HOUSE_UPGRADE_AVAILABLE_EMOJI["UPGRADE_LAB"][labLevel]:
                    currentXP = player.research[researchKey]["TOTAL"]
                    currentLevel = player.research[researchKey]["LEVEL"]

                    xpForLastLevel = self.getXPLevelOffset(researchKey, currentLevel)
                    currentXPMinusPreviousRequirements = currentXP - xpForLastLevel
                    
                    if currentLevel == len(self.RESEARCH_LEVEL_THRESHOLDS[researchKey]) - 1:
                        currentLevel = "MAX"
                        goalXP = "MAX"
                    else:
                        requiredXPMinusPreviousRequirements = self.RESEARCH_LEVEL_THRESHOLDS[researchKey][currentLevel + 1] - xpForLastLevel
                        goalXP = self.currencyString(["", requiredXPMinusPreviousRequirements])

                    resultString += itemDescriptions[researchKey].format(
                        currentLevel,
                        self.currencyString(["", currentXPMinusPreviousRequirements]),
                        goalXP,
                        self.currencyString(["", player.research[researchKey]["RATE"]]),
                    )

            return resultString

        # remember that you need to refresh the housemessageobject to get the current reactions before calling this
        async def recalculateResearchRatesForPlayer(self, playerID):
            player = self.players[playerID]

            if player.items["UPGRADE_LAB"] < 1:
                return

            totalRate = 4 * (1.0 + .1 * player.research["RESEARCH_RESEARCH"]["LEVEL"])

            enabledResearchKeys = []
            for reaction in player.houseMessageObject.reactions:
                if self.EMOJI_TO_KEY_MAP[reaction.emoji] in self.HOUSE_UPGRADE_AVAILABLE_EMOJI["UPGRADE_LAB"][player.items["UPGRADE_LAB"]]:
                    for user in await reaction.users().flatten():
                        if user.id == playerID:
                            enabledResearchKeys.append(self.EMOJI_TO_KEY_MAP[reaction.emoji])

            for key in player.research:
                player.research[key]["RATE"] = 0

            for key in enabledResearchKeys:
                player.research[key]["RATE"] = totalRate / len(enabledResearchKeys)

        # Gives the amount of XP required to reach the level
        def getXPLevelOffset(self, researchKey, level):
            tot = 0
            for i in range(level + 1):
                tot += self.RESEARCH_LEVEL_THRESHOLDS[researchKey][i]

            return tot

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

            if currencyTuple[0] in self.KEY_TO_EMOJI_MAP:
                unit = self.KEY_TO_EMOJI_MAP[currencyTuple[0]]
            else:
                unit = currencyTuple[0]
            currencyInteger = round(currencyTuple[1], 1)
            negativeString = ""
            if currencyInteger < 0:
                negativeString = "-"
                currencyInteger = currencyInteger * -1

            def doCommas(numStr):
                if len(numStr) > 3:
                    return numStr[:-3] + "," + numStr[-3:]
                else:
                    return numStr

            currencyStringRawSplit = str(currencyInteger).split(".")
            currencyStringRaw = currencyStringRawSplit[0]
            result = currencyStringRaw

            if len(currencyStringRaw) > 15:
                result = doCommas(currencyStringRaw[0:len(currencyStringRaw) - 15]) + "q"
            elif len(currencyStringRaw) > 12:
                result = currencyStringRaw[0:len(currencyStringRaw) - 12] + "." + currencyStringRaw[len(currencyStringRaw) - 12] + "t"
            elif len(currencyStringRaw) > 9:
                result = currencyStringRaw[0:len(currencyStringRaw) - 9] + "." + currencyStringRaw[len(currencyStringRaw) - 9] + "b"
            elif len(currencyStringRaw) > 6:
                result = currencyStringRaw[0:len(currencyStringRaw) - 6] + "." + currencyStringRaw[len(currencyStringRaw) - 6] + "m"
            elif len(currencyStringRaw) > 3:
                result = currencyStringRaw[0:len(currencyStringRaw) - 3] + "." + currencyStringRaw[len(currencyStringRaw) - 3] + "k"
            else:
                if len(currencyStringRawSplit) == 1:
                    result = currencyStringRaw
                else:
                    result = currencyStringRaw + "." + currencyStringRawSplit[1]

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

        def __getstate__(self):
                # Copy the object's state from self.__dict__ which contains
                # all our instance attributes. Always use the dict.copy()
                # method to avoid modifying the original state.
                state = self.__dict__.copy()
                # Remove the unpicklable entries.
                state['loop'] = None
                state['client'] = None
                state['guild'] = None
                state['channel'] = None
                state['buildingMessageObjects'] = {}
                state['buildingMessageIDs'] = {key: self.buildingMessageObjects[key].id for key in self.buildingMessageObjects}
                state['channelID'] = self.channel.id

                return state

        def __setstate__(self, state):
            self.__dict__.update(state)
            self.lastInteraction = datetime.datetime.now()

    ##################
    #### BOT INITIALIZATION
    ##################

    def __init__(self, prefix="!", greeting="Hello", farewell="Goodbye"):
        super().__init__(prefix, greeting, farewell)

        self.gameSessions = {} # maps guildIDs to GameSession objects
        self.backupFilenames = [
            'storage/{}/backup1.pickle'.format(self.getName()),
            'storage/{}/backup2.pickle'.format(self.getName())
        ]

    async def on_ready(self):
        await super().on_ready()

        newestFile = ""
        for filename in self.backupFilenames:
            if os.path.isfile(filename):
                lastUpdated = os.path.getmtime(filename)
                if newestFile == "" or lastUpdated > os.path.getmtime(newestFile):
                    newestFile = filename

        if newestFile != "":
            await self.load(newestFile)

        for guild in self.client.guilds:
            gameChannel = None

            for channel in guild.channels:
                if channel.name == GAME_CHANNEL_NAME and isinstance(channel, discord.TextChannel):
                    print("Found " + guild.name + "." + channel.name)
                    gameChannel = channel

            if gameChannel is not None:
                if guild.id not in self.gameSessions:
                    print("Running first time initialization")
                    gameSession = IdleGameBot.GameSession(self.loop, self.client, guild, gameChannel)
                    self.gameSessions[guild.id] = gameSession

                    await self.gameSessions[guild.id].initializeBuildings()

                else:
                    gameSession = self.gameSessions[guild.id]

                    missingMessage = None
                    for buildingKey in gameSession.buildingMessageObjects:
                        if gameSession.buildingMessageObjects[buildingKey] == -1:
                           missingMessage = buildingKey
                           break 

                    for playerID in gameSession.players:
                        player = gameSession.players[playerID]
                        if player.houseMessageObject == -1:
                            missingMessage = "Player House for {}".format(player.discordUserObject.name)

                    if missingMessage is not None:
                        print("Missing message for {}, running first time initialization with existing save file".format(missingMessage))
                        await gameSession.channel.purge()
                        await gameSession.initializeBuildings()
                    else:
                        print("Reinitializing buildings")
                        await gameSession.reinitializeBuildings()

                self.loop.create_task(IdleGameBot.tick(gameSession))

        self.loop.create_task(self.backup())

    ##################
    #### BOT EVENT HANDLERS
    ##################

    async def tick(gameSession):
        while True:
            await gameSession.onTick()
            await asyncio.sleep(1)

    async def backup(self):
        while True:
            await asyncio.sleep(10) # TODO longer time
            filename = self.backupFilenames.pop(0)

            if not os.path.isfile(filename):
                os.makedirs(os.path.dirname(filename), exist_ok=True)

            self.backupFilenames.append(filename)
            with open(filename, 'wb') as f:
                pickle.dump(self.gameSessions, f, pickle.HIGHEST_PROTOCOL)
            print("Successfully backed up to {}".format(filename))

    async def load(self, filename):
        loadedSessions = pickle.load(open(filename, "rb"))
        for guild in self.client.guilds:
            if guild.id not in loadedSessions:
                print("Could not load session for {}".format(guild.name))
            else:
                gameSession = loadedSessions[guild.id]
                gameSession.loop = self.loop
                gameSession.client = self.client
                gameSession.guild = guild
                gameSession.channel = await self.client.fetch_channel(gameSession.channelID)

                for buildingKey in gameSession.buildingMessageIDs:
                    try:
                        gameSession.buildingMessageObjects[buildingKey] = await gameSession.channel.fetch_message(gameSession.buildingMessageIDs[buildingKey])
                    except discord.errors.NotFound:
                        gameSession.buildingMessageObjects[buildingKey] = -1

                for playerID in gameSession.players:
                    player = gameSession.players[playerID]
                    player.discordUserObject = await self.client.fetch_user(playerID)
                    if player.houseMessageObject is not None:
                        try:
                            player.houseMessageObject = await gameSession.channel.fetch_message(player.houseMessageObject)
                        except discord.errors.NotFound:
                            player.houseMessageObject = -1

                self.gameSessions[guild.id] = gameSession

                print("Successfully loaded from {}".format(filename))

    async def on_message(self, message):
        await super().on_message(message)
        if message.author.id != self.client.user.id:
            # This logic is problematic if users are playing in multiple guilds
            if isinstance(message.channel, discord.DMChannel):
                for guildID in self.gameSessions:
                    if message.author.id in self.gameSessions[guildID].players:
                        await self.gameSessions[guildID].directMessageReceived(message)
                        return

                print("Unauthorized DM from user {}".format(message.author.name))
            elif message.guild.id in self.gameSessions.keys():
                await self.gameSessions[message.guild.id].guildMessageReceived(message)

    async def on_raw_reaction_add(self, payload):
        await super().on_raw_reaction_add(payload)
        if payload.guild_id in self.gameSessions.keys() and payload.user_id != self.client.user.id:
            await self.gameSessions[payload.guild_id].onReactionToggled(payload, True)

    async def on_raw_reaction_remove(self, payload):
        await super().on_raw_reaction_remove(payload)
        if payload.guild_id in self.gameSessions.keys() and payload.user_id != self.client.user.id:
            await self.gameSessions[payload.guild_id].onReactionToggled(payload, False)