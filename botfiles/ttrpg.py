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

    EMOJI_MAP = {
        "yes": "✅",
        "no": "🚫",
    }

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

        self.saveXP()

        await message.channel.send("New XP Total is **{}**! Only {} more XP to level {}!".format(self.xpTotals[message.guild.id], xpDiff, newLevel + 1))

    def printSpell(self, spellDict):
        formatString = "__**{}**__\n*Level {} {}{}*\n\n**Casting Time:** {}\n**Range:** {}\n**Components:** {}\n**Duration:** {}\n\n{}\n{}\n"        

        higherLevel = ""
        if "higher_level" in spellDict and len(spellDict["higher_level"]) > 0:
            higherLevel = "***At Higher Levels***\n" + spellDict["higher_level"]

        book = ""
        if "book" in spellDict and len(spellDict["book"]) > 0:
            book = " ({})".format(spellDict["book"])

        return formatString.format(
            spellDict["name"],
            spellDict["level"],
            spellDict["school"].capitalize(),
            book,
            spellDict["casting_time"],
            spellDict["range"],
            spellDict["components"],
            spellDict["duration"],
            spellDict["description"],
            higherLevel,
        )

    async def lookupSpell(self, message, params):
        if params == "":
            await message.channel.send("Give me a spell name to search!")
            return

        spell = self.getSpell(params)
        if spell is not None:
            await message.channel.send(self.printSpell(spell))
            return

        print("Did not find spell {} in list, looking it up".format(params))

        hyphenSpellName = "-".join(params.lower().split(" ")).replace(",", "")
        url = "http://dnd5eapi.co/api/spells/{}".format(hyphenSpellName)

        response = None
        try:
            response = urllib.request.urlopen(url).read().decode("utf-8") 
        except urllib.error.HTTPError as e:
            if e.code == 404:
                backup = "https://duckduckgo.com/?q=!ducky+{}+site%3A5e.tools".format(params.replace(" ", "%20"))

                await message.channel.send("Sorry, I couldn't find that spell. Why not do me a favor and add it to my spellbook using `!addspell`?")
                return

            await message.channel.send("Yikes I spilled beer on my copy of the PHB! Hang on a sec while I clean up.")
            return

        spellDict = json.loads(response.read().decode("utf-8"))

        components = ""
        if "components" in spellDict:
            components += ",".join(spellDict["components"])
        if "material" in spellDict:
            components += " ({})".format(spellDict["material"]) 

        school = spellDict["school"]["name"]

        higherLevel = ""
        if "higher_level" in spellDict:
            higherLevel = spellDict["higher_level"]
        if not isinstance(higherLevel, str):
            higherLevel = "\n".join(spellDict["higher_level"])

        spell = {
            "name": spellDict["name"],
            "book": "PHB",
            "school": school,
            "level": spellDict["level"],
            "casting_time": spellDict["casting_time"],
            "range": spellDict["range"],
            "components": components,
            "duration": spellDict["duration"],
            "description": "\n".join(spellDict["desc"]),
            "higher_level": higherLevel,
        }

        output = self.printSpell(spell)
        if spell["name"] not in self.spells:
            self.saveSpell(spell)

        await message.channel.send(output)

    async def addSpell(self, message, params):
        if len(params) == 0:
            await message.channel.send("You didn't give me a spell! Please paste the spell data in the command in the same format as in the PHB. e.g.:\n```!addspell Magic Missile\n1st-level evocation\nCasting Time: 1 action\nRange: 120 feet\nComponents: V,S\nDuration: Instantaneous\nYou create three glowing darts of magical force...```")

        rawlines = params.split("\n")
        lines = []
        for line in rawlines:
            if line != "":
                lines.append(line)

        pattern_level = "[Ll]evel:\s*(.+)\n"
        pattern_cast = "[Cc]asting [Tt]ime:\s*(.+)\n"
        pattern_range = "[Rr]ange:\s*(.+)"
        pattern_components = "[Cc]omponents:\s*(.+)\n"
        pattern_duration = "[Dd]uration:\s*(.+)\n"

        pattern_bot_combo = "[Ll]evel\s*(\d+)\s*(\w+)\s*\((\w+)\)\n"
        pattern_book_combo = "(\d+)\w+-[Ll]evel\s*(\w+)\n"
        pattern_book_combo_cantrip = "(\w+)\s*[Cc]antrip\n"

        schools = {
            "conjuration": True,
            "necromancy": True,
            "evocation": True,
            "abjuration ": True,
            "transmutation": True,
            "divination": True,
            "enchantment": True,
            "illusion": True,
        }

        books = {
            "Sword Coast Adventure's Guide": "SCAG",
            "Player's Handbook": "PHB",
            "Xanathar's Guide To Everything": "XGE",
            "Elemental Evil": "EE",
        }

        spellName = lines[0]

        bot_combo_match = re.search(pattern_bot_combo, params)
        book_combo_match = re.search(pattern_book_combo, params)
        book_combo_cantrip_match = re.search(pattern_book_combo_cantrip, params)

        level = "COULD NOT PARSE LEVEL"
        book = ""
        school = "COULD NOT PARSE SCHOOL"
        castingTime = "COULD NOT PARSE CASTING TIME"
        spellRange = "COULD NOT PARSE RANGE"
        components = "COULD NOT PARSE COMPONENTS"
        duration = "COULD NOT PARSE DURATION"
        description = "COULD NOT PARSE DESCRIPTION"

        if bot_combo_match is not None:
            level = bot_combo_match.group(1)
            school = bot_combo_match.group(2)
            book = bot_combo_match.group(3)
        elif book_combo_match is not None:
            level = book_combo_match.group(1)
            school = book_combo_match.group(2)
        elif book_combo_cantrip_match is not None:
            level = "0"
            school = book_combo_cantrip_match.group(1)
        else:
            book = "PHB"
            if lines[1].lower() in schools:
                school = lines[1].lower()
            if lines[1].lower() not in schools:
                book = ""
                for possibleTitle in books.keys():
                    if possibleTitle in lines[1]:
                        book = books[possibleTitle]
                        break

                if lines[2].lower() in schools:
                    school = lines[2].lower()

            match = re.search(pattern_level, params)
            if match is not None:
                level = match.group(1)

        match = re.search(pattern_cast, params)
        if match is not None:
            castingTime = match.group(1)

        match = re.search(pattern_range, params)
        if match is not None:
            spellRange = match.group(1)

        match = re.search(pattern_components, params)
        if match is not None:
            components = match.group(1)

        match = re.search(pattern_duration, params)
        if match is not None:
            duration = match.group(1)
            description = params[match.end():].strip()

        descsplit = re.split("[Aa]t [Hh]igher [Ll]evels?\.?", description)
        print(descsplit)
        higherLevel = ""
        if len(descsplit) > 1:
            description = descsplit[0]
            higherLevel = descsplit[1]

        if level.lower() == "cantrip":
            level = "0"

        spell = {
            "name": " ".join(i.capitalize() for i in spellName.strip().lower().split(" ")),
            "book": book.strip(),
            "school": school.strip(),
            "level": level.strip(),
            "casting_time": castingTime.strip(),
            "range": spellRange.strip(),
            "components": components.strip(),
            "duration": duration.strip(),
            "description": description.strip(),
            "higher_level": higherLevel.strip(),
        }

        await message.channel.send(self.printSpell(spell))
        msg = await message.channel.send("Does this look correct?")

        self.pendingSpells[msg.id] = {"message": msg, "spell": spell}

        await msg.add_reaction(self.EMOJI_MAP["yes"])
        await msg.add_reaction(self.EMOJI_MAP["no"])


    async def spellListLink(self, message, params):
        await message.channel.send("https://www.dnd-spells.com/spells")

    async def refreshGMList(self, message, params):
        await self.fetchGMs()

    async def on_ready(self):
        await self.fetchGMs()
        for guild in self.client.guilds:
            if guild.id not in self.xpTotals:
                self.xpTotals[guild.id] = 0

        self.saveXP()

    def saveXP(self):
        if not os.path.isfile(self.xpFilePath):
            os.makedirs(os.path.dirname(self.xpFilePath), exist_ok=True)

        with open(self.xpFilePath, 'wb') as f:
            pickle.dump(self.xpTotals, f, pickle.HIGHEST_PROTOCOL)

    def formatSpellKey(self, name):
        return re.sub(r"['’]|\(.+\)", "", name.lower().replace("-", " ")).strip()

    def getSpell(self, name):
        spellNameKey = self.formatSpellKey(name)
        if spellNameKey in self.spells:
            return self.spells[spellNameKey][-1]
        return None

    def saveSpell(self, spell):
        spellNameKey = self.formatSpellKey(spell["name"])
        if spellNameKey not in self.spells:
            self.spells[spellNameKey] = []

        self.spells[spellNameKey].append(spell)

        if not os.path.isfile(self.spellFilePath):
            os.makedirs(os.path.dirname(self.spellFilePath), exist_ok=True)

        with open(self.spellFilePath, 'w', encoding='utf8') as f:
            json.dump(self.spells, f, ensure_ascii=False)

    async def on_raw_reaction_add(self, payload):
        await super().on_raw_reaction_add(payload)
        if payload.user_id != self.client.user.id and payload.message_id in self.pendingSpells:
            msg = self.pendingSpells[payload.message_id]["message"]
            if payload.emoji.name == self.EMOJI_MAP["no"]:
                await msg.channel.send("Spell discarded.")
                del self.pendingSpells[payload.message_id]
                return
            
            if payload.emoji.name == self.EMOJI_MAP["yes"]:
                spellDict = self.pendingSpells[payload.message_id]["spell"]
                self.saveSpell(spellDict)
                await msg.channel.send("Spell saved!")
                del self.pendingSpells[payload.message_id]

    ###################
    #     Startup     #
    ###################

    def __init__(self, prefix="!", greeting="Hello", farewell="Goodbye"):
        super().__init__(prefix, greeting, farewell)

        self.xpFilePath = "storage/{}/xptotals.pickle".format(self.getName())
        self.spellFilePath = "storage/{}/spells.pickle".format(self.getName())
        if os.path.isfile(self.xpFilePath):
            self.xpTotals = pickle.load(open(self.xpFilePath, "rb"))
            print("Imported XP Totals:")
            for guildID in self.xpTotals:
                print("{}: {}".format(guildID, self.xpTotals[guildID]))
        else:
            self.xpTotals = {} # {guildID: int}

        if os.path.isfile(self.spellFilePath):
            self.spells = json.load(open(self.spellFilePath, "rb"))
            print ("Imported {} spells".format(len(self.spells)))
        else:
            self.spells = {} # {spellName: [spellDefinition1, spellDefinition2, ...]}

        self.guildGMRoleMap = {} # { guildID: guildGMRole }
        self.pendingSpells = {} # {messageID: {message: confirmationMessageObj, spell: spellDict} }

        self.addCommand('xp', self.manageXP, lambda x: True, "See XP", "+1000")
        self.addCommand('refresh', self.refreshGMList, lambda x: True)
        self.addCommand('spell', self.lookupSpell, lambda x: True, "Look up a spell", "Acid Arrow")
        self.addCommand('spelllist', self.spellListLink, lambda x: True, "Get a link to the spell list")
        self.addCommand('addspell', self.addSpell, lambda x: True, "Paste in a spell to save it forever")
