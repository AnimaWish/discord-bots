import discord
import asyncio
import random
import re
import os
from .simplevote import SimpleVoteBot
import argparse
import importlib

class MettatonBot(SimpleVoteBot):
    ###################
    #    Constants    #
    ###################

    ###################
    #     Helpers     #
    ###################

    ###################
    #    Commands     #
    ###################
    
    async def getPose(self, message, params):
        DIR = "assets/mettaton/poses/"

        poseCount = 0
        for root, dirs, files in os.walk(DIR):
            for file in files:    
                if file.endswith('.png'):
                    poseCount += 1

        choice = random.randint(1, poseCount)
        poseFile = open(os.path.join(DIR, "{}.png".format(choice)), 'rb')
        await message.channel.send(file=discord.File(poseFile))

    ###################
    #   Bot Methods   #
    ###################

    def getName(self):
        return "mettaton"

    def __init__(self, prefix="!"):
        super().__init__(prefix, "OHHH YES!", "GUESS YOU DON'T WANT TO JOIN MY FAN CLUB...?")

        self.addCommand('pose', self.getPose, lambda x: True, "Strike a pose")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Mettaton Bot')
    parser.add_argument("token", type=str, nargs=1)
    args = parser.parse_args()
    mettaton = MettatonBot()
    mettaton.run(args.token[0])
