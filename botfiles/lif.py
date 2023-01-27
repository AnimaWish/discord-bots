import discord
import asyncio
from .botmodules import DNDBot
import argparse

class LifBot(DNDBot):
    ###################
    #    Constants    #
    ###################

    ###################
    #     Helpers     #
    ###################

    ###################
    #    Commands     #
    ###################

    ###################
    #   Bot Methods   #
    ###################

    def getName(self):
        return "lif"

    def __init__(self, prefix="!", *, intents, **options):
        super().__init__(prefix, "*pours a drink*", "*ouija marker goes limp*", intents=intents, options=options)

