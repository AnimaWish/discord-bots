import discord
import asyncio
import random
import re
from .generic import DiscordBot
import argparse
import importlib

class ZenyattaBot(DiscordBot):
    ###################
    #    Constants    #
    ###################

    MAX_DICE = 1000000
    OVERWATACH_SERVER_ID = 199402098754846729

    GENTLEMEN_ROLE_ID = 432092120007049236
    ROBOTS_ROLE_ID = 433376740312875049

    EVENTS_CHANNEL_ID = 542851422333567007
    EVENT_PLANNING_CATEGORY_ID = 542857613524598804

    OVERWATCH_CHARACTERS = {
        'offense': [
            'Doomfist',
            'Genji',
            'McCree',
            'Pharah',
            'Reaper',
            'Soldier: 76',
            'Sombra',
            'Tracer'
        ],
        'defense': [
            'Bastion',
            'Hanzo',
            'Junkrat',
            'Mei',
            'Torbjörn',
            'Widowmaker',
        ],
        'tank': [
            'D.Va',
            'Orisa',
            'Reinhardt',
            'Roadhog',
            'Winston',
            'Zarya'
        ],
        'support': [
            'Ana',
            'Brigitte',
            'Lúcio',
            'Mercy',
            'Moira',
            'Symmetra'
        ]
    }

    ###################
    #     Helpers     #
    ###################

    def memberIsGentleman(self, author):
        return ZenyattaBot.memberHasRole(author, ZenyattaBot.GENTLEMEN_ROLE_ID)

    def mentionGents(self, text):
        return '<@&{}>'.format(ZenyattaBot.GENTLEMEN_ROLE_ID) + ' ' + text

    ###################
    #    Commands     #
    ###################
    async def getRandomCharacter(self, message, params):
        # TODO strip off brackets if user adds them
        splitCharacterRoles = set(re.split('[; |,\s]',params))
        pool = []
        for key in splitCharacterRoles:
            key = key.lower()
            if key == 'all' or key == 'any':
                pool = ZenyattaBot.OVERWATCH_CHARACTERS['offense'] + ZenyattaBot.OVERWATCH_CHARACTERS['defense'] + ZenyattaBot.OVERWATCH_CHARACTERS['tank'] + ZenyattaBot.OVERWATCH_CHARACTERS['support']
                break
            if key in ZenyattaBot.OVERWATCH_CHARACTERS:
                pool = pool + ZenyattaBot.OVERWATCH_CHARACTERS[key]

        if len(splitCharacterRoles) == 0 or len(pool) == 0:
            pool = ZenyattaBot.OVERWATCH_CHARACTERS['offense'] + ZenyattaBot.OVERWATCH_CHARACTERS['defense'] + ZenyattaBot.OVERWATCH_CHARACTERS['tank'] + ZenyattaBot.OVERWATCH_CHARACTERS['support']

        await message.channel.send(random.choice(ZenyattaBot.CHOICE_STRINGS).format(random.choice(pool)))

    async def createEvent(self, message, params):
        if message.channel.category_id == ZenyattaBot.EVENT_PLANNING_CATEGORY_ID:
            channelNamePattern = "\[([\w -]+)\]\s*"
            channelNameMatch = re.match(channelNamePattern, params)
            channelName = "new event (rename me!)"
            eventMessage = params
            if channelNameMatch:
                channelName = channelNameMatch.group(1)
                eventMessage = re.sub(channelNamePattern, "", params)

            if len(eventMessage) == 0:
                await message.channel.send("Speak up! This message will be pinned, so make sure you include those juicy party details!")
                return

            await message.pin()

            robotRole = message.guild.me.top_role.id

            overwrites = {
                message.guild.default_role: discord.PermissionOverwrite(read_messages=False),
                message.guild.get_role(robotRole): discord.PermissionOverwrite(read_messages=True),
                #message.guild.get_role(ZenyattaBot.GENTLEMEN_ROLE_ID): discord.PermissionOverwrite(read_messages=True),
            }

            category = message.guild.get_channel(message.channel.category_id)


            newChannel = await message.guild.create_text_channel(
                name = channelName, 
                overwrites = overwrites,
                category = category,
                topic = eventMessage,
            )

            newChannelMessage = await newChannel.send("__**Event Submitted By:**__ {}\n__**Event Details:**__\n{}".format(message.author.mention, eventMessage))
            await newChannelMessage.pin()
            if not channelNameMatch:
                await newChannel.send("Hey {}! Make sure to give this channel a name relevant to your event :sparkles:".format(message.author.mention))
        else:
            await message.channel.send("You need to do this in an `#events` channel")

    ###################
    #   Bot Methods   #
    ###################

    def __init__(self, prefix="!"):
        super().__init__(prefix, "Peace be upon you.", "Passing into the Iris.")

        # self.addCommand('character', self.getRandomCharacter,                             lambda x: True,         "Get a random OW character from the selected roles",   "[offense|defense|tank|support|any]")
        self.addCommand('captain',   self.chooseCaptain,                                  lambda x: True,         "Choose a random user from the current voice channel")
        self.addCommand('event',     self.createEvent,                                    lambda x: True, "Create an event", "[Event Name Here] whatever you want to say")
        self.addCommand('bears',     lambda message, params: self.mentionGents(':bear:'), self.memberIsGentleman, ":bear:")
        self.addCommand('pubg',      lambda message, params: self.mentionGents(':pubg:'), self.memberIsGentleman, ":b:")

    async def on_ready(self):
        await super().on_ready()

    async def on_message(self, message):
        await super().on_message(message)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Zenyatta Bot')
    parser.add_argument("token", type=str, nargs=1)
    args = parser.parse_args()
    zenyatta = ZenyattaBot()
    zenyatta.run(args.token[0])
