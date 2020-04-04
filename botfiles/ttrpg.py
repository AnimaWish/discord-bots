import discord
import asyncio
import random
import urllib.request
import re
import os, io
import pickle
import json
import threading
import datetime, time

from .generic import DiscordBot

class TTRPGBot(DiscordBot):
    XP_THRESHOLDS = [
        0,
        300,
        900,
        2700,
        6500,
        14000,
        23000,
        34000,
        48000,
        64000,
        85000,
        100000,
        120000,
        140000,
        165000,
        195000,
        225000,
        265000,
        305000,
        355000,
    ]

    def xpToLevel(self, xp):
        i = 0
        while xp > self.XP_THRESHOLDS[i]:
            i+=1

        return i

    async def fetchGMs(self):
        for guild in self.client.guilds:
            for role in guild.roles:
                if role.name == "GM" or role.name == "DM":
                    self.guildGMRoleMap[guild.id] = role
                    print("Found GM role for " + guild.name)
            if guild.id not in self.guildGMRoleMap:
                print("Couldn't find GM role for " + guild.name)

    async def manageXP(self, message, params):
        if len(params) == 0:
            await message.channel.send("Current XP Total is " + str(self.xpTotals[message.guild.id]) + "!")
            return

        if message.author not in self.guildGMRoleMap[message.guild.id].members:
            await message.channel.send("Last I checked, you weren't the GM.")
            return

        # Determine if this is a subtraction
        xpString = params
        multiplier = 1
        if xpString[0] == "-":
            multiplier = -1
            xpString = xpString[1:]
        elif xpString[0] == "+":
            xpString = xpString[1:]

        addXP = 0
        try: 
            addXP = int(xpString.strip())
        except ValueError:
            await message.channel.send("I couldn't find a number in there.")
            return

        oldLevel = self.xpToLevel(self.xpTotals[message.guild.id])
        self.xpTotals[message.guild.id] += multiplier * addXP
        newLevel = self.xpToLevel(self.xpTotals[message.guild.id])

        xpThresholdForNextLevel = self.XP_THRESHOLDS[newLevel]
        xpDiff = xpThresholdForNextLevel - self.xpTotals[message.guild.id]

        if oldLevel < newLevel:
            await message.channel.send(":sparkles::sparkles::sparkles: LEVEL UP! :sparkles::sparkles::sparkles:")
        elif oldLevel > newLevel:
            await message.channel.send(":scream::scream::scream: Level... DOWN???? :scream::scream::scream:")

        self.save()

        await message.channel.send("New XP Total is **{}**! Only {} more XP to level {}!".format(self.xpTotals[message.guild.id], xpDiff, newLevel + 1))

    async def lookupSpell(self, message, params):
        if params == "":
            await message.channel.send("Give me a spell name to search!")
            return

        hyphenSpellName = "-".join(params.lower().split(" ")).replace(",", "")

        url = "http://dnd5eapi.co/api/spells/{}".format(hyphenSpellName)

        response = None
        try:
            response = urllib.request.urlopen(url) #.read().decode("utf-8") 
        except urllib.error.HTTPError as e:
            if e.code == 404:
                backup = "https://duckduckgo.com/?q=!ducky+{}+site%3A5e.tools".format(params.replace(" ", "%20"))

                await message.channel.send("Sorry, I couldn't find that spell. This link might work: {}".format(backup))
                return

            await message.channel.send("Yikes I spilled beer on my copy of the PHB! Hang on a sec while I clean up.")
            return

        spellDict = json.loads(response.read().decode("utf-8"))


        formatString = "__**{}**__\n*Level {} {}*\n\n**Casting Time:** {}\n**Range:** {}\n**Components:** {}\n**Duration:** {}\n\n{}\n***At Higher Levels.*** {}\n"

        components = ""
        if "components" in spellDict:
            components += ",".join(spellDict["components"])
        if "material" in spellDict:
            components += " ({})".format(spellDict["material"])

        output = formatString.format(
            spellDict["name"],
            spellDict["level"],
            spellDict["school"]["name"],
            spellDict["casting_time"],
            spellDict["range"],
            components,
            spellDict["duration"],
            "\n".join(spellDict["desc"]),
            "\n".join(spellDict["higher_level"]),
        )

        await message.channel.send(output)


    async def refreshGMList(self, message, params):
        await self.fetchGMs()

    async def on_ready(self):
        await self.fetchGMs()
        for guild in self.client.guilds:
            if guild.id not in self.xpTotals:
                self.xpTotals[guild.id] = 0

        self.save()

    def save(self):
        if not os.path.isfile(self.filePath):
            os.makedirs(os.path.dirname(self.filePath), exist_ok=True)

        with open(self.filePath, 'wb') as f:
            pickle.dump(self.xpTotals, f, pickle.HIGHEST_PROTOCOL)

    ###################
    #     Startup     #
    ###################

    def __init__(self, prefix="!", greeting="Hello", farewell="Goodbye"):
        super().__init__(prefix, greeting, farewell)

        self.filePath = "storage/{}/xptotals.pickle".format(self.getName())
        if os.path.isfile(self.filePath):
            self.xpTotals = pickle.load(open(self.filePath, "rb"))
            print("Imported XP Totals:")
            for guildID in self.xpTotals:
                print("{}: {}".format(guildID, self.xpTotals[guildID]))
        else:
            self.xpTotals = {} # {guildID: int}

        self.guildGMRoleMap = {} # { guildID: guildGMRole }

        self.addCommand('xp', self.manageXP, lambda x: True, "See XP", "+1000")
        self.addCommand('refresh', self.refreshGMList, lambda x: True)
        self.addCommand('spell', self.lookupSpell, lambda x: True, "Look up a spell", "Acid Arrow")