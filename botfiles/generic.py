import discord
import asyncio
import random
import urllib.request
import re
import os, io

class BotCommand:
    # method must accept `message` and `params`, and return a string or None
    # permissionFunction expects a User/Member as an argument, and returns a bool
    def __init__(self, method, permissionFunction):
        self.method = method
        self.permission = permissionFunction

    def execute(self, params, message):
        if self.permission(message.author):
            return self.method(message=message, params=params)
        else:
            raise PermissionError("{}#{}:({})".format(message.author.name, message.author.discriminator, message.author.id))

class DiscordBot:
    ###################
    #     Helpers     #
    ###################

    @staticmethod
    def memberHasRole(member, roleId):
        for role in member.roles:
            if role.id == roleId:
                return True

        return False

    ###################
    #    Commands     #
    ###################

    # TODO generate this programmatically
    def getHelp(self, message, params):
        return """
    Hit up Wish#6215 for feature requests/bugs, or visit my repository at https://github.com/AnimaWish/discord-bots
    """

    def echo(self, message, params):
        return params

    ###################
    #  Event Methods  #
    ###################

    async def on_ready(self):
        #TODO pipe to stdout?
        print('Logged in as')
        print(self.client.user.name)
        print(self.client.user.id)
        print('------')

    async def on_message(self, message):
        commandPattern = "^{}\S+\s*".format(self.prefix)
        commandMatch = re.match(commandPattern, message.content)
        if commandMatch:
            commandString = message.content[commandMatch.start() + len(self.prefix) : commandMatch.end()].strip()
            if commandString in self.commandMap:
                command = self.commandMap[commandString]
                params  = message.content[commandMatch.end():].strip()
                try: 
                    result = command.execute(params, message)
                    if isinstance(result, io.IOBase):
                        await self.client.send_file(message.channel, result)
                    elif result is not None and len(result) > 0:
                        await self.client.send_message(message.channel, result)

                except PermissionError as err:
                    print("Insufficient permissions for user {}".format(err))

    ###################
    #     Startup     #
    ###################

    def __init__(self, token, prefix="!"):
        self.client = discord.Client()
        self.token = token
        self.prefix = prefix

        self.commandMap = {
            'help': BotCommand(self.getHelp, lambda x: True),
            'echo': BotCommand(self.echo,    lambda x: True),
        }
        self.client.event(self.on_ready)
        self.client.event(self.on_message)

    def run(self):
        self.client.run(self.token)
