import discord
import asyncio
import random
import urllib.request
import re
import os

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

###################
#    Commands     #
###################

class BotCommand:
    def __init__(self, method, requiredPermission):
        self.method = method
        self.permission = requiredPermission

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

def getDieRoll(arg):
        params = arg.split("d")
        if len(params) != 2 or not (params[0].isdigit() and params[1].isdigit()):
            return "Required syntax: `!roll XdY`"
        elif int(params[0]) > MAX_DICE:
            return "I can't possibly hold {} dice!".format(params[0])
        else:
            result = 0
            for x in range(0, int(params[0])):
                result = result + random.randint(1, int(params[1]))

        return "You rolled {}!".format(result)

def getRandomCharacter(role):
    splitCharacterRoles = set(re.split('[; |,\s]',role))
    pool = []
    for key in splitCharacterRoles:
        key = key.lower()
        if key == 'all' or key == 'any':
            pool = OVERWATCH_CHARACTERS['offense'] + OVERWATCH_CHARACTERS['defense'] + OVERWATCH_CHARACTERS['tank'] + OVERWATCH_CHARACTERS['support']
            break;
        if key in OVERWATCH_CHARACTERS:
            pool = pool + OVERWATCH_CHARACTERS[key]

    if len(splitCharacterRoles) == 0 or len(pool) == 0:
        pool = OVERWATCH_CHARACTERS['offense'] + OVERWATCH_CHARACTERS['defense'] + OVERWATCH_CHARACTERS['tank'] + OVERWATCH_CHARACTERS['support']

    return random.choice(CHOICE_STRINGS).format(random.choice(pool))

def chooseRand(list):
    theList = re.split('[; |,\s]',list)
    return random.choice(CHOICE_STRINGS).format(random.choice(theList))

def mentionGents(message):
    return '<@&{}>'.format(GENTLEMEN_ROLE_ID) + ' ' + message

commandMap = {
    'help':         BotCommand(getHelp,                          False),
    'echo':         BotCommand(echo,                             False),
    'roll':         BotCommand(getDieRoll,                       False),
    'character':    BotCommand(getRandomCharacter,               False),
    'choose':       BotCommand(chooseRand,                       False),
    'bears':        BotCommand(lambda x: mentionGents(':bear:'), GENTLEMEN_ROLE_ID),
    'pubg':         BotCommand(lambda x: mentionGents(':pubg:'), GENTLEMEN_ROLE_ID)
}
 
###################
#  Event Methods  #
###################

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    print('------')

@client.event
async def on_message(message):
    commandPattern = "^!\S+\s"
    commandMatch = re.match(commandPattern, message.content)
    if commandMatch:
        commandString = message.content[commandMatch.start() + 1 : commandMatch.end()].strip()
        if commandString in commandMap:
            command = commandMap[commandString]
            if not command.permission or memberHasRole(message.author, command.permission):
                await client.send_message(message.channel, command.method(message.contents[commandMatch.end() + 1:]))

###################
#     Startup     #
###################

def fetchToken():
    rootdirname = os.path.dirname(os.path.dirname(__file__))
    secrets = open(os.path.join(rootdirname, "secrets.txt"), 'r')
    for line in secrets:
        parsed = line.split(":")
        if parsed[0] == os.path.basename(__file__):
            token = parsed[1].strip()
            secrets.close()
            return token

client.run(fetchToken())