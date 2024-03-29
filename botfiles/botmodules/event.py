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

EVENT_TITLE_PATTERN = "\*\*What:\*\* (.+)\n"
TIME_PATTERN = "\*\*When:\*\* (.+)\n"
TIME_FMT = "**When:** {}\n"
CODE_PATTERN = "\`\$<(.+)>\`"

class EventInfo:
    def __init__(self, channelID, messageID, datetimeString, title):
        #self.dateTime = int(dateTime)
        self.channelID = int(channelID)
        self.messageID = int(messageID)
        self.humanDateTime = datetimeString
        self.title = title

class NotEventCategoryError(Exception):
    '''This is not in the events category'''

class EventNotFoundError(Exception):
    '''A connection is broken; either the eventList is missing an entry, or the events category is missing a channel'''

class EventBot(DiscordBot):
    ###################
    #     Helpers     #
    ###################

    def encodeEventInfo(self, channelID, messageID):
        code = str(channelID) + "." + str(messageID)
        return "`$<" + code + ">`"

    # parse the bot code
    def decodeEventInfo(self, message):
        match = re.search(EVENT_TITLE_PATTERN, message)
        name = ""
        if match != None:
            name = match.group(1)

        match = re.search(TIME_PATTERN, message)
        if match == None:
            print("failed to decode event info from message {\n" + message + "\n}")
            return None
        timeString = match.group(1)

        match = re.search(CODE_PATTERN, message)
        if match == None:
            print("failed to decode event info from message {\n" + message + "\n}")
            return None
        code = match.group(1)
        data = code.split(".")

        if len(data) == 0 or len(data) > 2:
            return None

        # backwards compat
        messageID = -1
        if len(data) > 1:
            messageID = data[1]

        return EventInfo(channelID=data[0], messageID = messageID, datetimeString=timeString, title=name)

    # events are mapped message.id => Eventinfo{dateTime, channelID}
    # where message is the eventList message, and channelID is the channel associated with the event
    async def getEvents(self):
        for guildID in self.guildChannelMap.keys():
            self.guildEventMap[guildID] = {}
            async for message in self.guildChannelMap[guildID][EVENT_LIST_CHANNEL_NAME].history():
                if message.author.id == self.user.id:
                    eventInfo = self.decodeEventInfo(message.content)
                    if eventInfo is not None:
                        channel = self.get_channel(eventInfo.channelID)
                        if channel is None:
                            print("Could not import event, channel [" + str(eventInfo.channelID) + "] not found")
                        elif channel.category_id == self.guildChannelMap[channel.guild.id][EVENTS_CATEGORY_NAME].id:
                            self.guildEventMap[guildID][message.id] = eventInfo

                            # migration code
                            # if eventInfo.messageID == -1:
                            #     eventInfo.messageID = await self.generatePinnedInfoMessage(channel)
                            #     await self.migrateEventListing(message, eventInfo)

                            pinnedMessage = await channel.fetch_message(eventInfo.messageID)
                            if not pinnedMessage.pinned:
                                await channel.send("Who's the scoundrel unpinning my messages?")
                                await pinnedMessage.pin()

    def getConfigs(self):
        for guild in self.guilds:
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

    # checks that the time is in an accepted format
    def parseDateTime(self, string):
        dateFormats = [
            "%m/%d/%y %I:%M%p",
            "%m/%d/%Y %I:%M%p",
            "%m/%d/%y %I%p",
            "%m/%d/%Y %I%p",
            "%m/%d/%y %I:%M %p",
            "%m/%d/%Y %I:%M %p",
            "%m/%d/%y at %I:%M%p",
            "%m/%d/%Y at %I:%M%p",
            "%m/%d/%y at %I%p",
            "%m/%d/%Y at %I%p",
            "%m/%d/%y at %I:%M %p",
            "%m/%d/%Y at %I:%M %p",
        ]


        for dfmt in dateFormats:
            try:
                dt = datetime.datetime.strptime(string, dfmt)
                return dt
            except ValueError:
                pass

        return None

    async def constructGuestList(self, channel):
        results = await self.getUsersForEvent(channel)
        responseTemplate = ":sparkles:**__Current Guest List__**:sparkles:\n:white_check_mark: **Going:**\n{}\n:no_entry_sign: **Not Going:**\n{}\n:grey_question: **Maybe:**\n{}"
        rsvpLists = []
        for memberList in [results['yes'], results['no'], results['maybe']]:
            rsvpList = ""
            for member in memberList:
                rsvpList += "- " + member.name + "\n"

            rsvpLists.append(rsvpList)

        return responseTemplate.format(rsvpLists[0], rsvpLists[1], rsvpLists[2])
        

    def fetchDateTimeFromEventListMessageContents(self, message):
        match = re.search(TIME_PATTERN, message)
        if match == None:
            print("failed to decode event info from message {\n" + message + "\n}")
            return None
        timeString = match.group(1)

        return timeString

    # Given a channel ID, find the message in the event-list channel that corresponds to it
    async def getEventMessageFromChannel(self, guildID, channelID):
        # get the message ID in the event List
        eventListMessageID = None
        for messageID in self.guildEventMap[guildID]:
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
            if str(reaction) not in emojiMap_reverse:
                continue
            reactionString = emojiMap_reverse[str(reaction)] # reaction is "✅", reactionString is "yes"
            results[reactionString] = []
            async for user in reaction.users():
                if user.id == self.user.id:
                    continue
                results[reactionString].append(user)
                if user.id not in userVoteCounts:
                    userVoteCounts[user.id] = 0
                userVoteCounts[user.id] = userVoteCounts[user.id] + 1

        # if someone answers multiple they become a maybe
        maybes = []
        for reactionString in ['yes', 'no']:
            popIndices = []
            for i in range(len(results[reactionString])):
                user = results[reactionString][i]
                if userVoteCounts[user.id] > 1:
                    maybes.append(user)
                    popIndices.append(i)

            for i in reversed(popIndices):
                results[reactionString].pop(i)

        results['maybe'] = list(set(maybes) | set(results['maybe']))

        return results

    async def generatePinnedInfoMessage(self, channel):
        message = await channel.send(await self.constructGuestList(channel))
        await message.pin()
        return message.id

    async def migrateEventListing(self, message, eventInfo):
        match = re.search(CODE_PATTERN, message.content)
        if match == None:
            message.channel.send("oh god someone help me I can't see")

        newContent = message.content[:match.start()] + self.encodeEventInfo(eventInfo.channelID, eventInfo.messageID) + message.content[match.end():]

        await message.edit(content=newContent)


    ###################
    #    Commands     #
    ###################

    async def createEvent(self, message, params):
        if message.channel.id == self.guildChannelMap[message.guild.id][EVENT_CREATION_CHANNEL_NAME].id:
            if len(params) == 0:
                await message.channel.send("You need three things to create an event: a name, a time, and a description.\n Try something like this: `!event-create cool party name 1/2/19 7:00pm here is a description`")
                return
            # Parse out the time first
            dateTimePattern = "\d+\/\d+\/\d+\s+(at\s*)?\d+(:\d+)?\s*\w[mM]"
            dateTimeMatch = re.search(dateTimePattern, params)
            if dateTimeMatch == None:
                await message.channel.send("Sorry, I couldn't read when the party starts! Make sure you match the format `1/2/19 7:00pm` precisely.")
                return
            eventDateTime_human = dateTimeMatch.group(0).strip()
            eventDateTime_dt = self.parseDateTime(eventDateTime_human)
            if eventDateTime_dt == None:
                await message.channel.send("I don't think that that's a real time or date! Are you trying to mess with me?")
                return
            if eventDateTime_dt.date() < datetime.date.today():
                await message.channel.send("Unless you're offering a time machine limousine service, nobody's going to be able to make it to a party in the past!")
                return

            # Get the rest of the information for the party
            pattern = "(.+\s+)?{}(\s+.+)?".format(dateTimePattern)
            match = re.match(pattern, params, re.DOTALL)
            if not match:
                await message.channel.send("Sorry, I didn't understand that at all. Make sure you have the correct format! ```!event-create Cool Party!!! 1/2/19 7:00pm This is the description of your party!```") # TODO use buildCommandHint
                return

            # Get the name of the event and generate the channel name from it
            eventName = match.group(1)
            if eventName == None or len(eventName) < 2:
                await message.channel.send("Sorry, I couldn't read the name of the party. Every party needs a name. Make sure yours has one!")
                return
            channelName = re.sub("[^\w -]", "", eventName)
            if len(channelName) > MAX_EVENT_NAME_LENGTH:
                await message.channel.send("Slow down bucko! Keep that party name succinct!")
                return

            # Get the event details
            eventDetails = match.group(4)
            if eventDetails == None or len(eventDetails.strip()) == 0:
                await message.channel.send("Sorry, what was your party about? Add a description!")
                return

            eventDetails = eventDetails.strip()

            # Create the new channel
            robotRole = message.guild.me.top_role.id
            # overwrites = {
            #     message.guild.default_role: discord.PermissionOverwrite(read_messages=False),
            #     message.guild.get_role(robotRole): discord.PermissionOverwrite(read_messages=True),
            # }
            newChannel = await message.guild.create_text_channel(
                name = channelName, 
                # overwrites = overwrites,
                category = self.guildChannelMap[message.guild.id][EVENTS_CATEGORY_NAME],
                topic = '@ ' + eventDateTime_human,
            )

            pinnedMessage = await newChannel.send("Nobody has RSVP'd yet!")
            await pinnedMessage.pin()

            # Create the message for event-list channel
            eventListMessage = ":sparkles:**__New Event__**:sparkles:\n**What:** {}\n".format(eventName) + TIME_FMT.format(eventDateTime_human) + "**Channel:**  {}\n".format(newChannel.mention) + "**Details:**\n{}\n".format(eventDetails) + self.encodeEventInfo(newChannel.id, pinnedMessage.id)
            eventListMessage = await self.guildChannelMap[message.guild.id][EVENT_LIST_CHANNEL_NAME].send(eventListMessage)
            await eventListMessage.add_reaction(emojiMap["yes"])
            await eventListMessage.add_reaction(emojiMap["no"])
            await eventListMessage.add_reaction(emojiMap["maybe"])

            # update event list
            await self.getEvents()
        else:
            await message.channel.send("You need to do this in the `#event-creation` channel")

    async def getGuestList(self, message, params):
        try:
            await message.channel.send(await self.constructGuestList(message.channel))
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
            dt = self.parseDateTime(event.humanDateTime)
            if dt == None:
                await message.channel.send("Something has gone horribly wrong, I forgot what time an event starts!")
                return

            if dt > datetime.datetime.now():
                channel = message.channel.guild.get_channel(event.channelID)
                if channel is not None:
                    events.append((dt, event.title, channel.mention))

        events.sort()

        response = "There are no upcoming events!"
        if len(events) > 0:
            response = ":sparkles:__**Upcoming Events**__:sparkles:\n"
            for event_tuple in events:
                eventString = "{} - {} ({})".format(event_tuple[0].strftime("**%m/%d/%y** at **%I:%M %p**"), event_tuple[1], event_tuple[2])
                response += eventString + "\n"            

        await message.channel.send(response)

    async def updateEventDate(self, message, params):
        try:
            eventMessage = await self.getEventMessageFromChannel(message.channel.guild.id, message.channel.id)

            eventDateTime_bot = self.parseDateTime(params)
            if eventDateTime_bot == None:
                await message.channel.send("Sorry, I couldn't read when the party starts! Make sure you match the format `1/2/19 7:00pm` precisely.")
                return

            newEventMessageContent = re.sub(TIME_PATTERN, TIME_FMT.format(params), eventMessage.content, 1)
            await eventMessage.edit(content=newEventMessageContent)
            await self.getEvents()
            await message.channel.edit(topic='@ ' + params)
            await self.appendEventDescription(message, "Updated Start Time")

        except NotEventCategoryError:
            await message.channel.send("This is not an event channel!")
        except EventNotFoundError:
            await message.channel.send("Something has gone horribly wrong, I don't know what event this is!")

    # make sure to use params and not message.content
    async def appendEventDescription(self, message, params):
        try:
            eventMessage = await self.getEventMessageFromChannel(message.channel.guild.id, message.channel.id)

            if len(params) == 0:
                await message.channel.send("Speak up! What do you want me to add to the description?")
                return

            await eventMessage.edit(content=eventMessage.content + "\nEdit: " + params + "\n")
            await message.channel.send("Got it! Updated the event listing.")

        except NotEventCategoryError:
            await message.channel.send("This is not an event channel!")
        except EventNotFoundError:
            await message.channel.send("Something has gone horribly wrong, I don't know what event this is!")

    ###################
    #     Events      #
    ###################
    #
    # Need to namespace event functions
    #

    async def on_ready(self):
        await super().on_ready()
        self.getConfigs()
        await self.getEvents()

    async def on_raw_reaction_add(self, payload):
        await super().on_raw_reaction_add(payload)
        await self.updateGuestList(payload)

    async def on_raw_reaction_remove(self, payload):
        await super().on_raw_reaction_remove(payload)
        await self.updateGuestList(payload)

    async def updateGuestList(self, reactionPayload):
        if self.guildChannelMap[reactionPayload.guild_id][EVENT_LIST_CHANNEL_NAME].id == reactionPayload.channel_id:
            eventListingMessage = await self.guildChannelMap[reactionPayload.guild_id][EVENT_LIST_CHANNEL_NAME].fetch_message(reactionPayload.message_id)

            if eventListingMessage.author.id == self.user.id and eventListingMessage.id in self.guildEventMap[eventListingMessage.guild.id]:
                eventInfo = self.guildEventMap[eventListingMessage.guild.id][eventListingMessage.id]

                eventChannel = self.get_channel(eventInfo.channelID)
                pinnedMessage = await eventChannel.fetch_message(eventInfo.messageID)
                newContent = await self.constructGuestList(eventChannel)

                await pinnedMessage.edit(content = newContent)

    ###################
    #   Bot Methods   #
    ###################

    def __init__(self, prefix="!", greeting="Hello", farewell="Goodbye", *, intents, **options):
        super().__init__(prefix, greeting, farewell, intents=intents, options=options)

        self.addCommand('event-create', self.createEvent, lambda x: True, "Create an event", "cool party name! 1/2/19 7:00pm here is a description")
        self.addCommand('event-guests', self.getGuestList, lambda x: True, "Get guest list",  "")
        self.addCommand('event-announce', self.mentionGuests, lambda x: True, "Pings everyone who has RSVP'd yes or maybe",  "")
        self.addCommand('event-list', self.listEvents, lambda x: True, "List all upcoming events",  "")
        self.addCommand('event-time', self.updateEventDate, lambda x: True, "Update the time of the event",  "4/20/19 7:00pm")
        self.addCommand('event-date', self.updateEventDate, lambda x: True, "",  "")
        self.addCommand('event-update', self.appendEventDescription, lambda x: True, "Add more information to the event listing", "new information for your event")

        self.guildChannelMap = {}
        self.guildEventMap = {}