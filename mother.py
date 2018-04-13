import discord
import asyncio
import random
import urllib.request
import re
import os, sys
import importlib
import threading

client = discord.Client()

class BotObject:
    def __init__(self, botName, token):
        self.token = token
        self.name = botName
        sys.path.append("botfiles")
        package = importlib.__import__('botfiles', fromlist=[botName])
        self.module = getattr(package, botName)
        self.reloadModule()

    def reloadModule(self):
        importlib.reload(self.module)
        botClass = getattr(self.module, self.name.capitalize() + "Bot")
        self.bot = botClass(self.token)

###################
#    Constants    #
###################

botMap = {
    #'philippe': None,
    'zenyatta': None
}

threads = {
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
        if threads[botName] is not None:
            botObj.stop()
            threads[botName].join()

        botObj.reloadModule()
        threads[botName] = threading.Thread(target=botObj.bot.run, name="{}-thread".format(botName))
        threads[botName].start()

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
    if not botName in botMap:
        return botName + " not found." 

    restartChild(botName)

    print("Restarted {}".format(botName))

    #TODO hash file to make sure something actually changed
    #TODO https://stackoverflow.com/questions/684171/how-to-re-import-an-updated-package-while-in-python-interpreter

# Update local files
def update(params, author):
    bashCommand = "git pull"
    process = subprocess.Popen(bashCommand.split(), cwd=os.path.dirname(os.path.abspath(__file__)))
    output, error = process.communicate()

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
    #TODO gracefully shutdown children
    #TODO gracefully shutdown event loop - why is this so hard
    sys.exit(0)

commandMap = {
    'help':     BotCommand(getHelp,     lambda x: True),
    'whoami':   BotCommand(whoAmI,      lambda x: True),
    'status':   BotCommand(getStatus,   lambda x: True),

    'echo':     BotCommand(echo,        isValidUser),
    'restart':  BotCommand(restart,     isValidUser),
    'update':   BotCommand(update,      isValidUser),

    'block':    BotCommand(block,       isAdmin),
    'shutdown': BotCommand(shutdown,    isAdmin)
}

###################
#  Event Methods  #
###################

@client.event
async def on_ready():
    #Report startup
    print('Logged in as')
    print(client.user.name)
    print(client.user.id)
    
    #Find Wish
    try:
        global wishUser
        wishUser = await client.get_user_info(WISH_USER_ID)
        print("Found administrator: {}#{}".format(wishUser.name, wishUser.discriminator))
    except Exception as e:
        print(e)
        print("NO ADMINISTRATOR FOUND")

    #Initialize Blacklist
    importBlacklist()
    print("Imported blacklist with {} members.".format(len(blacklist)))

    #Start Children
    for botName in botMap.keys():
        botMap[botName] = BotObject(botName, fetchToken(botName + ".py"))
        restartChild(botName)

    print('------')

@client.event
async def on_message(message):
    if message.author.id in blacklist:
        print("Blocked message `{}` from {}#{}({})".format(message.content, message.author.name, message.author.discriminator, message.author.id))
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

def fetchToken(botName):
    dirname = os.path.dirname(__file__)
    secrets = open(os.path.join(dirname, "secrets.txt"), 'r')
    for line in secrets:
        parsed = line.split(":")
        if parsed[0] == botName:
            token = parsed[1].strip()
            secrets.close()
            return token

client.run(fetchToken(__file__))
