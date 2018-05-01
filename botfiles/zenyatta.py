import discord
import asyncio
import random
import urllib.request
import re
import os
from generic import DiscordBot, BotCommand
import argparse

class ZenyattaBot(DiscordBot):
    ###################
    #    Constants    #
    ###################

    MAX_DICE = 1000000
    OVERWATACH_SERVER_ID = '199402098754846729'
    GENTLEMEN_ROLE_ID = '432092120007049236'

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
        return DiscordBot.memberHasRole(author, ZenyattaBot.GENTLEMEN_ROLE_ID)

    def mentionGents(self, text):
        return '<@&{}>'.format(ZenyattaBot.GENTLEMEN_ROLE_ID) + ' ' + text

    ###################
    #    Commands     #
    ###################

    def getHelp(self, message, params):
        return """
Available Commands:
    `!bears` - :bear:
    `!pubg`  - :b:
    `!roll XdY` - roll X Y-sided dice
    `!character [offense|defense|tank|support|any]` - get a random character
    `!choose a,list,of,things` - get a random member of the list
Hit up Wish#6215 for feature requests/bugs, or visit my repository at https://github.com/AnimaWish/discord-bots
    """

    def getRandomCharacter(self, message, params):
        # TODO strip off brackets if user adds them
        splitCharacterRoles = set(re.split('[; |,\s]',params))
        pool = []
        for key in splitCharacterRoles:
            key = key.lower()
            if key == 'all' or key == 'any':
                pool = ZenyattaBot.OVERWATCH_CHARACTERS['offense'] + ZenyattaBot.OVERWATCH_CHARACTERS['defense'] + ZenyattaBot.OVERWATCH_CHARACTERS['tank'] + ZenyattaBot.OVERWATCH_CHARACTERS['support']
                break;
            if key in ZenyattaBot.OVERWATCH_CHARACTERS:
                pool = pool + ZenyattaBot.OVERWATCH_CHARACTERS[key]

        if len(splitCharacterRoles) == 0 or len(pool) == 0:
            pool = ZenyattaBot.OVERWATCH_CHARACTERS['offense'] + ZenyattaBot.OVERWATCH_CHARACTERS['defense'] + ZenyattaBot.OVERWATCH_CHARACTERS['tank'] + ZenyattaBot.OVERWATCH_CHARACTERS['support']

        return random.choice(ZenyattaBot.CHOICE_STRINGS).format(random.choice(pool))
     
    ###################
    #   Bot Methods   #
    ###################

    def __init__(self, token, prefix="!"):
        super().__init__(token, prefix)
        self.commandMap = {
            'help':         BotCommand(self.getHelp,                                        lambda x: True),
            'echo':         BotCommand(self.echo,                                           lambda x: True),
            'ping':         BotCommand(self.ping,                                           lambda x: True),
            'roll':         BotCommand(self.getDieRoll,                                     lambda x: True),
            'character':    BotCommand(self.getRandomCharacter,                             lambda x: True),
            'choose':       BotCommand(self.chooseRand,                                     lambda x: True),
            'captain':      BotCommand(self.chooseCaptain,                                  lambda x: True),
            'bears':        BotCommand(lambda message, params: self.mentionGents(':bear:'), self.memberIsGentleman),
            'pubg':         BotCommand(lambda message, params: self.mentionGents(':pubg:'), self.memberIsGentleman)
        }

    async def on_ready(self):
        await super().on_ready()

    async def on_message(self, message):
        await super().on_message(message)


if __name__ == "__main__":
    print("Peace be upon you.")
    parser = argparse.ArgumentParser(description='Zenyatta Bot')
    parser.add_argument("token", type=str, nargs=1)
    args = parser.parse_args()
    zenyatta = ZenyattaBot(args.token[0])
    zenyatta.run()
