import discord
import asyncio
import random
import urllib.request
import re
import os, io
import pickle, json, csv
import threading
import datetime, time

from .generic import DiscordBot

class TTRPGBot(DiscordBot):
    EMOJI_MAP = {
        "yes": "✅",
        "no": "🚫",
    }

    async def manageInventory(self, message, params):
        pass

    async def manageNotes(self, message, params):
        pass

    async def manageHP(self, message, params):
        pass

    async def manageStats(self, message, params):
        pass

    async def manageConfig(self, message, params):
        pass

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
                output += "Could not parse roll.`\n"
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
        await message.delete(delay=5)


    async def handleExport(self, message, params):
        pass

    async def fetchGMs(self):
        for guild in self.client.guilds:
            for role in guild.roles:
                if role.name == "GM" or role.name == "DM":
                    self.guildGMRoleMap[guild.id] = role
                    print("Found GM role for " + guild.name)
            if guild.id not in self.guildGMRoleMap:
                print("Couldn't find GM role for " + guild.name)

    # throws ValueError exceptions
    def parseSumDiff(self, inputString, allowDecimal=False):
        deltaString = inputString.replace(",", "").strip()
        sign = 1
        if deltaString[0] == "-":
            sign = -1
            deltaString = deltaString[1:]
        elif deltaString[0] == "+":
            deltaString = deltaString[1:]

        if allowDecimal:
            absDelta = float(deltaString) # can except
        else:
            absDelta = int(deltaString) # can except

        return sign * absDelta

    async def refreshGMList(self, message, params):
        await self.fetchGMs()

    async def on_ready(self):
        await self.fetchGMs()

    async def on_raw_reaction_add(self, payload):
        await super().on_raw_reaction_add(payload)

    ###################
    #     Startup     #
    ###################

    def __init__(self, prefix="!", greeting="Hello", farewell="Goodbye"):
        super().__init__(prefix, greeting, farewell)

        self.serverConfigFilePath = "storage/{}/serverconfig.json".format(self.getName())
        self.charactersFilePath = "storage/{}/characterdata.json".format(self.getName())

        self.guildGMRoleMap = {} # { guildID: guildGMRole }
        self.guildConfigMap = {} # { guildID: {stats: []} }
        self.guildCharactersMap = {} # { guildID: [{playerID: int, }, ...] }

        self.addCommand('roll', self.rollDice, lambda x: True, "Roll dice", "4d3 + 4 + 1d20")
        self.addCommand('r', self.rollDice, lambda x: True, "Roll dice", "4d3 + 4 + 1d20")