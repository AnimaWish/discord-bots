import discord
import asyncio
import random
import urllib.request
import re
import os, sys
import importlib
import threading, subprocess

class BotObject:
    def __init__(self, botName, token):
        self.token = token
        self.name = botName
        sys.path.append("botfiles")
        package = importlib.__import__('botfiles', fromlist=[botName])
        self.module = getattr(package, botName)
        self.reloadModule()

    def reloadModule(self):
        self.module = importlib.reload(self.module)
        botClass = getattr(self.module, self.name.capitalize() + "Bot")
        self.bot = botClass("!")

    def stop(self):
        self.bot.stop()

###################
#    Constants    #
###################

botMap = {
    'mettaton': None,
    'philippe': None,
    'zenyatta': None
}

threads = {
    'mettaton': None,
    'philippe': None,
    'zenyatta': None
}

WISH_USER_ID = '199401793032028160'

VALID_USERS = [
    WISH_USER_ID, # Caius
    '201083741928423424'  # Drew
]

###################
#     Helpers     #
###################

def motherprint(pront):
    print("MOTHER: {}".format(pront))

def isValidUser(userId):
    return userId in VALID_USERS

def isAdmin(userId):
    return userId == WISH_USER_ID

def mentionWish(message):
    return wishUser.mention + ': ' + message

def importBlacklist():
    blacklistFile = open('blacklist.txt', 'r')
    global blacklist
    blacklist = []
    for line in blacklistFile:
        blacklist.append(line.strip())
    blacklistFile.close()

# Requires botMap to be mapped
def restartChild(botName):
    if botName in botMap:
        botObj = botMap[botName]

        killChild(botName)

        motherprint("Restarting {}...".format(botName))

        botObj.reloadModule()
        threads[botName] = threading.Thread(target=botObj.bot.run, args=(botObj.token,), name="{}-thread".format(botName))
        threads[botName].start()

        motherprint("Restarted {}.".format(botName))

def killChild(botName):
    botObj = botMap[botName]
    if threads[botName] is not None:
        motherprint("Shutting down {}...".format(botName))
        botObj.stop()
        threads[botName].join()
        threads[botName] = None
        motherprint("Shut down {}.".format(botName))

###################
#    Commands     #
###################

class BotCommand:
    def __init__(self, method, permissionCheck):
        self.method = method
        self.checkPermission = permissionCheck

def getHelp(params, author):
    return """
PRIORITY ONE
ENSURE RETURN OF ORGANISM FOR ANALYSIS.
ALL OTHER CONSIDERATIONS SECONDARY.
CREW EXPENDABLE.
"""

# Returns information about sender
def whoAmI(params, author):
    permString = "NONE"
    if isAdmin(author.id):
        permString = "ADMINISTRATOR"
    elif isValidUser(author.id):
        permString = "DEVELOPER"

    return "Username: {}#{}\nUserId: {}\nAccess Permission: {}".format(author.name, author.discriminator, author.id, permString)

# Returns status of children bots
def getStatus(params, author):
    return "Who knows"

def echo(params, author):
    return params

# Reload and restart a bot
def restart(params, author):
    botName = params
    if botName == "all":
        for botName in botMap:
            restartChild(botName)
    else:
        if not botName in botMap:
            return botName + " not found." 

        restartChild(botName)

def kill(params, author):
    botName = params
    if not botName in botMap:
        return botName + " not found." 

    killChild(botName)

# Update local files
def update(params, author):
    out = subprocess.check_output(["git", "pull"])
    return out.decode("utf-8") 

# Add a user to the blacklist
def block(params, author):
    userId = params.strip()
    if userId in VALID_USERS:
        return "Cannot block whitelisted user."

    blacklistFile = open('blacklist.txt', 'a')
    blacklistFile.write(userId)
    blacklistFile.close()
    importBlacklist()
    return "User blocked. Blacklist has {} members.".format(len(blacklist))

# Shut down everything
def shutdown(params, author):
    _stop_event.set()

commandMap = {
    'help':     BotCommand(getHelp,     lambda x: True),
    'whoami':   BotCommand(whoAmI,      lambda x: True),
    'status':   BotCommand(getStatus,   lambda x: True),

    'echo':     BotCommand(echo,        isValidUser),
    'restart':  BotCommand(restart,     isValidUser),
    'update':   BotCommand(update,      isValidUser),
    'kill':     BotCommand(kill,        isValidUser),

    'block':    BotCommand(block,       isAdmin),
    'shutdown': BotCommand(shutdown,    isAdmin)
}

###################
#  Event Methods  #
###################

async def on_ready():
    #Report startup
    motherprint('Logged in as {} ({})'.format(client.user.name, client.user.id))
    
    #Find Wish
    try:
        global wishUser
        wishUser = await client.get_user_info(WISH_USER_ID)
        motherprint("Found administrator: {}#{}".format(wishUser.name, wishUser.discriminator))
    except Exception as e:
        motherprint(e)
        motherprint("NO ADMINISTRATOR FOUND")

    #Initialize Blacklist
    importBlacklist()
    motherprint("Imported blacklist with {} members.".format(len(blacklist)))

    #Start Children
    for botName in botMap.keys():
        botMap[botName] = BotObject(botName, fetchToken(botName + ".py"))
        restartChild(botName)

    motherprint('------')

async def on_message(message):
    if message.author.id in blacklist:
        motherprint("Blocked message `{}` from {}#{}({})".format(message.content, message.author.name, message.author.discriminator, message.author.id))
        return

    address = "mother "
    commandPattern = "^{}\S+".format(address)
    commandMatch = re.match(commandPattern, message.content.lower())
    if commandMatch:
        commandString = message.content[commandMatch.start() + len(address) : commandMatch.end()].strip()
        # TODO Write to logs

        if commandString in commandMap:
            command = commandMap[commandString]
            if command.checkPermission(message.author.id):
                result = command.method(params=message.content[commandMatch.end() + 1:], author=message.author)
                if isinstance(result, str):
                    await client.send_message(message.author, result)
            else:
                # Tattle
                await client.send_message(wishUser, "Alert: Invalid access from {}#{} ({}): {}".format(message.author.name, message.author.discriminator, message.author.id, message.content))

            #TODO log tattle


###################
#     Startup     #
###################

@asyncio.coroutine
def shutdown_coro():
    motherprint("SHUTTING DOWN")
    for name in botMap:
        killChild(name)

    yield from client.logout()
    motherprint("SHUT DOWN IS COMPLETE")

@asyncio.coroutine
def checkForStopEvent():
    while True:
        if _stop_event.is_set():
            yield from shutdown_coro()
            break
        try:
            yield from asyncio.sleep(3)
        except asyncio.CancelledError:
            break

def fetchToken(botName):
    dirname = os.path.dirname(__file__)
    secrets = open(os.path.join(dirname, "secrets.txt"), 'r')
    for line in secrets:
        parsed = line.split(":")
        if parsed[0] == botName:
            token = parsed[1].strip()
            secrets.close()
            return token


_stop_event = threading.Event()

loop = asyncio.new_event_loop()
client = discord.Client(loop=loop)
client.event(on_ready)
client.event(on_message)

checkForStopTask = loop.create_task(checkForStopEvent())

try:
    loop.run_until_complete(client.start(fetchToken(__file__)))
except KeyboardInterrupt:
    checkForStopTask.cancel()
    loop.run_until_complete(shutdown_coro())
except Exception as e:
    motherprint("Exception: {}".format(e))
finally:
    loop.close()