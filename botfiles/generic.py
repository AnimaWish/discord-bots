import discord
import asyncio
import random
import urllib.request
import re
import os

class BotCommand:
        # permissionFunction expects a User as an argument, and returns a
        def __init__(self, method, permissionFunction):
            self.method = method
            self.permission = permissionFunction

class DiscordBot:
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

    # TODO generate this programmatically
    def getHelp():
        return """
    Hit up Wish#6215 for feature requests/bugs, or visit my repository at https://github.com/AnimaWish/discord-bots
    """

    ###################
    #  Event Methods  #
    ###################

    async def on_ready(self):
        print('Logged in as')
        print(self.client.user.name)
        print(self.client.user.id)
        print('------')

    async def on_message(self, message):
        commandPattern = "^!\S+\s"
        commandMatch = re.match(commandPattern, message.content)
        if commandMatch:
            commandString = message.content[commandMatch.start() + 1 : commandMatch.end()].strip()
            if commandString in self.commandMap:
                command = self.commandMap[commandString]
                if command.permission(message.author):
                    await self.client.send_message(message.channel, command.method(message.content[commandMatch.end():]))

    ###################
    #     Startup     #
    ###################

    def __init__(self, token):
        self.client = discord.Client()
        self.token = token
        # commandMap should be overloaded by implementer
        self.commandMap = {
            'help': generic.BotCommand(self.getHelp, lambda x: True),
        }
        self.client.event(self.on_ready)
        self.client.event(self.on_message)

    def run(self):
        self.client.run(self.token)
