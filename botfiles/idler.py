import discord
import asyncio
import random
import urllib.request
import re
import os, io
import threading
import datetime, time

from .generic import DiscordBot

class IdlerBot(DiscordBot):
    class Player:
        def __init__(self, discordUserObject, importString=""):
            self.discordUserID = discordUserObject

            if importString == "":
                self.currency = {
                    "DOLLARS": 0,
                }

                self.upgrades = {
                    "LEMONS":         0,
                    "MELONS":         0,
                    "MONEY_PRINTERS": 0,
                }
            else:
                pass #TODO import from string

    ##################
    #### INITIALIZATION
    ##################

    def __init__(self, prefix="!", greeting="Hello", farewell="Goodbye"):
        super().__init__(prefix, greeting, farewell)

        self.channel = -1
        self.players = {}
        self.buildingMessageObjects = {}

        self.counter = 0
        self.lastInteraction = -1
        self.slumber = False
        self.eventCounters = {}
        self.eventMessages = {}

        threading.Timer(1, onTick).start()

        self.addCommand('register', self.registerPlayer, lambda x: True, "Register with the game!", "")

    async def initializeBuildings(self):
        self.buildingMessageObjects["BLDG_CONFIG"] = await self.channel.send("")
        self.buildingMessageObjects["BLDG_BANK"] = await self.channel.send(self.generateBankMessage())
        self.buildingMessageObjects["BLDG_SHOP_1"] = await self.channel.send(self.generateShop1Message())
        self.buildingMessageObjects["BLDG_LOTTERY"] = await self.channel.send(self.generateLotteryMessage())

        self.buildingMessageObjects["BLDG_CONFIG"].edit(self.encodeState())

    async def on_ready(self):
        await super().on_ready()
        await self.importState()

    ##################
    #### EVENT HANDLERS
    ##################

    async def onTick(self):
        SLUMBER_MINUTES_THRESHOLD = 30
        self.counter += 1

        self.slumber = datetime.now() - self.lastInteraction > datetime.timedelta(minutes=SLUMBER_MINUTES_THRESHOLD)

        # 1 tick actions
        for player in this.players:
            player.currency["DOLLARS"] += player.upgrades["LEMONS"]
            player.currency["DOLLARS"] += 5 * player.upgrades["MELONS"]
            player.currency["DOLLARS"] += 50 * player.upgrades["MONEY_PRINTERS"]

        if self.counter % 15 == 0: 
            if not slumber:
                await self.buildingMessageObjects["BLDG_BANK"].edit(generateBankMessage)

        if self.counter % 60 == 0:
            await self.buildingMessageObjects["BLDG_CONFIG"].edit(self.encodeState())

        if self.counter % (SLUMBER_MINUTES_THRESHOLD * 60) == 0: #slumber update
            if slumber:
                await self.buildingMessageObjects["BLDG_BANK"].edit(generateBankMessage)

        # check for timed event triggers
        for key in self.eventCounters:
            self.eventCounters[key] -= 1
            if self.eventCounters[key] == 0:
                if key == "EVENT_SHOOTING_STAR":
                    # TODO modify a building with the shooting star event
                    # TODO reset event counter
                    pass


    async def on_message(self, message):
        if self.channel.id == message.channel.id:
            self.lastInteraction = datetime.now()
            pass

    async def on_raw_reaction_add(self, payload):
        await super().on_raw_reaction_add(payload)
        if self.channel.id == payload.channel_id:
            self.lastInteraction = datetime.now()
            await self.reactionToggled(payload, True)

    async def on_raw_reaction_remove(self, payload):
        await super().on_raw_reaction_remove(payload)
        if self.channel.id == payload.channel_id:
            self.lastInteraction = datetime.now()
            await self.reactionToggled(payload, False)

    async def reactionToggled(self, payload, toggledOn):
        messageID = -1 # TODO get messageID

        for key in self.eventMessages:
            if self.eventMessages[key].id == messageID:
                pass

        if messageID == self.buildingMessageObjects["BLDG_BANK"]:
            pass
        else if messageID == self.buildingMessageObjects["BLDG_SHOP_1"]:
            pass
        else if messageID == self.buildingMessageObjects["BLDG_LOTTERY"]:
            pass

    ##################
    #### BUILDING MESSAGES
    ##################

    def generateBankMessage(self):
        bankEmojiString = ":bank::bank::bank:"
        if self.slumber:
            bankEmojiString = ":bank::bank::zzz:"
        resultString =  "`~~~~~~~~~~~~~~~~~~~~~~~~~`\n`"
        resultString += bankEmojiString + " **BANK** " + bankEmojiString + "\n"
        resultString += "`~~~~~~~~~~~~~~~~~~~~~~~~~`\n"

        longestNameLength = 0
        # figure out what length to buffer names at
        for player in players:
            if len(player.discordUserObject.name) > longestNameLength:
                longestNameLength = len(player.discordUserObject.name)

        resultString += "```"
        for player in players:
            bufferSpaces = ' '*(longestNameLength - len(player.discordUserObject.name)
            resultString += player.discordUserObject.name + bufferSpaces + currencyString("$", player.currency["DOLLARS"])
        resultString += "```"

        return resultString

    # currencyString("$", "123456") => "$123,456"
    # currencyString("%", "123456789") => "%123m"
    def currencyString(unit, currencyInteger):
        def doCommas(numStr):
            result = numStr[-3:-1]
            numStr = numStr[0:-4]
            while len(numStr) > 2:
                result = numStr[-3:-1] + "," + result
                numStr = numStr[0:-4]
            return result

        currencyStringRaw = str(currencyInteger)
        result = currencyStringRaw

        # TODO decimal place for mbtq
        if len(currencyStringRaw) > 15:
            result = doCommas(currencyStringRaw[0:len(currencyStringRaw) - 14]) + "q"
        if len(currencyStringRaw) > 12:
            result = currencyStringRaw[0:len(currencyStringRaw) - 12] + "t"
        if len(currencyStringRaw) > 9:
            result = currencyStringRaw[0:len(currencyStringRaw) - 9] + "b"
        if len(currencyStringRaw) > 6:
            result = currencyStringRaw[0:len(currencyStringRaw) - 6] + "m"
        else:
            result = doCommas(currencyStringRaw)

        return unit + result

    emojiMap = {
        "ITEM_LEMON":         ":lemon:",
        "ITEM_MELON":         ":melon:",
        "ITEM_MONEY_PRINTER", ":printer:",
        "ITEM_HOUSE":         ":house_abandoned:"
    }

    def generateShop1Message(self):
        shopEmojiString = ":convenience_store::convenience_store::convenience_store:"
        resultString =  "`~~~~~~~~~~~~~~~~~~~~~~~~`\n`"
        resultString += shopEmojiString + " **SHOP** " + shopEmojiString + "\n"
        resultString += "`~~~~~~~~~~~~~~~~~~~~~~~~`\n\n"

        shopInventory = [
            ["ITEM_LEMON",                 ["$", 10],  "+$1/sec", "Lemons into lemonade, right?"],
            ["ITEM_MELON",                 ["$", 49],  "+$5/sec", "Melons into melonade... Right...?"],
            ["ITEM_MONEY_PRINTER",        ["$", 469], "+$50/sec", "Top of the line money printer!"],
            ["ITEM_BROKEN_HOUSE",     ["$", 1000000], "A house!", "It ain't much, but it's home."],
        ]

        resultString += prettyPrintInventory(shopInventory)
        return resultString

    # inventoryList = [ [emojiID, priceTuple, effectDescription, flavorText], ... ]
    def prettyPrintInventory(inventoryList):
        result = ""

        maxPriceLength  = 0 
        maxEffectLength = 0
        for item in inventoryList:
            pass # TODO space buffers

        for item in inventoryList:
            priceStr = currencyString(item[1][0], item[1][1])
            result += "• {} `{}|{}|{}`".format(
                emojiMap[item[0]],
                " "*(maxPriceLength - len(priceStr)) + priceStr,
                " "*(maxEffectLength - len(item[2])) + item[2],
                item[3]
            )

        return result

    def generateLotteryMessage(self):
        lotteryEmojiString = ":moneybag::moneybag::moneybag:"
        resultString =  "`~~~~~~~~~~~~~~~~~~~~~~~~`\n`"
        resultString += lotteryEmojiString + " **SHOP** " + lotteryEmojiString + "\n"
        resultString += "`~~~~~~~~~~~~~~~~~~~~~~~~`\n\n"

        resultString += "_Every day the lottery hint will change! Choose your three lucky numbers and you could be a winner! (Only the lowest three numbers selected will be counted. Terms and conditions apply.)_\n"

        # select the 3 lotto numbers
        lotteryNumbers = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"]
        self.chosenNumbers = []
        while len(chosenNumbers) < 3:
            self.chosenNumbers.add(lotteryNumbers.pop(randrange(0, len(lotteryNumbers))))
        self.chosenNumbers.sort()

        # determine notable features about the drawing
        features = {
            "PRIMES": 0,
            "EVENS": 0,
            "ODDS": 0,
            "THREES": 0,
            "LUCKYSEVEN": 0,
        }
        for num in chosenNumbers:
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
                candidates.add(key)
        chosenFeatures = []
        while len(chosenFeatures) < 2:
            chosenFeatures.add(candidates.pop(randrange(0, len(candidates))))

        FEATURE_STRINGS = {
            "PRIMES": "{} primes",
            "EVENS": "{} even numbers" ,
            "ODDS": "{} odd numbers",
            "THREES": "{} numbers divisible by three"
        }

        sevenIndex = -1
        if chosenFeatures[0] == "LUCKYSEVEN":
            sevenIndex = 0
        else if chosenFeatures[1] == "LUCKYSEVEN":
            sevenIndex = 1

        hintString = ""
        if sevenIndex > -1:
            featureNameKey = chosenFeatures[~sevenIndex]
            hintString = "There are {} and a Lucky Seven!!".format(FEATURE_STRINGS[featureNameKey].format(features[chosenFeatures[~sevenIndex]]))
        else:
            hintString = "There are {} and {}.".format(FEATURE_STRINGS[chosenFeatures[0]], FEATURE_STRINGS[chosenFeatures[1]])

        resultString += "\n__Today's Hint__: {}".format(hintString)

        return resultString


    ##################
    #### ENCODING
    ##################

    CURRENT_VERSION = "0"
    ENCODING_CHARSET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890~!@#$%^&*()<>?/-_+=[]{}|"

    BLOCK_0 = "0" # Version Number
    BLOCK_1 = "1" # System Message IDs
    BLOCK_2 = "2" # Milestones
    BLOCK_3 = "3" # Reserved
    BLOCK_4 = "4" # Reserved
    BLOCK_5 = "5" # Reserved
    BLOCK_6 = "6" # Player statistics

    ENCODING_INDEX_BLDG_BANK = 0
    ENCODING_INDEX_BLDG_STORE_1 = 1

    # convert a base 10 integer string into a base len(ENCODING_CHARSET) integer string
    def compressInt(num):
        result = ""
        radix = len(ENCODING_CHARSET)
        while num > 0:
            rem = num % radix
            result = ENCODING_CHARSET[rem] + result
            num = num / radix

        return result

    # encode the state as a string
    def encodeState(self):
        # BLOCK_0 - Version
        stateString = CURRENT_VERSION

        stateString += "."
        # BLOCK_1 - System Message IDs

        stateString += ",".join(
            compressInt(self.buildingMessageObjects["BLDG_CONFIG"].id),
            compressInt(self.buildingMessageObjects["BLDG_BANK"].id),
            compressInt(self.buildingMessageObjects["BLDG_SHOP_1"].id),
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


