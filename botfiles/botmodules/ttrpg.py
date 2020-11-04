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

    async def damagePlayer(self, message, params):
        #     splitParams = params.split(" ")
        #     amount = int(splitParams[0])
        #     target = message.author
        #     if len(splitParams) > 1:
        #         amount = int(splitParams[1])
        #         target = await self.getUserFromMention(splitParams[0])
        self.manageHP(message, params, "HP", -1)
        pass

    async def healPlayer(self, message, params):
        #     splitParams = params.split(" ")
        #     amount = int(splitParams[0])
        #     target = message.author
        #     if len(splitParams) > 1:
        #         amount = int(splitParams[1])
        #         target = await self.getUserFromMention(splitParams[0])
        self.manageHP(message,params, "HP", 1)
        pass

    async def manageCharacter(self, message, params):
        if not await self.assertGuildConfigured(message.channel):
            return

        guildStats = self.guildConfigMap[message.guild.id]["stats"]

        def helpManageCharacter(user, subParams):
            pass

        # !c [@] new Name HP/STAT1/STAT2
        async def new(user, subParams):
            newCharPattern = "^(.+)\s+(\d+(?:\/\d+){" + str(len(guildStats) - 1) + "})$"

            charMatch = re.match(newCharPattern, " ".join(subParams))

            if charMatch is None:
                return await helpManageCharacter(user, ["new"])
                return

            name = charMatch[1]
            newStatsArr = charMatch[2].split("/")

            if (len(newStatsArr) != len(guildStats)):
                await message.channel.send("Invalid number of stats, expected {}".format("/".join(newStatsArr)))
                return

            for i in range(len(newStatsArr)):
                try:
                    newStatsArr[i] = int(newStatsArr[i])
                except ValueError:
                    await message.channel.send("Could not parse an integer for stat {}".format(guildStats[i]))
                    return

            if user.id not in self.guildCharactersMap[message.guild.id]:
                self.guildCharactersMap[message.guild.id][user.id] = {"name": name, "stats": {}, "inventory": {}, "notes": []}
            for i in range(len(newStatsArr)):
                self.guildCharactersMap[message.guild.id][user.id]["stats"][guildStats[i]] = {"current": newStatsArr[i], "max": newStatsArr[i]}

            await message.channel.send(":sparkles: New Character Created!\nWelcome to the party, {}!".format(name))

        # !c [@] name John Wick
        async def name(user, subParams):
            if not await self.assertPlayerExists(message.channel, user):
                return

            newName = " ".join(subParams)

            if len(newName) == 0:
                return await helpManageCharacter(user, ["name"])

            self.guildCharactersMap[message.guild.id][user.id]["name"] = newName
            await message.channel.send("{}'s character is now named {}".format(user.mention, newName))

        # !c [@] stat WIS 10
        async def stat(user, subParams):
            if not await self.assertPlayerExists(message.channel, user):
                return

            if len(subParams) == 0:
                return await helpManageCharacter(user, ["stat"])

            statKey = subParams[0].upper()
            try:
                newVal = int(subParams[1])
            except ValueError:
                await message.channel.send("Could not parse a value for stat {}".format(statKey))

            self.guildCharactersMap[message.guild.id][user.id]["stats"][statKey]["current"] = newVal
            await message.channel.send("{}'s current {} stat is now {}".format(
                self.guildCharactersMap[message.channel.guild.id][user.id]["name"],
                statKey,
                str(newVal)
            ))

            
        # !c [@] maxstat WIS 15
        async def maxstat(user, subParams):
            if not await self.assertPlayerExists(message.channel, user):
                return

            if len(subParams) == 0:
                return await helpManageCharacter(user, ["stat"])

            statKey = subParams[0].upper()
            try:
                newVal = int(subParams[1])
            except ValueError:
                await message.channel.send("Could not parse a value for stat {}".format(statKey))

            self.guildCharactersMap[message.guild.id][user.id]["stats"][statKey]["max"] = newVal
            await message.channel.send("{}'s max {} stat is now {}".format(
                self.guildCharactersMap[message.channel.guild.id][user.id]["name"],
                statKey,
                str(newVal)
            ))

        # !c [@] info
        async def info(user, subParams):
            if not await self.assertPlayerExists(message.channel, user):
                return

            char = self.guildCharactersMap[message.channel.guild.id][user.id]
            stats = self.guildConfigMap[message.channel.guild.id]["stats"]

            maxStatStrLength = 0
            for stat in stats:
                maxStatStrLength = max(maxStatStrLength, len(stat))

            maxItemKeyStrLength = 0
            for itemKey in char["inventory"].keys():
                maxItemKeyStrLength = max(maxItemKeyStrLength, len(itemKey))

            dividerStr = "__# {} #__\n"
            output = "📄 {}'s Character Sheet:\n**Name:** {}\n".format(user.mention, char["name"])
            output += dividerStr.format("STATS")
            for stat in stats:
                output += "**{}**{}: {}/{}\n".format(stat, " "*(maxStatStrLength - len(stat)), char["stats"][stat]["current"], char["stats"][stat]["max"])
            output += dividerStr.format("INVENTORY")
            for itemKey, itemObj in char["inventory"].items():
                output += "{}{} ({}) - {}".format(itemKey, " "*(maxItemKeyStrLength - len(itemKey)), itemObj["count"], itemObj["desc"])
            output += dividerStr.format("NOTES")
            for note_i in range(len(char["notes"])):
                output += "{}. {}".format(note_i, char["notes"][note_i])
            
            await message.channel.send(output)


        subcommands = {
            "help": helpManageCharacter,
            "new": new,
            "name": name,
            "stat": stat,
            "maxstat": maxstat,
            "info": info,
        }

        tokens = params.split(" ")
        if len(params) == 0:
            tokens = ["info"]

        if tokens[0] in subcommands.keys():
            await subcommands[tokens[0]](message.author, tokens[1:])
        elif tokens[1] in subcommands.keys():
            user = token # TODO
            await subcommands[tokens[1]](user, tokens[2:])
        else:
            await message.channel.send("Invalid subcommand, expected one of [{}]".format(",".join(subcommands.keys())))
        await message.delete(delay=5)


    async def manageGuildConfig(self, message, params):
        if not await self.assertUserIsGM(message.channel, message.author):
            return

        async def helpConfig(subArgs):
            helpMsg = await message.channel.send("e.g. `!config stats STR/CON/DEX/WIS/INT/CHA`\n*(this message will self destruct in 30 seconds)")
            await helpMsg.delete(delay=30)

        async def configureStats(subArgs):
            stats = []
            for arg in subArgs:
                stats += re.split("[,/]", arg)

            hpIndex = None
            for i in range(len(stats)):
                stats[i] = stats[i].upper()
                if stats[i] == "HP":
                    hpIndex = i
            if hpIndex is not None:
                stats.pop(hpIndex)
            stats = ["HP"] + stats

            newStatsString = "/".join(stats)
            oldStatsString = "None Configured"
            if message.channel.guild.id in self.guildConfigMap:
                oldStatsString = "/".join(self.guildConfigMap[message.channel.guild.id]["stats"])

            self.guildConfigMap[message.channel.guild.id] = {"stats": stats}
            if message.guild.id not in self.guildCharactersMap:
                self.guildCharactersMap[message.channel.guild.id] = {}

            await message.channel.send(":tools: Available character stats on this server have changed from `{}` to `{}`. Please note that character data may be affected.".format(
                oldStatsString,
                newStatsString
            ))

        subcommands = {
            "help": helpConfig,
            "stats": configureStats
        }

        tokens = params.split(" ")
        if len(params) == 0:
            tokens = ["help"]

        if (tokens[0] in subcommands.keys()):
            await subcommands[tokens[0]](tokens[1:])
        else:
            await message.channel.send("Invalid subcommand, expected one of [{}]".format(",".join(subcommands.keys())))
        await message.delete(delay=5)


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
                output += "Could not parse roll`\n"
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

    # # sign can be -1, 0, or 1. if it's 0, take param as value, not delta
    # async def managePlayerStat(self, message, params, stat, sign):
    #     splitParams = params.split(" ")
    #     amount = int(splitParams[0])
    #     target = message.author
    #     if len(splitParams) > 1:
    #         amount = int(splitParams[1])
    #         target = await self.getUserFromMention(splitParams[0])

    #     if not self.checkForPlayerInCharactersMap(message.channel, target):
    #             await message.channel.send("{} does not have a character registered. Use `!c new` to create one!".format(target.mention))

    #     statBlock = self.guildCharactersMap[message.channel.guild.id][target.id]["stats"][stat]

    #     newAmount = amount
    #     if sign != 0:
    #         currentAmount = statBlock["current"]
    #         newAmount = currentAmount + sign * abs(amount)

    #     if newAmount > statBlock["max"]:
    #         newAmount = statBlock["max"]

    #     statBlock["current"] = newAmount

    #     await message.channel.send("FIXME {}={}".format(stat, newAmount))

    # sign can be -1, 0, or 1. if it's 0, take param as value, not delta
    async def managePlayerStat(self, channel, target, stat, amount, sign):
        if not self.checkForPlayerInCharactersMap(channel, target):
                await channel.send("{} does not have a character registered. Use `!c new` to create one!".format(target.mention))

        statBlock = self.guildCharactersMap[channel.guild.id][target.id]["stats"][stat]

        newAmount = amount
        if sign != 0:
            currentAmount = statBlock["current"]
            newAmount = currentAmount + sign * abs(amount)

        if newAmount > statBlock["max"]:
            newAmount = statBlock["max"]

        statBlock["current"] = newAmount

        await channel.send("FIXME {}={}".format(stat, newAmount))

    async def assertPlayerExists(self, channel, user):
        if user.id not in self.guildCharactersMap[channel.guild.id]:
            await channel.send("{} does not have a registered character! Try `!c help new`.")
            return False
        return True

    async def assertGuildConfigured(self, channel):
        if channel.guild.id not in self.guildConfigMap:
            await channel.send("This server is not configured. Try `!config`.")
            return False
        return True

    async def assertUserIsGM(self, channel, user):
        if not self.userIsGM(channel.guild.id, user):
            await channel.send("{} is not a GM.".format(user.mention))
            return False
        return True

    # returns user object from "@Wish" mention string
    async def getUserFromMention(self, mentionStr):
        pass

    # returns true if the user has a registered character in the channel
    async def checkForPlayerInCharactersMap(self, channel, user):
        pass

    def userIsGM(self, guildID, user):
        return self.guildGMRoleMap[guildID] in user.roles

    async def fetchGMs(self):
        for guild in self.client.guilds:
            for role in guild.roles:
                if role.name == "GM" or role.name == "DM":
                    self.guildGMRoleMap[guild.id] = role
                    print("Found GM role for {}".format(guild.name))
            if guild.id not in self.guildGMRoleMap:
                print("Couldn't find GM role for " + guild.name)

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

        # guildCharactersMap = { 
        #    guildID: {
        #        userID: { 
        #           characterName: string,
        #           stats: {
        #               hp:   {current: int, max: int},
        #               key1: {current: int, max: int},
        #               key2: ...
        #           },
        #           inventory: {
        #               key1: {count: int, desc: str},
        #               ...
        #           },
        #           notes: [str, ...],
        #        }, ...
        #    }
        # }
        self.guildCharactersMap = {}

        self.addCommand('roll', self.rollDice, lambda x: True, "Roll dice", "4d3 + 4 + 1d20")
        self.addCommand('r', self.rollDice, lambda x: True)
        self.addCommand('config', self.manageGuildConfig, lambda x: True, "Manage guild configurations")
        self.addCommand('character', self.manageCharacter, lambda x: True, "Manage a character", "!character name John Wick")
        self.addCommand('char', self.manageCharacter, lambda x: True)
        self.addCommand('c', self.manageCharacter, lambda x: True)