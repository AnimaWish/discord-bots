import discord
import asyncio
import random
import urllib.request
import re
import random
import os

client = discord.Client()

MAX_DICE = 1000000
OVERWATACH_SERVER_ID = '199402098754846729'
GENTLEMEN_ROLE_ID = '432092120007049236'

server = None
gents = None

chars = {
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

choiceStrings = [
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

commandMap = {
    
}

@client.event
async def on_ready():
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    initConstants()
    print('------')

def initConstants():
    global server
    server = client.get_server(OVERWATACH_SERVER_ID)
    for role in server.roles:
        if role.id == GENTLEMEN_ROLE_ID:
            global gents
            gents = role
            break

    print(server.name)
    print(gents.name)

@client.event
async def on_message(message):
    if message.content.startswith('!help'):
        await client.send_message(message.channel, getHelp())
    elif message.content.startswith('!echo'):
        await client.send_message(message.channel, message.content[len('!echo '):])
    elif gents in message.author.roles:
        if message.content.startswith('!bears'):
            await client.send_message(message.channel, mentionGents() + ":bear:")
        elif message.content.startswith('!pubg'):
            await client.send_message(message.channel, mentionGents() + ":b:")
    elif message.content.startswith('!roll'):
        await client.send_message(message.channel, getDieRoll(message.content[len('!roll '):]))   
    elif message.content.startswith('!character'):
        await client.send_message(message.channel, getRandomCharacter(message.content[len('!character '):]))
    elif message.content.startswith('!choose'):
        await client.send_message(message.channel, chooseRand(message.content[len('!choose '):]))

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
    splitRoles = set(re.split('[; |,\s]',role))
    pool = []
    for key in splitRoles:
        key = key.lower()
        print(key)
        if key == 'all' or key == 'any':
            pool = chars['offense'] + chars['defense'] + chars['tank'] + chars['support']
            break;
        if key in chars:
            pool = pool + chars[key]

    if len(splitRoles) == 0 or len(pool) == 0:
        pool = chars['offense'] + chars['defense'] + chars['tank'] + chars['support']

    return random.choice(choiceStrings).format(random.choice(pool))


def chooseRand(list):
    theList = re.split('[; |,\s]',list)
    return random.choice(choiceStrings).format(random.choice(theList))

def getHelp():
    return """
Available Commands:
`!bears` - :bear:
`!pubg`  - :b:
`!roll XdY` - roll X Y-sided dice
`!character [offense|defense|tank|support|any]` - get a random character
`!choose [a,list,of,shit]` - get a random member of the list
Hit up Wish#6215 for feature requests/bugs!
"""

def getRoles(server):
    roles = list(server.roles)
    for x in roles:
        print(x.name, x.id)

def mentionGents():
    return '<@&{}>'.format(GENTLEMEN_ROLE_ID)

def fetchToken():
    dirname = os.path.dirname(__file__)
    secrets = open(os.path.join(dirname, "secrets.txt"), 'r')
    for line in secrets:
        parsed = line.split(":")
        if parsed[0] == os.path.basename(__file__):
            token = parsed[1].strip()
            secrets.close()
            return token

client.run(fetchToken())