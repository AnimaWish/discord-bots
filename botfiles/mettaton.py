import discord
import asyncio
import random
import os
from .botmodules import VoteBot
import argparse
import importlib

class MettatonBot(VoteBot):
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

    async def getGenre(self, message, params):
        thematicArr = ["Action", "Drama", "Romance", "Documentary", "Horror", "Comedy", "Adventure", "Mystery", "Thriller", "Musical"]
        aestheticArr = ["Sci-Fi","Fantasy","Holiday","School","Historical","Crime","Family","Spy","Sports","Western","War","Slice of Life","Martial Arts","Legal","Kaiju","Apocalypse","Superhero","Urban","Cooking"]
        productionArr = ["Foreign","B-movie","Indie","Hollywood","Silent","Animated","Exploitation","<1960s","1960s","1970s","1980s","1990s","2000s","2010-20s"]

        qualifierArr = random.choice([aestheticArr, productionArr])

        decision = "a **" + random.choice(qualifierArr) + " " + random.choice(thematicArr) + "** film"

        await message.channel.send(random.choice(self.CHOICE_STRINGS).format(decision))

    ###################
    #   Bot Methods   #
    ###################

    def getName(self):
        return "mettaton"

    def __init__(self, prefix="!", *, intents, **options):
        super().__init__(prefix, "OHHH YES!", "GUESS YOU DON'T WANT TO JOIN MY FAN CLUB...?", intents=intents, options=options)

        self.addCommand('pose', self.getPose, lambda x: True, "Strike a pose")
        self.addCommand('genre', self.getGenre, lambda x: True, "Select a film genre from my massive database")
