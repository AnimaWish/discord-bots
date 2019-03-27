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

class EventInfo:
    def __init__(self, dateTime, channelID, datetimeString):
        self.dateTime = int(dateTime)
        self.channelID = int(channelID)
        self.humanDateTime = datetimeString

class NotEventCategoryError(Exception):
    '''This is not in the events category'''

class EventNotFoundError(Exception):
    '''A connection is broken; either the eventList is missing an entry, or the events category is missing a channel'''

class EventBot(DiscordBot):
    guildChannelMap = {}


    guildEventMap = {}

    ###################
    #     Helpers     #
    ###################

    # def encodeEventInfo(self, dateTime, channelID):
    #     toEncode = str.encode(dateTime + "." + str(channelID))
    #     return "`$<" + str(base64.b64encode(toEncode)) + ">`"

    # # parse the bot code
    # def decodeEventInfo(self, message):
    #     pattern = "\`\$<b'(.+)'>\`"
    #     match = re.search(pattern, message)
    #     if match == None:
    #         print("failed to decode event info from message {\n" + message + "\n}")
    #         return
    #     code = match.group(1)
    #     result = base64.b64decode(str.encode(code))
    #     data = str(result).split(".")
    #     return EventInfo(data[0][2:], data[1][:-2]) #substrings because base64 str shit outputs b'whatwecareabout'

    def encodeEventInfo(self, dateTime, channelID):
        code = dateTime + "." + str(channelID)
        return "`$<" + code + ">`"

    # parse the bot code
    def decodeEventInfo(self, message):
        timePattern = "\*\*When:\*\* (.+)\n"
        match = re.search(timePattern, message)
        if match == None:
            print("failed to decode event info from message {\n" + message + "\n}")
            return None
        timeString = match.group(1)

        codePattern = "\`\$<(.+)>\`"
        match = re.search(codePattern, message)
        if match == None:
            print("failed to decode event info from message {\n" + message + "\n}")
            return None
        code = match.group(1)
        data = code.split(".")
        if len(data) != 2:
            return None
        return EventInfo(data[0], data[1], timeString)

    # events are mapped message.id => Eventinfo{dateTime, channelID}
    # where message is the eventList message, and channelID is the channel associated with the event
    async def getEvents(self):
        for guildID in self.guildChannelMap.keys():
            self.guildEventMap[guildID] = {}
            async for message in self.guildChannelMap[guildID][EVENT_LIST_CHANNEL_NAME].history():
                self.guildEventMap[guildID][message.id] = self.decodeEventInfo(message.content)

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

    # Given a channel ID, find the message in the event-list channel that corresponds to it
    async def getEventMessageFromChannel(self, guildID, channelID):
        # get the message ID in the event List
        eventListMessageID = None
        for messageID in self.guildEventMap[guildID].keys():
            if self.guildEventMap[guildID][messageID].channelID == channelID:
                eventListMessageID = messageID
                break
        if eventListMessageID == None:
            raise EventNotFoundError

        # get the message object
        async for eventListMessage in self.guildChannelMap[guildID][EVENT_LIST_CHANNEL_NAME].history():
            if eventListMessage.id == eventListMessageID:
                return eventListMessage

        raise EventNotFoundError

    # returns a map {
    #   'yes': [list, of, users],
    #   'no': [list, of, users],
    #   'maybe': [list, of, users]
    # }
    async def getUsersForEvent(self, channel):
        if channel.category_id != self.guildChannelMap[channel.guild.id][EVENTS_CATEGORY_NAME].id:
            raise NotEventCategoryError()

        eventMessage = await self.getEventMessageFromChannel(channel.guild.id, channel.id)

        # get the reactions off the message
        results = {}
        userVoteCounts = {}
        for reaction in eventMessage.reactions:
            reactionString = emojiMap_reverse[str(reaction)] # reaction is "✅", reactionString is "yes"
            results[reactionString] = []
            async for user in reaction.users():
                if user.id == self.client.user.id:
                    continue
                results[reactionString].append(user)
                if user.id not in userVoteCounts:
                    userVoteCounts[user.id] = 0
                userVoteCounts[user.id] = userVoteCounts[user.id] + 1

        # if someone answers multiple they become a maybe
        maybes = []
        for reactionString in ['yes', 'no']:
            for i in range(len(results[reactionString])):
                user = results[reactionString][i]
                if userVoteCounts[user.id] > 1:
                    maybes.append(user)
                    results[reactionString].pop(i)
        results['maybe'] = list(set(maybes) | set(results['maybe']))

        return results

    ###################
    #    Commands     #
    ###################

    # !event `event-name` 1/2/19 7:00pm `here is a description`
    async def createEvent(self, message, params):
        if message.channel.id == self.guildChannelMap[message.guild.id][EVENT_CREATION_CHANNEL_NAME].id:
            print (params)
            pattern = "\`(.+)\`\s+(.+)\s+\`(.+)\`"
            match = re.match(pattern, params, re.DOTALL)

            if not match:
                await message.channel.send("Sorry, I didn't understand that at all. Make sure you have the correct format! ```!event `event name` 1/2/19 7:00pm `here is a description````")
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
                topic = eventName,
            )

            eventListMessage = "**What:** {}\n".format(eventName) + "**When:** {}\n".format(eventDateTime_human) + "**Details:**\n{}\n".format(eventDetails) + self.encodeEventInfo(eventDateTime_bot, newChannel.id)

            eventListMessage = await self.guildChannelMap[message.guild.id][EVENT_LIST_CHANNEL_NAME].send(eventListMessage)
            await eventListMessage.add_reaction(emojiMap["yes"])
            await eventListMessage.add_reaction(emojiMap["no"])
            await eventListMessage.add_reaction(emojiMap["maybe"])

            await self.getEvents()
        # newChannelMessage = await newChannel.send("__**Event Submitted By:**__ {}\n__**Event Details:**__\n{}\n@everyone".format(message.author.mention, eventMessage))
        # await newChannelMessage.pin()
        # if not channelNameMatch:
        #     await newChannel.send("Hey {}! Make sure to give this channel a name relevant to your event :sparkles:".format(message.author.mention))
        else:
            await message.channel.send("You need to do this in an `#event-creation` channel")

    async def getGuestList(self, message, params):
        try:
            results = await self.getUsersForEvent(message.channel)
            responseTemplate = ":sparkles:**__Current Guest List__**:sparkles:\n:white_check_mark: **Going:**\n{}\n:no_entry_sign: **Not Going:**\n{}\n:grey_question: **Maybe:**\n{}"
            rsvpLists = []
            for memberList in [results['yes'], results['no'], results['maybe']]:
                rsvpList = ""
                for member in memberList:
                    rsvpList += "- " + member.name + "\n"

                rsvpLists.append(rsvpList)

            response = responseTemplate.format(rsvpLists[0], rsvpLists[1], rsvpLists[2])
            await message.channel.send(response)

        except NotEventCategoryError:
            await message.channel.send("This is not an event channel!")
        except EventNotFoundError:
            await message.channel.send("Something has gone horribly wrong, I don't know what event this is!")

    async def mentionGuests(self, message, params):
        try:
            results = await self.getUsersForEvent(message.channel)

            pingList = results['yes'] + results['maybe']

            response = ""
            for member in pingList:
                response += member.mention + " "

            if len(response) == 0:
                response = "Nobody has RSVP'd :("

            await message.channel.send(response)

        except NotEventCategoryError:
            await message.channel.send("This is not an event channel!")
        except EventNotFoundError:
            await message.channel.send("Something has gone horribly wrong, I don't know what event this is!")

    async def listEvents(self, message, params):
        events = []
        for messageID in self.guildEventMap[message.channel.guild.id]:
            event = self.guildEventMap[message.channel.guild.id][messageID]
            if datetime.datetime.fromtimestamp(event.dateTime) > datetime.datetime.now():
                dt = datetime.datetime.fromtimestamp(event.dateTime)
                channel = message.channel.guild.get_channel(event.channelID)
                if channel is not None:
                    events.append(event.humanDateTime + " - " + channel.topic)

        response = "There are no upcoming events!"
        if len(events) > 0:
            response = ":sparkles:__**Upcoming Events**__:sparkles:\n"
            for eventString in events:
                response += eventString + "\n"            

        await message.channel.send(response)

    ###################
    #     Events      #
    ###################
    #
    # Need to namespace functions

    async def on_ready_events(self):
        await self.getConfigs()

    #async def on_reaction_add_events(self, reaction, user):

        # if user.id != self.client.user.id and reaction.message.author.id == self.client.user.id:
        #     if reaction.message.id in self.currentReferendums:
        #         self.currentReferendums[reaction.message.id].addVote(user.id, reaction.emoji)

    ###################
    #   Bot Methods   #
    ###################

    def __init__(self, prefix="!", greeting="Hello", farewell="Goodbye"):
        super().__init__(prefix, "Peace be upon you.", "Passing into the Iris.")

        self.addCommand('event-create', self.createEvent, lambda x: True, "Create an event", "`event-name` 1/2/19 7:00pm `here is a description`")
        self.addCommand('event-guests', self.getGuestList, lambda x: True, "Get guest list",  "")
        self.addCommand('event-announce', self.mentionGuests, lambda x: True, "Pings everyone who has RSVP'd yes or maybe",  "")
        self.addCommand('event-list', self.listEvents, lambda x: True, "List all upcoming events",  "")


        # self.addEventListener("on_reaction_add", "addReactionEvent", self.on_reaction_add_events)
        self.addEventListener("on_ready", "readyEvent", self.on_ready_events)
