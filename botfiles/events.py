import discord
import asyncio
import random
import re
from .generic import DiscordBot
import argparse
import importlib
import base64
import datetime


EVENT_CREATION_CHANNEL_NAME = "event-creation"
EVENT_LIST_CHANNEL_NAME = "event-list"
EVENTS_CATEGORY_NAME = "events"
MAX_EVENT_NAME_LENGTH = 100

emojiMap = {
    "yes": "✅",
    "no": "🚫",
    "maybe": "❔",
}

emojiMap_reverse = {
    "✅": "yes",
    "🚫": "no",
    "❔": "maybe",
}

class EventBot(DiscordBot):
    guildChannelMap = {}


    guildEventMap = {}

    ###################
    #     Helpers     #
    ###################

    class EventInfo:
        def __init__(self, dateTime, channelID):
            self.dateTime = dateTime
            self.channelID = channelID


    def encodeEventInfo(self, dateTime, channelID):
        toEncode = str.encode(dateTime + "." + str(channelID))
        return "`$<" + str(base64.b64encode(toEncode)) + ">`"

    # parse the bot code
    def decodeEventInfo(self, message):
        pattern = "`$<(.+)>`"
        match = re.match(pattern, message)
        code = match.group(1)
        result = base64.b64decode(code)
        data = result.split(".")
        return EventInfo(data[0], data[1])

    async def getEvents(self):
        for guildID in self.guildChannelMap.keys():
            self.guildEventMap[guildID] = {}
            async for message in self.guildChannelMap[guildID][EVENT_LIST_CHANNEL_NAME].history():
                self.guildEventMap[guildID][message.id] = self.decodeEventInfo(message.contents)

    async def getConfigs(self):
        for guild in self.client.guilds:
            self.guildChannelMap[guild.id] = {}
            for channel in guild.channels:
                if channel.name == EVENT_CREATION_CHANNEL_NAME and isinstance(channel, discord.TextChannel):
                    self.guildChannelMap[guild.id][EVENT_CREATION_CHANNEL_NAME] = channel
                    print("Found " + guild.name + "." + channel.name)
                elif channel.name == EVENT_LIST_CHANNEL_NAME and isinstance(channel, discord.TextChannel):
                    self.guildChannelMap[guild.id][EVENT_LIST_CHANNEL_NAME] = channel
                    print("Found " + guild.name + "." + channel.name)
                elif channel.name == EVENTS_CATEGORY_NAME and isinstance(channel, discord.CategoryChannel):
                    self.guildChannelMap[guild.id][EVENTS_CATEGORY_NAME] = channel
                    print("Found " + guild.name + "." + channel.name)

            if not (EVENT_CREATION_CHANNEL_NAME in self.guildChannelMap[guild.id] and EVENT_LIST_CHANNEL_NAME in self.guildChannelMap[guild.id] and EVENTS_CATEGORY_NAME in self.guildChannelMap[guild.id]):
                self.guildChannelMap.pop(guild.id, None)
                print("Failed to compile configurations for " + guild.name)

        await self.getEvents()


    def parseDateTime(self, string):
        dateFormats = [
            "%m/%d/%y %I:%M%p",
            "%m/%d/%Y %I:%M%p",
            "%m/%d/%y %I:%M %p",
            "%m/%d/%Y %I:%M %p",
            "%m/%d/%y at %I:%M%p",
            "%m/%d/%Y at %I:%M%p",
            "%m/%d/%y at %I:%M %p",
            "%m/%d/%Y at %I:%M %p",
        ]

        timestamp = None
        for dfmt in dateFormats:
            try:
                dt = datetime.datetime.strptime(string, dfmt)
                timestamp = int((dt - datetime.datetime(1970, 1, 1)) / datetime.timedelta(seconds=1))
                timestamp = timestamp
                break
            except ValueError:
                timestamp = None

        return str(timestamp)

    async def getUsersForEvent(self, message):
        if message.channel.category_id != self.guildChannelMap[message.guild.id][EVENTS_CATEGORY_NAME]:
            return None

        # get the message ID in the event List
        eventListMessageID = None
        for eventMessageID in self.guildEventMap[message.guild.id].keys():
            if self.guildEventMap[message.guild.id][eventMessageID].channelID == message.channel.id:
                eventListMessageID = eventMessageID
                break
        if eventListMessageID == None:
            return None

        # get the message object
        eventMessage = None
        async for message in self.guildChannelMap[message.guild.id][EVENT_LIST_CHANNEL_NAME].history():
            if message.id == eventListMessageID:
                eventMessage = message
        if eventMessage == None:
            return None

        # get the reactions off the message
        results = {}
        userVoteCounts = {}
        for reaction in eventMessage.reactions:
            results[emojiMap_reverse[str(reaction)]] = []
            async for user in reaction.users():
                results[reaction].append(user)
                if user.id not in userVoteCounts:
                    userVoteCounts[user.id] = 0
                userVoteCounts[user.id] = userVoteCounts[user.id] + 1



    ###################
    #    Commands     #
    ###################

    # !event `event-name` 1/2/19 7:00pm `here is a description`
    async def createEvent(self, message, params):
        if message.channel.id == self.guildChannelMap[message.guild.id][EVENT_CREATION_CHANNEL_NAME].id:
            pattern = "\`(.+)\`\s+(.+)\s+\`(.+)\`"
            match = re.match(pattern, params)

            if not match:
                await message.channel.send("Sorry, I didn't understand that at all. Make sure you have the correct format! ``!event `event name` 1/2/19 7:00pm `here is a description```")
                return

            eventName = match.group(1)
            if len(eventName) == 0:
                await message.channel.send("Sorry, I couldn't read the name of the party. Every party needs a name. Make sure yours has one!")
                return

            channelName = re.sub("[^\w -]", "", eventName)
            if len(channelName) > MAX_EVENT_NAME_LENGTH:
                await message.channel.send("Slow down bucko! That event name is too long!")
                return

            eventDateTime_human = match.group(2).strip()
            eventDateTime_bot = self.parseDateTime(eventDateTime_human)

            if eventDateTime_bot == None:
                await message.channel.send("Sorry, I couldn't read when the party starts! Make sure you match the format `1/2/19 7:00pm` precisely.")
                return

            eventDetails = match.group(3)
            if len(eventDetails) == 0:
                await message.channel.send("Sorry, what was your party about? Add a description!")
                return


            robotRole = message.guild.me.top_role.id
            overwrites = {
                message.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                message.guild.get_role(robotRole): discord.PermissionOverwrite(read_messages=True),
                #message.guild.get_role(ZenyattaBot.GENTLEMEN_ROLE_ID): discord.PermissionOverwrite(read_messages=True),
            }
            newChannel = await message.guild.create_text_channel(
                name = channelName, 
                overwrites = overwrites,
                category = self.guildChannelMap[message.guild.id][EVENTS_CATEGORY_NAME],
                topic = eventDetails,
            )

            eventListMessage = "**What:** {}\n".format(eventName) + "**When:** {}\n".format(eventDateTime_human) + "**Details:**\n{}\n".format(eventDetails) + self.encodeEventInfo(eventDateTime_bot, newChannel.id)

            eventListMessage = await self.guildChannelMap[message.guild.id][EVENT_LIST_CHANNEL_NAME].send(eventListMessage)
            await eventListMessage.add_reaction(emojiMap["yes"])
            await eventListMessage.add_reaction(emojiMap["no"])
            await eventListMessage.add_reaction(emojiMap["maybe"])

        # newChannelMessage = await newChannel.send("__**Event Submitted By:**__ {}\n__**Event Details:**__\n{}\n@everyone".format(message.author.mention, eventMessage))
        # await newChannelMessage.pin()
        # if not channelNameMatch:
        #     await newChannel.send("Hey {}! Make sure to give this channel a name relevant to your event :sparkles:".format(message.author.mention))
        else:
            await message.channel.send("You need to do this in an `#event-creation` channel")

    ###################
    #     Events      #
    ###################
    #
    # Need to namespace functions

    async def on_ready_events(self):
        await self.getConfigs()

    # async def on_reaction_add_events(self, reaction, user):
    #     print(reaction.emoji)
    #     print("reaction added 2")
        # if user.id != self.client.user.id and reaction.message.author.id == self.client.user.id:
        #     if reaction.message.id in self.currentReferendums:
        #         self.currentReferendums[reaction.message.id].addVote(user.id, reaction.emoji)

    ###################
    #   Bot Methods   #
    ###################

    def __init__(self, prefix="!", greeting="Hello", farewell="Goodbye"):
        super().__init__(prefix, "Peace be upon you.", "Passing into the Iris.")

        self.addCommand('event', self.createEvent, lambda x: True, "Create an event", "[Event Name Here] whatever you want to say")

        #self.addEventListener("on_reaction_add", "addReactionEvent", self.on_reaction_add_events)
        self.addEventListener("on_ready", "readyEvent", self.on_ready_events)
