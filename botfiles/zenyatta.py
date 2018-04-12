import discord
import asyncio
import random
import urllib.request
import re
import os
import generic
import argparse

class ZenyattaBot(generic.DiscordBot):
    client = discord.Client()

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

    CHOICE_STRINGS = [
        "I choose... {}!",
        "How about {}?",
        "Result hazy, try again later (jk do {})",
        "{}, obviously!",
        "Choose {}."
        "Whatever you do, DON'T pick {} (wink)",
        "Signs point to {}",
        "/me cracks open fortune cookie, finds message that says \"{}\"",
        "My lawyers advise {}",
        "I'm a {} man myself."
    ]

    ###################
    #     Helpers     #
    ###################

    def memberHasRole(member, roleId):
        for role in member.roles:
            if role.id == roleId:
                return True

        return False

    def memberIsGentleman(author):
        return memberHasRole(author, GENTLEMEN_ROLE_ID)

    ###################
    #    Commands     #
    ###################

    def getHelp():
        return """
    Available Commands:
    `!bears` - :bear:
    `!pubg`  - :b:
    `!roll XdY` - roll X Y-sided dice
    `!character [offense|defense|tank|support|any]` - get a random character
    `!choose [a,list,of,shit]` - get a random member of the list
    Hit up Wish#6215 for feature requests/bugs, or visit my repository at https://github.com/AnimaWish/discord-bots
    """

    def echo(arg):
        return arg

    def getDieRoll(self, arg):
            params = arg.split("d")
            if len(params) != 2 or not (params[0].isdigit() and params[1].isdigit()):
                return "Required syntax: `!roll XdY`"
            elif int(params[0]) > ZenyattaBot.MAX_DICE:
                return "I can't possibly hold {} dice!".format(params[0])
            else:
                result = 0
                for x in range(0, int(params[0])):
                    result = result + random.randint(1, int(params[1]))

            return "You rolled {}!".format(result)

    def getRandomCharacter(self, role):
        splitCharacterRoles = set(re.split('[; |,\s]',role))
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

    def chooseRand(self, list):
        theList = re.split('[; |,\s]',list)
        return random.choice(ZenyattaBot.CHOICE_STRINGS).format(random.choice(theList))

    def mentionGents(self, message):
        return '<@&{}>'.format(GENTLEMEN_ROLE_ID) + ' ' + message
     
    ###################
    #   Bot Methods   #
    ###################

    def __init__(self, token):
        super().__init__(token)
        self.commandMap = {
            'help':         generic.BotCommand(self.getHelp,                     lambda x: True),
            'echo':         generic.BotCommand(self.echo,                        lambda x: True),
            'roll':         generic.BotCommand(self.getDieRoll,                  lambda x: True),
            'character':    generic.BotCommand(self.getRandomCharacter,          lambda x: True),
            'choose':       generic.BotCommand(self.chooseRand,                  lambda x: True),
            'bears':        generic.BotCommand(lambda x: mentionGents(':bear:'), self.memberIsGentleman),
            'pubg':         generic.BotCommand(lambda x: mentionGents(':pubg:'), self.memberIsGentleman)
        }

    async def on_ready(self):
        await super().on_ready()

    async def on_message(self, message):
        await super().on_message(message)


if __name__ == "__main__":
    print("Hello")
    parser = argparse.ArgumentParser(description='Zenyatta Bot')
    parser.add_argument("token", type=str, nargs=1)
    args = parser.parse_args()
    zenyatta = ZenyattaBot(args.token[0])
    zenyatta.run()

