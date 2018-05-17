import discord
import asyncio
import random
import urllib.request
import re
import os
import generic
import argparse
import importlib

importlib.reload(generic)
class ZenyattaBot(generic.DiscordBot):
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

    def __init__(self, prefix="~"):
        super().__init__(prefix, "Peace be upon you", "Passing into the Iris")

        self.addCommand('character', self.getRandomCharacter,                             lambda x: True,         "Get a random OW character from the selected roles",   "[offense|defense|tank|support|any]")
        self.addCommand('captain',   self.chooseCaptain,                                  lambda x: True,         "Choose a random user from the current voice channel")
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
