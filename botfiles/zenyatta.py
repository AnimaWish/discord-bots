import discord
import asyncio
import random
import re
from .botmodules import VoteBot, EventBot
import argparse
import importlib

class ZenyattaBot(EventBot, VoteBot):
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
        return "zenyatta"

    def __init__(self, prefix="!", *, intents, **options):
        super().__init__(prefix, "Peace be upon you.", "Passing into the Iris.", intents=intents, options=options)
