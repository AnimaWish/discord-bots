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
    # EMOJI_MAP = {
    #     "yes": "✅",
    #     "no": "🚫",
    # }

    async def manageInventory(self, message, params):
        async def helpItems(user, subTokens):
            if len(subTokens) == 0 or subTokens[0] not in subcommands:
                return await message.channel.send(":thought_balloon: Available subcommands: `{}`\n\n Try `!item help add`\n".format("`, `".join(subcommands.keys())))    
            elif subTokens[0] == "help":
                await message.channel.send(":thought_balloon: Aren't you clever.")
            elif subTokens[0] == "add":
                return await message.channel.send(":thought_balloon: `item add` adds 1 or more items to your character's inventory. Note that the name of the item must be a hyphenated string - no spaces. Each semicolon-deliniated item after it adds a tag. Expected format: `!item add 50 gold-pieces shiny; valuable`")
            elif subTokens[0] == "remove":
                return await message.channel.send(":thought_balloon: `item remove` removes 1 or more items from your character's inventory. Expected format: `!item remove 50 gold-pieces`")
            elif subTokens[0] == "tag":
                if len(subTokens) == 1:
                    return await message.channel.send(":thought_balloon: `item tag` has available subcommands: `{}`\n\n Try `!item help tag add`\n".format("`, `".join(["add", "remove"])))    
                elif subTokens[1] == "add":
                    return await message.channel.send(":thought_balloon: `item tag add` adds a tag to an item. Expected format: `!item tag add really cool`")
                elif subTokens[1] == "remove":
                    return await message.channel.send(":thought_balloon: `item tag remove` removess a tag from an item. Expected format: `!item tag remove ugly`")
            elif subTokens[0] == "list": 
                return await message.channel.send(":thought_balloon: `item list` gives you a list of your items")

        # !item add 50 gp
        # !item add Magic Sword "A sword that is magical"
        async def addItems(user, subTokens):
            if not await self.assertUserIsSelfOrGM(message.channel, message.author, user):
                return

            addPattern = "^(?:(\d+)\s+)?(\w+(?:-\w+)*)\s*(?:\s+(.+))?"
            addMatch = re.match(addPattern, " ".join(subTokens))
            if addMatch == None:
                return await helpItems(user, ["add"])

            count = int(addMatch[1]) if addMatch[1] is not None else 1
            itemAlias = addMatch[2]
            tagArray = addMatch[3].split(",") if addMatch[3] is not None else []

            if count == 0:
                return await message.channel.send("You keep that up and you'll have 0 frontal lobes when I'm done with you")

            inventory = self.guildCharactersMap[message.channel.guild.id][user.id]["inventory"]

            newCountString = ""
            if itemAlias not in inventory:
                inventory[itemAlias] = {"count": count, "tags": tagArray}
            else:
                inventory[itemAlias]["count"] += count
                inventory[itemAlias]["tags"] += tagArray
                newCountString = "\nNew Total: {}".format(inventory[itemAlias]["count"])

            return await message.channel.send(":shopping_bags: {}x `{}` added to inventory{}{}".format(
                count, itemAlias,
                "!" if len(tagArray) == 0 else " with tags `{}`!".format("`; `".join(tagArray)),
                newCountString
            ))


        async def removeItems(user, subTokens):
            if not await self.assertUserIsSelfOrGM(message.channel, message.author, user):
                return

            removePattern = "^(?:(\d+)\s+)?(\w+(?:-\w+)*)"
            removeMatch = re.match(removePattern, " ".join(subTokens))
            if removeMatch == None:
                return await helpItems(user, ["remove"])

            count = int(removeMatch[1])
            itemAlias = removeMatch[2]

            inventory = self.guildCharactersMap[message.channel.guild.id][user.id]["inventory"]
            if itemAlias not in inventory:
                return await message.channel.send("{} is not in {}'s inventory!".format(itemAlias, self.guildCharactersMap[message.channel.guild.id][user.id]["name"]))
            if count > inventory[itemAlias]["count"]:
                return await message.channel.send("You only have {} of that item!".format(inventory[itemAlias]["count"]))

            inventory[itemAlias]["count"] -= count

            return await message.channel.send(":shopping_bags: {}x `{}` removed from inventory.".format(count, itemAlias))

        async def manageItemTags(user, subTokens):
            if not await self.assertUserIsSelfOrGM(message.channel, message.author, user):
                return

            if subTokens[0] != "add" and subTokens[0] != "remove":
                return await helpItems(user, ["tag"])

            inventory = self.guildCharactersMap[message.channel.guild.id][user.id]["inventory"]

            itemAlias = subTokens[1]
            if itemAlias not in inventory:
                return await message.channel.send("There is no item named `{}` in your inventory.".format(itemAlias))

            tag = " ".join(subTokens[2:])
            if len(tag) == 0:
                return await helpItems(user, ["tags", subTokens[0]])

            if subTokens[0] == "add":
                inventory[itemAlias]["tags"].append(tag)
                return await message.channel.send(":shopping_bags: `{}` tag added to `{}`!".format(tag, itemAlias))
            elif subTokens[0] == "remove":
                if tag not in inventory[itemAlias]["tags"]:
                    return await message.channel.send("There is no tag `{}` on your `{}`.".format(tag, itemAlias))
                inventory[itemAlias]["tags"].remove(tag)
                return await message.channel.send(":shopping_bags: `{}` tag removed from `{}`.".format(tag, itemAlias))


        async def listItems(user, subTokens):
            if not await self.assertPlayerExists(message.channel, user):
                return
            output = ":shopping_bags: **{}'s Items:**\n".format(self.guildCharactersMap[message.channel.guild.id][user.id]["name"])

            maxItemKeyStrLength = 0
            for itemKey in self.guildCharactersMap[message.channel.guild.id][user.id]["inventory"].keys():
                maxItemKeyStrLength = max(maxItemKeyStrLength, len(itemKey))

            for itemKey, itemObj in self.guildCharactersMap[message.channel.guild.id][user.id]["inventory"].items():
                if itemObj["count"] == 0:
                    continue
                tagString = ""
                if len(itemObj["tags"]) > 0:
                    tagString = " - `{}`".format("`, `".join(itemObj["tags"]))
                output += "{}{} ({}){}\n".format(itemKey, " "*(maxItemKeyStrLength - len(itemKey)), itemObj["count"], tagString)

            await message.channel.send(output)


        subcommands = {
            "help": helpItems,
            "add": addItems,
            "remove": removeItems,
            "tag": manageItemTags,
            "list": listItems,
        }

        tokens = params.split(" ")
        if len(params) == 0:
            tokens = ["help"]

        if tokens[0] in subcommands.keys():
            await subcommands[tokens[0]](message.author, tokens[1:])
        elif tokens[1] in subcommands.keys():
            user = token # TODO
            await subcommands[tokens[1]](user, tokens[2:])
        else:
            await message.channel.send("Invalid subcommand, expected one of `{}`".format("`, `".join(subcommands.keys())))
        if self.getDeleteDelay(message.channel.guild.id) > 0:
            await message.delete(delay=self.getDeleteDelay(message.channel.guild.id))

    async def manageNotes(self, message, params):
        # !note help
        async def helpNotes(user, subTokens):
            if len(subTokens) == 0 or subTokens[0] not in subcommands:
                return await message.channel.send(":thought_balloon: Available subcommands: `{}`\n\n Try `!note help add`\n".format("`, `".join(subcommands.keys())))    
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
                return await message.channel.send(":thought_balloon: I don't know that subcommand. Try `!note help`")

        # !note add Hello World
        async def addNote(user, subTokens):
            if not await self.assertUserIsSelfOrGM(message.channel, message.author, user):
                return

            note = " ".join(subTokens)

            if len(note) > 0:
                self.guildCharactersMap[message.channel.guild.id][user.id]["notes"].append(note)
                return await message.channel.send(":notepad_spiral: {} noted:\n> {}".format(self.guildCharactersMap[message.channel.guild.id][user.id]["name"], note))
            else:
                return await helpNotes(user, ["add"])

        # !note remove 1
        # input indices are 1 indexed
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

        # !note list
        async def listNotes(user, subTokens):
            if not await self.assertPlayerExists(message.channel, user):
                return

            char = self.guildCharactersMap[message.channel.guild.id][user.id]
            output = ":notepad_spiral: **{}'s Notes:**\n".format(char["name"])
            for note_i in range(len(char["notes"])):
                output += "**{}.** {}\n".format(note_i + 1, char["notes"][note_i])
            await message.channel.send(output)

        # !note move 1 2
        # input indices are 1 indexed
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
            await message.channel.send("Invalid subcommand, expected one of `{}`".format("`, `".join(subcommands.keys())))
        if self.getDeleteDelay(message.channel.guild.id) > 0:
            await message.delete(delay=self.getDeleteDelay(message.channel.guild.id))

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
            if len(subTokens) == 0 or subTokens[0] not in subcommands:
                return await message.channel.send(":thought_balloon: Available subcommands: `{}`\n\n Try `!help char new`\n".format("`, `".join(subcommands.keys())))    
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
                return await message.channel.send(":thought_balloon: I don't know that subcommand. Try `!char help`")

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
                if itemObj["count"] == 0:
                    continue
                tagString = ""
                if len(itemObj["tags"]) > 0:
                    tagString = " - `{}`".format("`, `".join(itemObj["tags"]))
                output += "{}{} ({}){}\n".format(itemKey, " "*(maxItemKeyStrLength - len(itemKey)), itemObj["count"], tagString)
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
            await message.channel.send("Invalid subcommand, expected one of `{}`".format("`, `".join(subcommands.keys())))
        if self.getDeleteDelay(message.channel.guild.id) > 0:
            await message.delete(delay=self.getDeleteDelay(message.channel.guild.id))


    async def manageGuildConfig(self, message, params):
        async def helpConfig(subTokens):
            if message.channel.guild.id not in self.guildConfigMap:
                await message.channel.send(":thought_balloon: This server is not configured. use `!config stats` to configure it.")
            if len(subTokens) == 0 or subTokens[0] not in subcommands:
                return await message.channel.send(":thought_balloon: Available subcommands: `{}`\n Try `!config help stats`\n".format("`, `".join(subcommands.keys())))    
            elif subTokens[0] == "help":
                await message.channel.send(":thought_balloon: Aren't you clever.")
            elif subTokens[0] == "stats":
                return await message.channel.send(":thought_balloon: `config stats` configures the stats that characters can have in this server. Expected format: `!config stats STR/DEX/CON/WIS/INT/CHA`")
            elif subTokens[0] == "list":
                return await message.channel.send(":thought_balloon: `config list` lists the current configuration settings.")
            elif subTokens[0] == "nuke":
                return await message.channel.send(":thought_balloon: `config nuke` resets all server settings. Be careful!")
            elif subTokens[0] == "refresh":
                return await message.channel.send(":thought_balloon: `config refresh` refreshes my reference to the GM role.")
            elif subTokens[0] == "delay":
                return await message.channel.send(":thought_balloon: `config delay` sets how many seconds I wait before deleting commands that I have followed. Set to a negative number to make me never delete messages. Expected format: `!config delay 10`")
            else:
                return await message.channel.send(":thought_balloon: I don't know that subcommand. Try `!char help`")

        async def configureStats(subTokens):
            if not await self.assertUserIsGM(message.channel, message.author):
                return

            stats = []
            for arg in subTokens:
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

            self.guildConfigMap[message.channel.guild.id] = {"stats": stats, "messageDeleteDelay": -1}
            if message.guild.id not in self.guildCharactersMap:
                self.guildCharactersMap[message.channel.guild.id] = {}

            await message.channel.send(":tools: Available character stats on this server have changed from `{}` to `{}`. Please note that character data may be affected.".format(
                oldStatsString,
                newStatsString
            ))

        async def listStats(subTokens):
            if not await self.assertGuildConfigured(message.channel): 
                return
            await message.channel.send("Stats are: {}".format("/".join(self.guildConfigMap[message.channel.guild.id]["stats"])))

        async def nuke(subTokens):
            if not await self.assertUserIsGM(message.channel, message.author):
                return

            liveNuke = "nuke_live_datetime" in self.guildConfigMap[message.channel.guild.id] and datetime.datetime.now() - self.guildConfigMap[message.channel.guild.id]["nuke_live_datetime"] < datetime.timedelta(minutes=1)

            if not liveNuke:
                self.guildConfigMap[message.channel.guild.id]["nuke_live_datetime"] = datetime.datetime.now()
                return await message.channel.send(":skull_crossbones: The nuclear option is armed. Repeat the nuke command within 60 seconds to complete the operation. :skull_crossbones:")
            elif liveNuke:
                self.guildConfigMap = {}
                self.guildCharactersMap = {}
                return await message.channel.send(":skull_crossbones: Missiles launched. Data destroyed. May God have mercy on us all. :skull_crossbones:")

        async def refreshGMs(subTokens):
            await self.fetchGMs()
            return await message.channel.send(":tropical_drink: GMs refreshed")

        async def setMessageDeleteDelay(subTokens):
            if not await self.assertGuildConfigured(message.channel):
                return

            if not await self.assertUserIsGM(message.channel, message.author):
                return
            delay = -1
            try:
                delay = int(subTokens[0])
            except ValueError:
                return await message.channel.send("Could not parse an int for the delay")
            delayStr = "{} seconds".format(delay)
            if delay < 0:
                delayStr = "never"

            self.guildConfigMap[message.channel.guild.id]["messageDeleteDelay"] = delay
            return await message.channel.send("Message destruct delay set to `{}`.".format(delayStr))

        subcommands = {
            "help": helpConfig,
            "list": listStats,
            "stats": configureStats,
            "nuke": nuke,
            "refresh": refreshGMs,
            "delay": setMessageDeleteDelay
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
            await message.channel.send("Invalid subcommand, expected one of `{}`".format("`, `".join(subcommands.keys())))
        if self.getDeleteDelay(message.channel.guild.id) > 0:
            await message.delete(delay=self.getDeleteDelay(message.channel.guild.id))


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
        if self.getDeleteDelay(message.channel.guild.id) > 0:
            await message.delete(delay=self.getDeleteDelay(message.channel.guild.id))


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

    # Returns True if the guild has been configured, otherwise False and prints message
    async def assertGuildConfigured(self, channel):
        if channel.guild.id not in self.guildConfigMap:
            await channel.send("This server is not configured. Try `!config help`")
            return False
        return True

    # Returns True if a character is associated with the given guild (from channel) and user, otherwise False and prints message
    async def assertPlayerExists(self, channel, user):
        if not await self.assertGuildConfigured(channel):
            return False
        if user.id not in self.guildCharactersMap[channel.guild.id]:
            await channel.send("{} does not have a registered character! Try `!c help new`".format(user.mention))
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

    def getDeleteDelay(self, guildID):
        if guildID in self.guildConfigMap:
            return self.guildConfigMap[guildID]["messageDeleteDelay"]
        else:
            return -1

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
        #               key1: {count: int, tags: [str, ...]},
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
        self.addCommand('item', self.manageInventory, lambda x: True, "Manage your inventory")
        self.addCommand('i', self.manageInventory, lambda x: True)
        self.addCommand('inv', self.manageInventory, lambda x: True)
        self.addCommand('inventory', self.manageInventory, lambda x: True)