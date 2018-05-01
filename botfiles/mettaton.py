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
    `!choose a,list,of,things` - get a random member of the list
    `!pose` - strike a pose
    `!captain` - choose a team captain from the current voice channel
Hit up Wish#6215 for feature requests/bugs, or visit my repository at https://github.com/AnimaWish/discord-bots
    """
    
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

    def chooseCaptain(self, message, params):
        print(message.author.voice)
        print(message.author.voice.voice_channel)
        print(message.author.voice.voice_channel.voice_members)
        captain = random.choice(message.author.voice.voice_channel.voice_members)
        return random.choice(MettatonBot.CHOICE_STRINGS).format(captain.name)

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
            'captain':      BotCommand(self.chooseCaptain,      lambda x: True)
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
