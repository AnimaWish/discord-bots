import discord
import asyncio
import random
import urllib.request
import re
import os, io
import threading

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

    MAX_DICE = 1000000

    CHOICE_STRINGS = [
        "I choose... {}!",
        "How about {}?",
        "Result hazy, try again later (jk do {})",
        "{}, obviously!",
        "Choose {}.",
        "Whatever you do, DON'T pick {} (wink)",
        "Signs point to {}",
        "*cracks open fortune cookie, finds message that says \"{}\"*",
        "My lawyers advise {}",
        "I'm a {} guy myself."
    ]

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

    def ping(self, message, params):
        return "pong"

    def echo(self, message, params):
        return params

    def getDieRoll(self, message, params):
            params = params.split("d")
            if len(params) != 2 or not (params[0].isdigit() and params[1].isdigit()):
                return "Required syntax: `!roll XdY`"
            elif int(params[0]) > DiscordBot.MAX_DICE:
                return "I can't possibly hold {} dice!".format(params[0])
            else:
                result = 0
                for x in range(0, int(params[0])):
                    result = result + random.randint(1, int(params[1]))

            return "You rolled {}!".format(result)

    def chooseRand(self, message, params):
        theList = re.split('[; |,\s]',params)
        return random.choice(DiscordBot.CHOICE_STRINGS).format(random.choice(theList))

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

    @asyncio.coroutine
    def checkForStopEvent(self):
        while True:
            if self._stop_event.is_set():
                print("Stop signal received")
                yield from self.client.logout()
                break
            try:
                yield from asyncio.sleep(3)
            except asyncio.CancelledError:
                break

    def stop(self):
        self._stop_event.set()

    def __init__(self, token, prefix="!"):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.client = discord.Client(loop=self.loop)

        self.token = token
        self.prefix = prefix

        self.commandMap = {
            'help': BotCommand(self.getHelp, lambda x: True),
            'echo': BotCommand(self.echo,    lambda x: True),
        }
        self.client.event(self.on_ready)
        self.client.event(self.on_message)

        self._stop_event = threading.Event()


    def run(self):      
        print("Hello")

        checkForStopTask = self.loop.create_task(self.checkForStopEvent())
        startTask = self.client.start(self.token)
        wait_tasks = asyncio.wait([startTask])

        try:
            self.loop.run_until_complete(wait_tasks)
        except KeyboardInterrupt:
            checkForStopTask.cancel()
        except Exception as e:
            print("Exception: {}".format(e))
        finally:
            self.loop.run_until_complete(self.client.logout())
            self.loop.close()

        print("Goodbye")
