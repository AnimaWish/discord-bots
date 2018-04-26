import discord
import asyncio
import random
import urllib.request
import re
import os
from generic import DiscordBot, BotCommand
import argparse

class MettatonBot(DiscordBot):
    ###################
    #    Constants    #
    ###################

    MAX_DICE = 1000000

    CHOICE_STRINGS = [
        "I choose... {}!",
        "How about {}?",
        "Result hazy, try again later (jk do {})",
        "{}, obviously!",
        "Choose {}."
        "Whatever you do, DON'T pick {} (wink)",
        "Signs point to {}",
        "*cracks open fortune cookie, finds message that says \"{}\"*"
        "My lawyers advise {}",
        "I'm a {} man myself."
    ]

    ###################
    #     Helpers     #
    ###################

    ###################
    #    Commands     #
    ###################

    def getHelp(self, message, params):
        return """
Available Commands:
    `!roll XdY` - roll X Y-sided dice
    `!choose a,list,of,shit` - get a random member of the list
    `!pose` - strike a pose
Hit up Wish#6215 for feature requests/bugs, or visit my repository at https://github.com/AnimaWish/discord-bots
    """

    #TODO move this to generic
    def getDieRoll(self, message, params):
            params = params.split("d")
            if len(params) != 2 or not (params[0].isdigit() and params[1].isdigit()):
                return "Required syntax: `!roll XdY`"
            elif int(params[0]) > MettatonBot.MAX_DICE:
                return "I can't possibly hold {} dice!".format(params[0])
            else:
                result = 0
                for x in range(0, int(params[0])):
                    result = result + random.randint(1, int(params[1]))

            return "You rolled {}!".format(result)

    #TODO move this to generic
    def chooseRand(self, message, params):
        theList = re.split('[; |,\s]',params)
        return random.choice(MettatonBot.CHOICE_STRINGS).format(random.choice(theList))
    
    def getPose(self, message, params):
        DIR = "assets/mettaton/poses/"# TODO Will this work with mother?

        poseCount = 0
        for root, dirs, files in os.walk(DIR):
            for file in files:    
                if file.endswith('.png'):
                    poseCount += 1

        choice = random.randint(1, poseCount)
        poseFile = open(os.path.join(DIR, "{}.png".format(choice)), 'rb')
        return poseFile

    ###################
    #   Bot Methods   #
    ###################

    def __init__(self, token, prefix="!"):
        super().__init__(token, prefix)
        self.commandMap = {
            'help':         BotCommand(self.getHelp,            lambda x: True),
            'echo':         BotCommand(self.echo,               lambda x: True),
            'roll':         BotCommand(self.getDieRoll,         lambda x: True),
            'choose':       BotCommand(self.chooseRand,         lambda x: True),
            'pose':         BotCommand(self.getPose,            lambda x: True),
        }

    async def on_ready(self):
        await super().on_ready()

    async def on_message(self, message):
        await super().on_message(message)

if __name__ == "__main__":
    print("OHH YEAH")
    parser = argparse.ArgumentParser(description='Mettaton Bot')
    parser.add_argument("token", type=str, nargs=1)
    args = parser.parse_args()
    mettaton = MettatonBot(args.token[0])
    mettaton.run()
