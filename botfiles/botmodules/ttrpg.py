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

    # async def manageInventory(self, message, params):

    #     async def addItems(user, subTokens):

    #     subcommands = {
    #         "help": helpNotes,
    #         "add": addItems,
    #         "remove": removeItems,
    #         "list": listNotes,
    #     }

    #     tokens = params.split(" ")
    #     if len(params) == 0:
    #         tokens = ["info"]

    #     if tokens[0] in subcommands.keys():
    #         await subcommands[tokens[0]](message.author, tokens[1:])
    #     elif tokens[1] in subcommands.keys():
    #         user = token # TODO
    #         await subcommands[tokens[1]](user, tokens[2:])
    #     else:
    #         await message.channel.send("Invalid subcommand, expected one of [{}]".format(",".join(subcommands.keys())))
    #     await message.delete(delay=10)

    async def manageNotes(self, message, params):
        async def helpNotes(user, subTokens):
            if len(subTokens) == 0:
                return await message.channel.send(":thought_balloon: Available subcommands: `{}`\n\n Try `!note help add`!\n".format("`, `".join(subcommands.keys())))    
            elif subTokens[0] == "help":
                await message.channel.send(":thought_balloon: Aren't you clever.")
            elif subTokens[0] == "add":
                return await message.channel.send(":thought_balloon: `note add` adds a new note to your character sheet. Expected format: `!note add The salty seadog is named Ishmael.`".format("/".join(self.guildConfigMap[message.channel.guild.id]["stats"])))
            elif subTokens[0] == "remove":
                return await message.channel.send(":thought_balloon: `note remove` deletes the given note # from your character. Expected format: `!note remove 5`")
            elif subTokens[0] == "list":
                return await message.channel.send(":thought_balloon: `note list` prints out all of your notes!")
            elif subTokens[0] == "move":
                return await message.channel.send(":thought_balloon: `note move` allows you to rearrange your notes. The first number you provide is the note you're moving, the second number is the position you're moving it to. Expected format: `!note move 1 2`")
            else:
                return await message.channel.send(":thought_balloon: I don't know that subcommand. Try `!note help`.")

        async def addNote(user, subTokens):
            if not await self.assertUserIsSelfOrGM(message.channel, message.author, user):
                return

            note = " ".join(subTokens)

            if len(note) > 0:
                self.guildCharactersMap[message.channel.guild.id][user.id]["notes"].append(note)
                return await message.channel.send(":notepad_spiral: {} noted:\n> {}".format(self.guildCharactersMap[message.channel.guild.id][user.id]["name"], note))
            else:
                return await helpNotes(user, ["add"])

        async def removeNote(user, subTokens):
            if not await self.assertUserIsSelfOrGM(message.channel, message.author, user):
                return

            noteIndex = None
            try:
                noteIndex = int(subTokens[0]) - 1
            except ValueError:
                return await message.channel.send("You need to tell me the number of the entry in the list.")
            note = self.guildCharactersMap[message.channel.guild.id][user.id]["notes"][noteIndex]
            del self.guildCharactersMap[message.channel.guild.id][user.id]["notes"][noteIndex]
            await message.channel.send(":notepad_spiral: {} removed note:\n> {}".format(self.guildCharactersMap[message.channel.guild.id][user.id]["name"], note))

        async def listNotes(user, subTokens):
            if not await self.assertPlayerExists(message.channel, user):
                return

            char = self.guildCharactersMap[message.channel.guild.id][user.id]
            output = ":notepad_spiral: **{}'s Notes:**\n".format(char["name"])
            for note_i in range(len(char["notes"])):
                output += "**{}.** {}\n".format(note_i + 1, char["notes"][note_i])
            await message.channel.send(output)

        async def moveNote(user, subTokens):
            if not await self.assertUserIsSelfOrGM(message.channel, message.author, user):
                return

            if len(subTokens) < 2:
                return await helpNotes(user, ["move"])

            notes = self.guildCharactersMap[message.channel.guild.id][user.id]["notes"]

            try:
                oldIndex = int(subTokens[0]) - 1
                newIndex = int(subTokens[1]) - 1
            except ValueError:
                oldIndex = -1
                newIndex = -1

            if oldIndex < 0 or oldIndex > len(notes) or newIndex < 0:
                return await message.channel.send("That is an invalid note index.")

            note = notes.pop(oldIndex)
            notes = notes[:newIndex] + [note] + notes[newIndex:]
            self.guildCharactersMap[message.channel.guild.id][user.id]["notes"] = notes

            await message.channel.send("Successfully moved the following note to position {}:\n> {}".format(min(newIndex + 1, len(notes)), note))


        subcommands = {
            "help": helpNotes,
            "add": addNote,
            "remove": removeNote,
            "list": listNotes,
            "move": moveNote,
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
            await message.channel.send("Invalid subcommand, expected one of `{}`".format(",".join(subcommands.keys())))
        await message.delete(delay=10)

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

        async def helpManageCharacter(user, subTokens):
            if len(subTokens) == 0:
                return await message.channel.send(":thought_balloon: Available subcommands: `{}`\n\n Try `!help char new`!\n".format("`, `".join(subcommands.keys())))    
            elif subTokens[0] == "help":
                await message.channel.send(":thought_balloon: Aren't you clever.")
            elif subTokens[0] == "new":
                return await message.channel.send(":thought_balloon: `char new` creates a new character. Expected format: `!char new Character Name {}`".format("/".join(self.guildConfigMap[message.channel.guild.id]["stats"])))
            elif subTokens[0] == "name":
                return await message.channel.send(":thought_balloon: `char name` changes a character's name. Expected format: `!char name New Name`")
            elif subTokens[0] == "stat":
                return await message.channel.send(":thought_balloon: `char stat` updates the CURRENT value of a stat. Expected format: `!char stat {} 69`".format(random.choice(self.guildConfigMap[message.channel.guild.id]["stats"])))
            elif subTokens[0] == "maxstat":
                return await message.channel.send(":thought_balloon: `char maxstat` updates the MAX value of a stat. Expected format: `!char maxstat {} 420`".format(random.choice(self.guildConfigMap[message.channel.guild.id]["stats"])))
            elif subTokens[0] == "info":
                return await message.channel.send(":thought_balloon: `char info` prints out the character sheet!")
            elif subTokens[0] == "delete":
                return await message.channel.send(":thought_balloon: `char delete` deletes a character. Expected format: `!char delete @Wish` Be careful!")
            elif subTokens[0] == "list":
                return await message.channel.send(":thought_balloon: `char list` gets a list of all the characters!")
            else:
                return await message.channel.send(":thought_balloon: I don't know that subcommand. Try `!char help`.")

        # !c [@] new Name HP/STAT1/STAT2
        async def new(user, subTokens):
            newCharPattern = "^(.+)\s+(\d+(?:\/\d+){" + str(len(guildStats) - 1) + "})$"

            charMatch = re.match(newCharPattern, " ".join(subTokens))

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
        async def name(user, subTokens):
            if not await self.assertUserIsSelfOrGM(message.channel, message.author, user):
                return

            newName = " ".join(subTokens)

            if len(newName) == 0:
                return await helpManageCharacter(user, ["name"])

            self.guildCharactersMap[message.guild.id][user.id]["name"] = newName
            await message.channel.send("{}'s character is now named {}".format(user.mention, newName))

        # !c [@] stat WIS 10
        async def stat(user, subTokens):
            if not await self.assertUserIsSelfOrGM(message.channel, message.author, user):
                return

            if len(subTokens) == 0:
                return await helpManageCharacter(user, ["stat"])

            statKey = subTokens[0].upper()
            try:
                newVal = int(subTokens[1])
            except ValueError:
                await message.channel.send("Could not parse a value for stat {}".format(statKey))

            self.guildCharactersMap[message.guild.id][user.id]["stats"][statKey]["current"] = newVal
            await message.channel.send("{}'s current {} stat is now {}".format(
                self.guildCharactersMap[message.channel.guild.id][user.id]["name"],
                statKey,
                str(newVal)
            ))

            
        # !c [@] maxstat WIS 15
        async def maxstat(user, subTokens):
            if not await self.assertUserIsSelfOrGM(message.channel, message.author, user):
                return

            if len(subTokens) == 0:
                return await helpManageCharacter(user, ["stat"])

            statKey = subTokens[0].upper()
            try:
                newVal = int(subTokens[1])
            except ValueError:
                await message.channel.send("Could not parse a value for stat {}".format(statKey))

            self.guildCharactersMap[message.guild.id][user.id]["stats"][statKey]["max"] = newVal
            await message.channel.send("{}'s max {} stat is now {}".format(
                self.guildCharactersMap[message.channel.guild.id][user.id]["name"],
                statKey,
                str(newVal)
            ))

        # !c [@] info
        async def info(user, subTokens):
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
            output = ":memo: {}'s Character Sheet:\n**Name:** {}\n".format(user.mention, char["name"])
            output += dividerStr.format("STATS")
            for stat in stats:
                output += "**{}**{}: {}/{}\n".format(stat, " "*(maxStatStrLength - len(stat)), char["stats"][stat]["current"], char["stats"][stat]["max"])
            output += dividerStr.format("INVENTORY")
            for itemKey, itemObj in char["inventory"].items():
                output += "{}{} ({}) - {}".format(itemKey, " "*(maxItemKeyStrLength - len(itemKey)), itemObj["count"], itemObj["desc"])
            output += dividerStr.format("NOTES")
            for note_i in range(len(char["notes"])):
                output += "**{}.** {}\n".format(note_i + 1, char["notes"][note_i])
            
            await message.channel.send(output)

        async def delete(user, subTokens):
            if not await self.assertUserIsSelfOrGM(message.channel, message.author, user):
                return

            await message.channel.send("Character info for posterity:")
            await info(user, subTokens)
            name = self.guildCharactersMap[message.channel.guild.id][user.id]["name"]
            del self.guildCharactersMap[message.channel.guild.id][user.id]
            await message.channel.send(":skull_crossbones: {} was deleted! さよなら!".format(name))

        async def listChars(user, subTokens):
            output = ":notebook_with_decorative_cover: Characters in party:\n"
            if len(self.guildCharactersMap[message.channel.guild.id].items()) == 0:
                output += "Nobody :pensive:"
            for userID, char in self.guildCharactersMap[message.channel.guild.id].items():
                output += "{}, played by {}\n".format(char["name"], self.client.get_user(userID).mention)
            await message.channel.send(output)

        subcommands = {
            "help": helpManageCharacter,
            "new": new,
            "name": name,
            "stat": stat,
            "maxstat": maxstat,
            "info": info,
            "delete": delete,
            "list": listChars,
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
            await message.channel.send("Invalid subcommand, expected one of `{}`".format(",".join(subcommands.keys())))
        await message.delete(delay=10)


    async def manageGuildConfig(self, message, params):
        async def helpConfig(subArgs):
            if not await self.assertUserIsGM(message.channel, message.author):
                return

            helpMsg = await message.channel.send(":thought_balloon: Config Help:\n • `!config stats` Configure stats on character sheets e.g. `!config stats STR/CON/DEX/WIS/INT/CHA`\n• `!config list` List configured stats.")
            await helpMsg.delete(delay=30)

        async def configureStats(subArgs):
            if not await self.assertUserIsGM(message.channel, message.author):
                return

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

        async def listStats(subArgs):
            if not await self.assertGuildConfigured(message.channel): 
                return
            await message.channel.send("Stats are: {}".format("/".join(self.guildConfigMap[message.channel.guild.id]["stats"])))

        subcommands = {
            "help": helpConfig,
            "list": listStats,
            "stats": configureStats
        }

        tokens = params.split(" ")
        if len(params) == 0:
            if message.channel.guild.id in self.guildConfigMap:
                tokens = ["list"]
            else:
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

    # Returns True if a character is associated with the given guild (from channel) and user, otherwise False and prints message
    async def assertPlayerExists(self, channel, user):
        if user.id not in self.guildCharactersMap[channel.guild.id]:
            await channel.send("{} does not have a registered character! Try `!c help new`.".format(user.mention))
            return False
        return True

    # Returns True if the guild has been configured, otherwise False and prints message
    async def assertGuildConfigured(self, channel):
        if channel.guild.id not in self.guildConfigMap:
            await channel.send("This server is not configured. Try `!config`.")
            return False
        return True

    # Returns True if user is a GM, otherwise False and prints message
    async def assertUserIsGM(self, channel, user):
        if not self.userIsGM(channel.guild.id, user):
            await channel.send("{} is not a GM.".format(user.mention))
            return False
        return True

    # Returns True if instigatingUser is targetUser or a GM, otherwise returns false and prints message
    async def assertUserIsSelfOrGM(self, channel, instigatingUser, targetUser):
        if await self.assertPlayerExists(channel, targetUser):
            if instigatingUser.id == targetUser.id:
                return True
            else:
                return await self.assertUserIsGM(channel, instigatingUser)
        return False

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
        self.guildConfigMap = {} # { guildID: {destructMessages: int, stats: []} }

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
        self.addCommand('config', self.manageGuildConfig, lambda x: True, "Manage server configurations")
        self.addCommand('character', self.manageCharacter, lambda x: True, "Manage a character")
        self.addCommand('char', self.manageCharacter, lambda x: True)
        self.addCommand('c', self.manageCharacter, lambda x: True)
        self.addCommand('note', self.manageNotes, lambda x: True, "Manage your notes")
        self.addCommand('notes', self.manageNotes, lambda x: True)
        self.addCommand('n', self.manageNotes, lambda x: True)